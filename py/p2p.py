import hashlib, json, select, socket, struct, time, threading, traceback, uuid
from collections import namedtuple, deque

version = "0.1.C"

user_salt    = str(uuid.uuid4())
sep_sequence = "\x1c\x1d\x1e\x1f"
compression = ['gzip', 'bz2']  # This should be in order of preference. IE: gzip is best, then none
max_outgoing = 8

try:
    import lzma
    compression.append('lzma')
except:
    pass

# Utility method/class section; feel free to mostly ignore

class protocol(namedtuple("protocol", ['sep', 'subnet', 'encryption'])):
    def id(self):
        h = hashlib.sha256(''.join([str(x) for x in self] + [version]).encode())
        return to_base_58(int(h.hexdigest(), 16))

default_protocol = protocol(sep_sequence, '', "PKCS1_v1.5")


class message(namedtuple("message", ['msg', 'sender', 'protocol', 'time', 'server'])):
    def reply(self, *args):
        """Replies to the sender if you're directly connected. Tries to make a connection otherwise"""
        if isinstance(self.sender, p2p_connection):
            self.sender.send('whisper', 'whisper', *args)
        elif self.server.routing_table.get(self.sender):
            self.server.routing_table.get(self.sender).send('whisper', 'whisper', *args)
        else:
            request_hash = hashlib.sha384((self.sender + to_base_58(getUTC())).encode()).hexdigest()
            request_id = to_base_58(int(request_hash, 16))
            self.server.send(request_id, self.sender, type='request')
            self.server.requests.update({request_id: ['whisper', 'whisper'] + list(args)})
            print("You aren't connected to the original sender. This reply is not guarunteed, but we're trying to make a connection and put the message through.")

    def parse(self):
        """Return the message's component packets, including it's type in position 0"""
        return self.msg.split(self.protocol.sep)

    def __repr__(self):
        string = "message(type=" + repr(self.parse()[0]) + ", packets=" + repr(self.parse()[1:]) + ", sender="
        if isinstance(self.sender, p2p_connection):
            return string + repr(self.sender.addr) + ")"
        else:
            return string + self.sender + ")"

    def id(self):
        """Returns the SHA384-based ID of the message"""
        msg_hash = hashlib.sha384((self.msg + to_base_58(self.time)).encode())
        return to_base_58(int(msg_hash.hexdigest(), 16))

base_58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


def to_base_58(i):
    """Takes an integer and returns its corresponding base_58 string"""
    string = ""
    while i:
        string = base_58[i % 58] + string
        i = i // 58
    return string


def from_base_58(string):
    """Takes a base_58 string and returns its corresponding integer"""
    decimal = 0
    if isinstance(string, bytes):
        string = string.decode()
    for char in string:
        decimal = decimal * 58 + base_58.index(char)
    return decimal


def getUTC():
    """Returns the current unix time in UTC"""
    import calendar, time
    return calendar.timegm(time.gmtime())


def compress(msg, method):
    """Shortcut method for compression"""
    if method == 'gzip':
        import zlib
        return zlib.compress(msg)
    elif method =='bz2':
        import bz2
        return bz2.compress(msg)
    elif method =='lzma':
        import lzma
        return lzma.compress(msg)
    else:
        raise Exception('Unknown compression method')


def decompress(msg, method):
    """Shortcut method for decompression"""
    if method == 'gzip':
        import zlib
        return zlib.decompress(msg, zlib.MAX_WBITS | 32)
    elif method == 'bz2':
        import bz2
        return bz2.decompress(msg)
    elif method =='lzma':
        import lzma
        return lzma.decompress(msg)
    else:
        raise Exception('Unknown decompression method')


def construct_message(prot, comp_types, msg_type, id, packets, time=None):
    time = kargs.get('time')
    if not kargs.get('time'):
        time = to_base_58(getUTC())

    msg_hash = hashlib.sha384((prot.sep.join(list(packets)) + time).encode()).hexdigest()
    msg_id = to_base_58(int(msg_hash, 16))

    packets = [msg_type, id, msg_id, time] + list(packets)
    msg = prot.sep.join(packets).encode()
    compression_used = ""
    for method in compression:
        if method in comp_types:
            compression_used = method
            msg = compress(msg, method)
            break

    size = struct.pack("!L", len(msg))
    return size, msg

# End utility section


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
        self.last_sent = []
        self.expected = 4
        self.active = False

    def collect_incoming_data(self, data):
        """Collects incoming data"""
        if not bool(data):
            if self.debug(5): print(data, time.time())
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except:
                pass
            return False
        self.buffer.append(data)
        self.time = getUTC()
        return True

    def find_terminator(self):
        """Returns whether the definied return sequences is found"""
        return len(''.encode().join(self.buffer)) == self.expected

    def found_terminator(self):
        """Processes received messages"""
        if not self.active:
            if self.debug(4): print(self.buffer, self.expected, self.find_terminator())
            self.expected = struct.unpack("!L", ''.encode().join(self.buffer))[0]
            self.buffer = []
            self.active = True
        else:
            raw_msg = ''.encode().join(self.buffer)
            self.expected = 4
            self.buffer = []
            compression_fail = False
            self.active = False
            for method in self.compression:
                if method in compression:
                    try:
                        raw_msg = decompress(raw_msg, method)
                        compression_fail = False
                    except:
                        compression_fail = True
                        continue
                    break
            try:
                if isinstance(raw_msg, bytes):
                    raw_msg = raw_msg.decode()
            except:
                pass
            packets = raw_msg.split(self.protocol.sep)
            if self.debug(1): print("Message received: %s" % packets)
            if packets[0] == 'waterfall':
                if (packets[2] in (i for i, t in self.server.waterfalls)):
                    if self.debug(2): print("Waterfall already captured")
                    return
                else:
                    if self.debug(2): print("New waterfall received. Proceeding as normal")
            elif packets[0] == 'renegotiate':
                if packets[4] == 'compression':
                    respond = (self.compression != json.loads(packets[5]))
                    self.compression = json.loads(packets[5])
                    if self.debug(2): print("Compression methods changed to: %s" % repr(self.compression))
                    if respond:
                        self.send('renegotiate', 'compression', json.dumps([method for method in compression if method in self.compression]))
                    return
                elif packets[4] == 'resend':
                    self.send(*self.last_sent)
                    return
            if compression_fail:
                self.send('renegotiate', 'compression', json.dumps([algo for algo in self.compression if algo is not method]))
                self.send('renegotiate', 'resend')
                return
            msg = self.protocol.sep.join(packets[4:])  # Handle request without routing headers
            if packets[0] == 'waterfall':
                reply_object = packets[1]
            else:
                reply_object = self
            self.server.handle_request(message(msg, reply_object, self.protocol, from_base_58(packets[3]), self.server))

    def send(self, msg_type, *args, **kargs):
        """Sends a message through its connection. The first argument is message type. All after that are content packets"""
        # This section handles waterfall-specific flags
        id = kargs.get('id')
        time = kargs.get('time')
        if not kargs.get('time'):
            time = to_base_58(getUTC())
        if not id:
            id = self.server.id
        # Begin real method
        msg_hash = hashlib.sha384((self.protocol.sep.join(list(args)) + time).encode()).hexdigest()
        msg_id = to_base_58(int(msg_hash, 16))
        if (msg_id, time) not in self.server.waterfalls:
            self.server.waterfalls.appendleft((msg_id, from_base_58(time)))
        packets = [msg_type, id, msg_id, time] + list(args)
        if msg_type in ['whisper', 'broadcast']:
            self.last_sent = [msg_type] + list(args)
        msg = self.protocol.sep.join(packets).encode()
        compression_used = ""
        for method in compression:
            if method in self.compression:
                compression_used = method
                msg = compress(msg, method)
                break
        size = struct.pack("!L", len(msg))
        if self.debug(4): print("Sending %s to %s" % ([size] + packets, self))
        if self.debug(4) and compression_used: print("Compressing with %s" % compression_used)
        try:
            self.sock.send(size)
            self.sock.send(msg)
        except IOError as e:
            self.server.daemon.exceptions.append((e, traceback.format_exc()))
            self.server.daemon.disconnect(self)

    def fileno(self):
        return self.sock.fileno()

    def debug(self, level=1):
        """Detects how verbose you want the printing to be"""
        return self.server.debug(level)


class p2p_daemon(object):
    def __init__(self, addr, port, server, prot=default_protocol):
        self.protocol = prot
        self.server = server
        if self.protocol.encryption == "Plaintext":
            self.sock = socket.socket()
        elif self.protocol.encryption == "PKCS1_v1.5":
            import net
            self.sock = net.secure_socket()
        else:
            raise Exception("Unknown encryption type")
        self.sock.bind((addr, port))
        self.sock.listen(5)
        self.sock.settimeout(0.1)
        self.exceptions = []
        self.daemon = threading.Thread(target=self.mainloop)
        self.daemon.daemon = True
        self.daemon.start()

    def handle_accept(self):
        """Handle an incoming connection"""
        try:
            conn, addr = self.sock.accept()
            if conn is not None:
                if self.debug(1): print('Incoming connection from %s' % repr(addr))
                handler = p2p_connection(conn, self.server, self.protocol)
                handler.send("whisper", "handshake", self.server.id, self.protocol.id(), json.dumps(self.server.out_addr), json.dumps(compression))
                handler.sock.settimeout(0.01)
                self.server.awaiting_ids.append(handler)
                # print("Appended ", handler.addr, " to handler list: ", handler)
        except socket.timeout:
            pass

    def mainloop(self):
        """Daemon thread which handles all incoming data and connections"""
        while True:
            # for handler in list(self.server.routing_table.values()) + self.server.awaiting_ids:
            if list(self.server.routing_table.values()) + self.server.awaiting_ids:
                for handler in select.select(list(self.server.routing_table.values()) + self.server.awaiting_ids, [], [], 0.01)[0]:
                    # print("Collecting data from %s" % repr(handler))
                    try:
                        while not handler.find_terminator():
                            if not handler.collect_incoming_data(handler.sock.recv(1)):
                                if self.debug(6): print("disconnecting node %s while in loop" % handler.id)
                                self.disconnect(handler)
                                raise socket.timeout()
                        handler.found_terminator()
                    except socket.timeout:
                        continue  # Shouldn't happen with select, but if it does...
                    except Exception as e:
                        if isinstance(e, socket.error) and e.args[0] in [9, 104, 10054, 10058]:
                            node_id = handler.id
                            if not node_id:
                                node_id = repr(handler)
                            if self.debug(1): print("Node %s has disconnected from the network" % node_id)
                        else:
                            if self.debug(0): print("There was an unhandled exception with peer id %s. This peer is being disconnected, and the relevant exception is added to the debug queue. If you'd like to report this, please post a copy of your p2p_socket.daemon.exceptions list to github.com/gappleto97/python-utils." % handler.id)
                            self.exceptions.append((e, traceback.format_exc()))
                        try:
                            handler.sock.shutdown(socket.SHUT_RDWR)
                        except:
                            pass
                        self.disconnect(handler)
            self.handle_accept()

    def disconnect(self, handler):
        """Disconnects a node"""
        node_id = handler.id
        if not node_id:
            node_id = repr(handler)
        if self.debug(1): print("Connection to node %s has been closed" % node_id)
        if handler in self.server.awaiting_ids:
            self.server.awaiting_ids.remove(handler)
        elif self.server.routing_table.get(handler.id):
            self.server.routing_table.pop(handler.id)
        if handler.id and handler.id in self.server.outgoing:
            self.server.outgoing.remove(handler.id)
        elif handler.id and handler.id in self.server.incoming:
            self.server.incoming.remove(handler.id)

    def debug(self, level=1):
        """Detects how verbose you want the printing to be"""
        return self.server.debug(level)


class p2p_socket(object):
    def __init__(self, addr, port, prot=default_protocol, out_addr=None, debug_level=0):
        self.protocol = prot
        self.debug_level = debug_level
        self.routing_table = {}     # In format {ID: handler}
        self.awaiting_ids = []      # Connected, but not handshook yet
        self.outgoing = []          # IDs of outgoing connections
        self.incoming = []          # IDs of incoming connections
        self.requests = {}          # Metadata about message replies where you aren't connected to the sender
        self.waterfalls = deque()   # Metadata of messages to waterfall
        self.queue = deque()        # Queue of received messages. Access through recv()
        if out_addr:                # Outward facing address, if you're port forwarding
            self.out_addr = out_addr
        else:
            self.out_addr = addr, port
        info = [str(out_addr), prot.id(), user_salt]
        h = hashlib.sha384(''.join(info).encode())
        self.id = to_base_58(int(h.hexdigest(), 16))
        self.daemon = p2p_daemon(addr, port, self, prot)

    def handle_request(self, msg):
        """Decides how to handle various message types, allowing some to be handled automatically"""
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
            handler.send("whisper", "peers", json.dumps([(self.routing_table[key].addr, key) for key in self.routing_table.keys()]))
        elif packets[0] == 'peers':
            new_peers = json.loads(packets[1])
            for addr, id in new_peers:
                if len(self.outgoing) < max_outgoing and addr:
                    self.connect(addr[0], addr[1], id)
        elif packets[0] == 'response':
            if self.debug(1): print("Response received for request id %s" % packets[1])
            if self.requests.get(packets[1]):
                addr = json.loads(packets[2])
                if addr:
                    msg = self.requests.get(packets[1])
                    self.requests.pop(packets[1])
                    self.connect(addr[0][0], addr[0][1], addr[1])
                    self.routing_table[addr[1]].send(*msg)
        elif packets[0] == 'request':
            if self.routing_table.get(packets[2]):
                handler.send('broadcast', 'response', packets[1], json.dumps([self.routing_table.get(packets[2]).addr, packets[2]]))
            elif packets[2] == '*':
                self.send("broadcast", "peers", json.dumps([(key, self.routing_table[key].addr) for key in self.routing_table.keys()]))
        elif packets[0] == 'whisper':
            self.queue.appendleft(msg)
        else:
            if self.waterfall(msg):
                self.queue.appendleft(msg)

    def send(self, *args, **kargs):
        """Sends data to all peers. type flag will override normal subflag. Defaults to 'broadcast'"""
        # self.cleanup()
        if kargs.get('type'):
            send_type = kargs.pop('type')
        else:
            send_type = 'broadcast'
        # map(methodcaller('send', 'broadcast', 'broadcast', *args), self.routing_table.values())
        for handler in self.routing_table.values():
            handler.send('broadcast', send_type, *args)

    def waterfall(self, msg):
        """Handles the waterfalling of received messages"""
        # self.cleanup()
        if self.debug(3): print(msg.id(), [i for i, t in self.waterfalls])
        if msg.id() not in (i for i, t in self.waterfalls):
            self.waterfalls.appendleft((msg.id(), msg.time))
            if isinstance(msg.sender, p2p_connection):
                id = msg.sender.id
            else:
                id = msg.sender
            for handler in self.routing_table.values():
                handler.send('waterfall', *msg.parse(), time=to_base_58(msg.time), id=id)
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
        if self.debug(3): print("Not rebroadcasting")
        return False

    def recv(self, quantity=1):
        """Receive 1 or several message objects. Returns none if none are present. Non-blocking."""
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
        """Connects to a specified node. Specifying ID will immediately add to routing table. Blocking"""
        # self.cleanup()
        if self.debug(1): print("Attempting connection to %s:%s" % (addr, port))
        if socket.getaddrinfo(addr, port)[0] == socket.getaddrinfo(*self.out_addr)[0] or \
                                                    id and id in self.routing_table.keys():
            if self.debug(1): print("Connection already established")
            return False
        if self.protocol.encryption == "Plaintext":
            conn = socket.socket()
        elif self.protocol.encryption == "PKCS1_v1.5":
            import net
            conn = net.secure_socket()
        conn.settimeout(0.01)
        conn.connect((addr, port))
        handler = p2p_connection(conn, self, self.protocol, outgoing=True)
        handler.id = id
        handler.send("whisper", "handshake", self.id, self.protocol.id(), json.dumps(self.out_addr), json.dumps(compression))
        if not id:
            self.awaiting_ids.append(handler)
        else:
            self.routing_table.update({id: handler})
        # print("Appended ", port, addr, " to handler list: ", handler)

    def debug(self, level=1):
        """Detects how verbose you want the printing to be"""
        return self.debug_level >= level
