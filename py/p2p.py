from __future__ import print_function
import hashlib, json, select, socket, struct, time, threading, traceback, uuid
from collections import namedtuple, deque

version = "0.1.E"

class flags():
    broadcast   = 'broadcast'.encode()
    waterfall   = 'waterfall'.encode()
    whisper     = 'whisper'.encode()
    renegotiate = 'renegotiate'.encode()

    handshake   = 'handshake'.encode()
    request     = 'request'.encode()
    response    = 'response'.encode()
    resend      = 'resend'.encode()
    peers       = 'peers'.encode()
    compression = 'compression'.encode()

    gzip = 'gzip'.encode()
    bz2  = 'bz2'.encode()
    lzma = 'lzma'.encode()

user_salt    = str(uuid.uuid4())
sep_sequence = "\x1c\x1d\x1e\x1f"
compression = [flags.gzip, flags.bz2]  # This should be in order of preference. IE: gzip is best, then bz2, then none
max_outgoing = 8

try:
    import lzma
    compression.append(flags.lzma)
except:
    pass

# Utility method/class section; feel free to mostly ignore

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
    if method == flags.gzip:
        import zlib
        return zlib.compress(msg)
    elif method == flags.bz2:
        import bz2
        return bz2.compress(msg)
    elif method == flags.lzma:
        import lzma
        return lzma.compress(msg)
    else:
        raise Exception('Unknown compression method')


def decompress(msg, method):
    """Shortcut method for decompression"""
    if method == flags.gzip:
        import zlib
        return zlib.decompress(msg, zlib.MAX_WBITS | 32)
    elif method == flags.bz2:
        import bz2
        return bz2.decompress(msg)
    elif method == flags.lzma:
        import lzma
        return lzma.decompress(msg)
    else:
        raise Exception('Unknown decompression method')


def intersect(*args):
    """Returns the ordered intersection of all given iterables, where the order is defined by the first iterable"""
    intersection = args[0]
    for l in args[1:]:
        intersection = [item for item in intersection if item in l]
    return intersection


class protocol(namedtuple("protocol", ['sep', 'subnet', 'encryption'])):
    @property
    def id(self):
        h = hashlib.sha256(''.join([str(x) for x in self] + [version]).encode())
        return to_base_58(int(h.hexdigest(), 16))

default_protocol = protocol(sep_sequence, '', "PKCS1_v1.5")


class message(namedtuple("message", ['msg', 'sender', 'protocol', 'time', 'server'])):
    def reply(self, *args):
        """Replies to the sender if you're directly connected. Tries to make a connection otherwise"""
        if isinstance(self.sender, p2p_connection):
            self.sender.send(flags.whisper, flags.whisper, *args)
        elif self.server.routing_table.get(self.sender):
            self.server.routing_table.get(self.sender).send(flags.whisper, flags.whisper, *args)
        else:
            request_hash = hashlib.sha384((self.sender + to_base_58(getUTC())).encode()).hexdigest()
            request_id = to_base_58(int(request_hash, 16))
            self.server.send(request_id, self.sender, type=flags.request)
            self.server.requests.update({request_id: [flags.whisper, flags.whisper] + list(args)})
            print("You aren't connected to the original sender. This reply is not guarunteed, but we're trying to make a connection and put the message through.")

    def __repr__(self):
        string = "message(type=" + repr(self.packets[0]) + ", packets=" + repr(self.packets[1:]) + ", sender="
        if isinstance(self.sender, p2p_connection):
            return string + repr(self.sender.addr) + ")"
        else:
            return string + self.sender + ")"

    @property
    def packets(self):
        """Return the message's component packets, including it's type in position 0"""
        if isinstance(self.msg, str):
            return self.msg.split(self.protocol.sep)
        else:
            return self.msg.split(self.protocol.sep.encode())

    @property
    def id(self):
        """Returns the SHA384-based ID of the message"""
        if isinstance(self.msg, str):
            msg_hash = hashlib.sha384((self.msg + to_base_58(self.time)).encode())
        else:
            msg_hash = hashlib.sha384(self.msg + to_base_58(self.time).encode())            
        return to_base_58(int(msg_hash.hexdigest(), 16))


class pathfinding_message(object):
    @classmethod
    def feed_string(cls, protocol, string, sizeless=False, compressions=None):
        """Constructs a pathfinding_message from a string."""
        if not sizeless:
            if struct.unpack('!L', string[:4])[0] != len(string[4:]):
                raise ValueError("Must assert struct.unpack('!L', string[:4])[0] == len(string[4:]).")
            string = string[4:]
        compression_fail = False
        if compressions:
            for method in intersect(compressions, compression):  # second is module scope compression
                try:
                    string = decompress(string, method)
                    compression_fail = False
                    break
                except:
                    compression_fail = True
                    continue
        packets = string.split(protocol.sep.encode())
        try:
            msg = cls(protocol, packets[0], packets[1], packets[4:], compression=compressions)
        except IndexError:
            if compression_fail:
                raise ValueError("Could not decompress the message")
            raise
        msg.time = from_base_58(packets[3])
        msg.compression_fail = compression_fail
        return msg

    def __init__(self, protocol, msg_type, sender, payload, compression=None):
        self.protocol = protocol
        self.msg_type = msg_type
        self.sender = sender
        self.__payload = payload
        self.time = getUTC()
        if compression:
            self.compression = compression
        else:
            self.compression = []
        self.compression_fail = False

    @property
    def payload(self):
        for i in range(len(self.__payload)):
            if not isinstance(self.__payload[i], bytes):
                self.__payload[i] = self.__payload[i].encode()
        return self.__payload

    @property
    def compression_used(self):
        for method in intersect(compression, self.compression):
            return method
        return None

    @property
    def time_58(self):
        """Returns the messages timestamp in base_58"""
        return to_base_58(self.time)

    @property
    def id(self):
        """Returns the message id"""
        payload_string = self.protocol.sep.encode().join(self.payload)
        payload_hash = hashlib.sha384(payload_string + self.time_58.encode())
        return to_base_58(int(payload_hash.hexdigest(), 16))

    @property
    def packets(self):
        meta = [self.msg_type, self.sender, self.id, self.time_58]
        for i in range(len(meta)):
            if not isinstance(meta[i], bytes):
                meta[i] = meta[i].encode()
        return meta + self.payload

    @property
    def __non_len_string(self):
        string = self.protocol.sep.encode().join(self.packets)
        if self.compression_used:
            string = compress(string, self.compression_used)
        return string
    
    @property
    def string(self):
        """Returns a string representation of the message"""
        string = self.__non_len_string
        return struct.pack("!L", len(string)) + string

    def __len__(self):
        return len(self.__non_len_string)

    @property
    def len(self):
        return struct.pack("!L", self.__len__())

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
            self.__print(data, time.time(), level=5)
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except:
                pass
            return False
        self.buffer.append(data)
        self.time = getUTC()
        if not self.active and self.find_terminator():
            self.__print(self.buffer, self.expected, self.find_terminator(), level=4)
            self.expected = struct.unpack("!L", ''.encode().join(self.buffer))[0] + 4
            self.active = True
        return True

    def find_terminator(self):
        """Returns whether the definied return sequences is found"""
        return len(''.encode().join(self.buffer)) == self.expected

    def found_terminator(self):
        """Processes received messages"""
        raw_msg = ''.encode().join(self.buffer)
        self.expected = 4
        self.buffer = []
        self.active = False
        reply_object = self
        try:
            msg = pathfinding_message.feed_string(self.protocol, raw_msg, False, self.compression)
        except ValueError as e:
            if e.args[0] == "Could not decompress the message":
                self.send(flags.renegotiate, flags.compression, json.dumps([algo for algo in self.compression if algo is not method]))
                self.send(flags.renegotiate, flags.resend)
                return
            else: #if e.args[0] == "Must assert struct.unpack(\"!L\", string[:4])[0] == len(string[4:]).":
                raise
        packets = msg.packets
        self.__print("Message received: %s" % packets, level=1)
        if packets[0] == flags.waterfall:
            if (packets[2] in (i for i, t in self.server.waterfalls)):
                self.__print("Waterfall already captured", level=2)
                return
            self.__print("New waterfall received. Proceeding as normal", level=2)
            reply_object = packets[1]
        elif packets[0] == flags.renegotiate:
            if packets[4] == flags.compression:
                respond = (self.compression != json.loads(packets[5]))
                self.compression = json.loads(packets[5])
                self.__print("Compression methods changed to: %s" % repr(self.compression), level=2)
                if respond:
                    self.send(flags.renegotiate, flags.compression, json.dumps(intersect(compression, self.compression)))
                return
            elif packets[4] == flags.resend:
                self.send(*self.last_sent)
                return
        msg = self.protocol.sep.encode().join(packets[4:])  # Handle request without routing headers
        self.server.handle_request(message(msg, reply_object, self.protocol, from_base_58(packets[3]), self.server))

    def send(self, msg_type, *args, **kargs):
        """Sends a message through its connection. The first argument is message type. All after that are content packets"""
        # This section handles waterfall-specific flags
        id = kargs.get('id')
        if not id:
            id = self.server.id
        if kargs.get('time'):
            time = from_base_58(kargs.get('time'))
        else:
            time = getUTC()
        # Begin real method
        msg = pathfinding_message(self.protocol, msg_type, id, list(args), self.compression)
        if (msg.id, msg.time) not in self.server.waterfalls:
            self.server.waterfalls.appendleft((msg.id, msg.time))
        if msg_type in [flags.whisper, flags.broadcast]:
            self.last_sent = [msg_type] + list(args)
        self.__print("Sending %s to %s" % ([msg.len] + msg.packets, self), level=4)
        if msg.compression_used: self.__print("Compressing with %s" % msg.compression_used, level=4)
        try:
            self.sock.send(msg.string)
        except IOError as e:
            self.server.daemon.exceptions.append((e, traceback.format_exc()))
            self.server.daemon.disconnect(self)

    def fileno(self):
        return self.sock.fileno()

    def __print(self, *args, **kargs):
        """Private method to print if level is <= self.server.debug_level"""
        self.server.__print__(*args, **kargs)


class p2p_daemon(object):
    def __init__(self, addr, port, server, prot=default_protocol):
        self.protocol = prot
        self.server = server
        if self.protocol.encryption == "Plaintext":
            self.sock = socket.socket()
        elif self.protocol.encryption == "PKCS1_v1.5":
            import net
            self.sock = net.secure_socket(silent=True)
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
                self.__print('Incoming connection from %s' % repr(addr), level=1)
                handler = p2p_connection(conn, self.server, self.protocol)
                handler.send(flags.whisper, flags.handshake, self.server.id, self.protocol.id, json.dumps(self.server.out_addr), json.dumps(compression))
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
                                self.__print("disconnecting node %s while in loop" % handler.id, level=6)
                                self.disconnect(handler)
                                raise socket.timeout()  # Quick, error free breakout
                        handler.found_terminator()
                    except socket.timeout:
                        continue  # Shouldn't happen with select, but if it does...
                    except Exception as e:
                        if isinstance(e, socket.error) and e.args[0] in [9, 104, 10054, 10058]:
                            node_id = handler.id
                            if not node_id:
                                node_id = repr(handler)
                            self.__print("Node %s has disconnected from the network" % node_id, level=1)
                        else:
                            self.__print("There was an unhandled exception with peer id %s. This peer is being disconnected, and the relevant exception is added to the debug queue. If you'd like to report this, please post a copy of your p2p_socket.daemon.exceptions list to github.com/gappleto97/python-utils." % handler.id, level=0)
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
        self.__print("Connection to node %s has been closed" % node_id, level=1)
        if handler in self.server.awaiting_ids:
            self.server.awaiting_ids.remove(handler)
        elif self.server.routing_table.get(handler.id):
            self.server.routing_table.pop(handler.id)

    def __print(self, *args, **kargs):
        """Private method to print if level is <= self.server.debug_level"""
        self.server.__print__(*args, **kargs)


class p2p_socket(object):
    def __init__(self, addr, port, prot=default_protocol, out_addr=None, debug_level=0):
        self.protocol = prot
        self.debug_level = debug_level
        self.routing_table = {}     # In format {ID: handler}
        self.awaiting_ids = []      # Connected, but not handshook yet
        self.requests = {}          # Metadata about message replies where you aren't connected to the sender
        self.waterfalls = deque()   # Metadata of messages to waterfall
        self.queue = deque()        # Queue of received messages. Access through recv()
        if out_addr:                # Outward facing address, if you're port forwarding
            self.out_addr = out_addr
        else:
            self.out_addr = addr, port
        info = [str(out_addr), prot.id, user_salt]
        h = hashlib.sha384(''.join(info).encode())
        self.id = to_base_58(int(h.hexdigest(), 16))
        self.daemon = p2p_daemon(addr, port, self, prot)

    @property
    def status(self):
        return len(self.daemon.exceptions) or "Nominal"   

    @property
    def outgoing(self):
        """IDs of outgoing connections"""
        return [handler.id for handler in self.routing_table.values() if handler.outgoing]

    @property
    def incoming(self):
        """IDs of incoming connections"""
        return [handler.id for handler in self.routing_table.values() if not handler.outgoing]

    def handle_request(self, msg):
        """Decides how to handle various message types, allowing some to be handled automatically"""
        handler = msg.sender
        packets = msg.packets
        if packets[0] == flags.handshake:
            if packets[2] != self.protocol.id.encode():
                handler.sock.close()
                self.awaiting_ids.remove(handler)
                return
            handler.id = packets[1]
            handler.addr = json.loads(packets[3].decode())
            handler.compression = json.loads(packets[4].decode())
            self.__print("Compression methods changed to %s" % repr(handler.compression), level=4)
            if handler in self.awaiting_ids:
                self.awaiting_ids.remove(handler)
            self.routing_table.update({packets[1]: handler})
            handler.send(flags.whisper, flags.peers, json.dumps([(self.routing_table[key].addr, key.decode()) for key in self.routing_table.keys()]))
        elif packets[0] == flags.peers:
            new_peers = json.loads(packets[1].decode())
            for addr, id in new_peers:
                if len(self.outgoing) < max_outgoing and addr:
                    self.connect(addr[0], addr[1], id)
        elif packets[0] == flags.response:
            self.__print("Response received for request id %s" % packets[1], level=1)
            if self.requests.get(packets[1]):
                addr = json.loads(packets[2].decode())
                if addr:
                    msg = self.requests.get(packets[1])
                    self.requests.pop(packets[1])
                    self.connect(addr[0][0], addr[0][1], addr[1])
                    self.routing_table[addr[1]].send(*msg)
        elif packets[0] == flags.request:
            if self.routing_table.get(packets[2]):
                handler.send(flags.broadcast, flags.response, packets[1], json.dumps([self.routing_table.get(packets[2]).addr, packets[2].decode()]))
            elif packets[2] == '*'.encode():
                self.send(flags.broadcast, flags.peers, json.dumps([(key, self.routing_table[key].addr) for key in self.routing_table.keys()]))
        elif packets[0] == flags.whisper:
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
            send_type = flags.broadcast
        # map(methodcaller('send', 'broadcast', 'broadcast', *args), self.routing_table.values())
        for handler in self.routing_table.values():
            handler.send(flags.broadcast, send_type, *args)

    def waterfall(self, msg):
        """Handles the waterfalling of received messages"""
        # self.cleanup()
        self.__print(msg.id, [i for i, t in self.waterfalls], level=5)
        if msg.id not in (i for i, t in self.waterfalls):
            self.waterfalls.appendleft((msg.id, msg.time))
            if isinstance(msg.sender, p2p_connection):
                id = msg.sender.id
            else:
                id = msg.sender
            for handler in self.routing_table.values():
                handler.send(flags.waterfall, *msg.packets, time=to_base_58(msg.time), id=id)
            self.waterfalls = deque(set(self.waterfalls))
            self.waterfalls = deque([i for i in self.waterfalls if i[1] - getUTC() > 60])
            while len(self.waterfalls) > 100:
                self.waterfalls.pop()
            return True
        self.__print("Not rebroadcasting", level=3)
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
        self.__print("Attempting connection to %s:%s" % (addr, port), level=1)
        if socket.getaddrinfo(addr, port)[0] == socket.getaddrinfo(*self.out_addr)[0] or \
                                                            id in self.routing_table.keys():
            self.__print("Connection already established", level=1)
            return False
        if self.protocol.encryption == "Plaintext":
            conn = socket.socket()
        elif self.protocol.encryption == "PKCS1_v1.5":
            import net
            conn = net.secure_socket(silent=True)
        conn.settimeout(0.01)
        conn.connect((addr, port))
        handler = p2p_connection(conn, self, self.protocol, outgoing=True)
        handler.id = id
        handler.send(flags.whisper, flags.handshake, self.id, self.protocol.id, json.dumps(self.out_addr), json.dumps(compression))
        if not id:
            self.awaiting_ids.append(handler)
        else:
            self.routing_table.update({id: handler})
        # print("Appended ", port, addr, " to handler list: ", handler)

    def __print__(self, *args, **kargs):
        """Private method to print if level is <= self.__debug_level"""
        if kargs.get('level') <= self.debug_level:
            print(*args)