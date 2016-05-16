# TODO: Allow for peer cleanup
# TODO: Fix incorrect sender on message construction, when routed around obstruction

import hashlib, json, multiprocessing.pool, socket, threading, traceback, uuid
from collections import namedtuple, deque

version = "0.1.4"

user_salt    = str(uuid.uuid4())
sep_sequence = "\x1c\x1d\x1e\x1f"
end_sequence = sep_sequence[::-1]
compression = ['gzip']  # This should be in order of preference. IE: gzip is best, then none
max_outgoing = 8

base_protocol = namedtuple("protocol", ['end', 'sep', 'subnet', 'encryption'])
base_message = namedtuple("message", ['msg', 'sender', 'protocol', 'time'])


class protocol(base_protocol):
    def id(self):
        h = hashlib.sha256(''.join([str(x) for x in self] + [version]).encode())
        return to_base_58(int(h.hexdigest(), 16))

default_protocol = protocol(end_sequence, sep_sequence, None, "PKCS1_v1.5")


class message(base_message):
    def reply(self, *args):
        if self.sender:
            self.sender.send('whisper', 'whisper', *args)
        else:
            return False

    def parse(self):
        return self.msg.split(self.protocol.sep)

    def __repr__(self):
        return "message(type=" + repr(self.parse()[0]) + ", packets=" + repr(self.parse()[1:]) + ", sender=" + repr(self.sender.addr) + ")"

    def id(self):
        msg_hash = hashlib.sha384((self.msg + to_base_58(self.time)).encode())
        return to_base_58(int(msg_hash.hexdigest(), 16))


def to_base_58(i):
    string = ""
    while i:
        string = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'[i % 58] + string
        i = i // 58
    return string


def from_base_58(string):
    decimal = 0
    if isinstance(string, bytes):
        string = string.decode()
    for char in string:
        decimal = decimal * 58 + '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'.index(char)
    return decimal


def getUTC():
    from calendar import timegm
    from time import gmtime
    return timegm(gmtime())


class p2p_connection(object):
    def __init__(self, sock, server, prot=default_protocol, outgoing=False):
        self.sock = sock
        self.server = server
        self.protocol = prot
        self.outgoing = outgoing
        self.buffer = []
        self.id = None
        self.time = getUTC()
        self.addr = None
        self.compression = []

    def collect_incoming_data(self, data):
        if data == '':
            self.sock.close()
            return ''
        self.buffer.append(data)
        self.time = getUTC()

    def find_terminator(self):
        return self.protocol.end.encode() in ''.encode().join(self.buffer)

    def found_terminator(self):
        raw_msg = ''.encode().join(self.buffer)
        raw_msg = raw_msg.replace(self.protocol.end.encode(), ''.encode())
        self.buffer = []
        for method in self.compression:
            if method in compression:
                raw_msg = self.decompress(raw_msg, method)
                break
        if isinstance(raw_msg, bytes):
            raw_msg = raw_msg.decode()
        packets = raw_msg.split(self.protocol.sep)
        # print("Message received: %s" % packets)
        if packets[0] == 'waterfall':
            if (packets[2] in (i for i, t in self.server.waterfalls)):
                # print("Waterfall already captured")
                return
            else:
                pass  # print("New waterfall received. Proceeding as normal")
        msg = self.protocol.sep.join(packets[4:])  # Handle request without routing headers
        self.server.handle_request(message(msg, self, self.protocol, from_base_58(packets[3])))

    def send(self, msg_type, *args):
        time = to_base_58(getUTC())
        msg_hash = hashlib.sha384((self.protocol.sep.join(list(args)) + time).encode()).hexdigest()
        msg_id = to_base_58(int(msg_hash, 16))
        if (msg_id, time) not in self.server.waterfalls:
            self.server.waterfalls.appendleft((msg_id, from_base_58(time)))
        packets = [msg_type, self.server.id, msg_id, time] + list(args)
        # print("Sending %s to %s" % (args, self))
        msg = self.protocol.sep.join(packets).encode()
        for method in compression:
            if method in self.compression:
                msg = self.compress(msg, method)
                break
        try:
            self.sock.send(msg + self.protocol.end.encode())
        except IOError as e:
            self.server.daemon.debug.append((e, traceback.format_exc()))
            self.server.daemon.disconnect(self)

    def compress(self, msg, method):
        if method == 'gzip':
            import zlib
            return zlib.compress(msg)
        else:
            raise Exception('Unknown compression method')

    def decompress(self, msg, method):
        if method == 'gzip':
            import zlib
            return zlib.decompress(msg)
        else:
            raise Exception('Unknown decompression method')


class p2p_daemon(object):
    def __init__(self, addr, port, server, prot=default_protocol):
        self.protocol = prot
        self.server = server
        if self.protocol.encryption == "Plaintext":
            self.sock = socket.socket()
        elif self.protocol.encryption == "PKCS1_v1.5":
            import net
            self.sock = net.secureSocket()
        else:
            raise Exception("Unknown encryption type")
        self.sock.bind((addr, port))
        self.sock.listen(5)
        self.sock.settimeout(0.1)
        self.debug = []
        self.daemon = threading.Thread(target=self.mainloop)
        self.daemon.daemon = True
        self.daemon.start()

    def handle_accept(self):
        try:
            conn, addr = self.sock.accept()
            if conn is not None:
                print('Incoming connection from %s' % repr(addr))
                handler = p2p_connection(conn, self.server, self.protocol)
                handler.send("whisper", "peers", json.dumps([(key, self.server.routing_table[key].addr) for key in self.server.routing_table.keys()]))
                handler.send("whisper", "handshake", self.server.id, self.protocol.id(), json.dumps(self.server.out_addr), json.dumps(compression))
                handler.sock.settimeout(0.01)
                self.server.awaiting_ids.append(handler)
                # print("Appended ", handler.addr, " to handler list: ", handler)
        except socket.timeout:
            pass

    def mainloop(self):
        while True:
            for handler in list(self.server.routing_table.values()) + self.server.awaiting_ids:
                # print("Collecting data from %s" % repr(handler))
                try:
                    while not handler.find_terminator():
                        if handler.collect_incoming_data(handler.sock.recv(1)) == '':
                            self.disconnect(handler)
                    handler.found_terminator()
                except socket.timeout:
                    continue #socket.timeout
                except socket.error as e:
                    if e.args[0] in [9, 104]:
                        node_id = handler.id
                        if not node_id:
                            node_id = repr(handler)
                        print("Node %s has disconnected from the network" % node_id)
                    else:
                        print("There was an unhandled exception with peer id %s. This peer is being disconnected, and the relevant exception is added to the debug queue. If you'd like to report this, please post a copy of your p2p_socket.daemon.debug list to github.com/gappleto97/python-utils." % handler.id)
                        self.debug.append((e, traceback.format_exc()))
                        handler.sock.close()
                        self.disconnect(handler)
            self.handle_accept()

    def disconnect(self, handler):
        node_id = handler.id
        if not node_id:
            node_id = repr(handler)
        print("Connection to node %s has been closed" % node_id)
        if handler in self.server.awaiting_ids:
            self.server.awaiting_ids.remove(handler)
        elif self.server.routing_table.get(handler.id):
            self.server.routing_table.pop(handler.id)
        if handler.id and handler.id in self.server.outgoing:
            self.server.outgoing.remove(handler.id)
        elif handler.id and handler.id in self.server.incoming:
            self.server.incoming.remove(handler.id)


class p2p_socket(object):
    def __init__(self, addr, port, prot=default_protocol, out_addr=None):
        self.protocol = prot
        self.routing_table = {}  # In format {ID: handler}
        self.awaiting_ids = []
        self.outgoing = []
        self.incoming = []
        self.queue = deque()
        self.waterfalls = deque()
        if out_addr:
            self.out_addr = out_addr
        else:
            self.out_addr = addr, port
        info = [str(out_addr), prot.id(), user_salt]
        h = hashlib.sha384(''.join(info).encode())
        self.id = to_base_58(int(h.hexdigest(), 16))
        self.daemon = p2p_daemon(addr, port, self, prot)

    def handle_request(self, msg):
        handler = msg.sender
        packets = msg.parse()
        if packets[0] == 'handshake':
            if packets[2] != self.protocol.id():
                handler.sock.close()
                self.awaiting_ids.remove(handler)
                return
            handler.id = packets[1]
            if handler.outgoing:
                self.outgoing.append(handler.id)
            else:
                self.incoming.append(handler.id)
            handler.addr = json.loads(packets[3])
            handler.compression = json.loads(packets[4])
            if handler in self.awaiting_ids:
                self.awaiting_ids.remove(handler)
            self.routing_table.update({packets[1]: handler})
        elif packets[0] == 'peers':
            new_peers = json.loads(packets[1])
            for id, addr in new_peers:
                if len(self.outgoing) < max_outgoing and addr:
                    self.connect(addr[0], addr[1], id)
        elif packets[0] == 'whisper':
            self.queue.appendleft(msg)
        else:
            if self.waterfall(msg):
                self.queue.appendleft(msg)

    def send(self, *args):
        # self.cleanup()
        # map(methodcaller('send', 'broadcast', 'broadcast', *args), self.routing_table.values())
        for handler in self.routing_table.values():
            handler.send('broadcast', 'broadcast', *args)

    def waterfall(self, msg):
        # self.cleanup()
        # print msg.id(), [i for i, t in self.waterfalls]
        if msg.id() not in (i for i, t in self.waterfalls):
            self.waterfalls.appendleft((msg.id(), msg.time))
            for handler in self.routing_table.values():
                handler.send('waterfall', *msg.parse())
            self.waterfalls = deque(set(self.waterfalls))
            removes = []
            for i, t in self.waterfalls:
                if t - getUTC() > 60:
                    removes.append((i, t))
            for x in removes:
                self.waterfalls.remove(x)
            while len(self.waterfalls) > 100:
                self.waterfalls.pop()
            return True
        # print("Not rebroadcasting")
        return False

    def recv(self, quantity=1):
        if quantity != 1:
            ret_list = []
            while len(self.queue) and quantity > 0:
                ret_list.append(self.queue.pop())
                quantity -= 1
            return ret_list
        elif len(self.queue):
            return self.queue.pop()
        else:
            return None

    def connect(self, addr, port, id=None):
        # self.cleanup()
        try:
            print("Attempting connection to %s:%s" % (addr, port))
            if socket.getaddrinfo(addr, port)[0] == socket.getaddrinfo(*self.out_addr)[0] or \
                                                        id and id in self.routing_table.keys():
                print("Connection already established")
                return False
            if self.protocol.encryption == "Plaintext":
                conn = socket.socket()
            elif self.protocol.encryption == "PKCS1_v1.5":
                import net
                conn = net.secureSocket()
            conn.connect((addr, port))
            conn.settimeout(0.1)
            handler = p2p_connection(conn, self, self.protocol, outgoing=True)
            handler.id = id
            handler.send("whisper", "peers", json.dumps([(key, self.routing_table[key].addr) for key in self.routing_table.keys()]))
            handler.send("whisper", "handshake", self.id, self.protocol.id(), json.dumps(self.out_addr), json.dumps(compression))
            if not id:
                self.awaiting_ids.append(handler)
            else:
                self.routing_table.update({id: handler})
            # print("Appended ", port, addr, " to handler list: ", handler)
        except Exception as e:
            print("Connection unsuccessful")
            raise e
