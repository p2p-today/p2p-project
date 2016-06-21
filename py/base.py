from __future__ import print_function
import bz2, hashlib, json, select, socket, struct, time, threading, traceback, uuid, zlib
from collections import namedtuple, deque

version = "0.2.0"

class flags():
    broadcast   = b'broadcast'
    waterfall   = b'waterfall'
    whisper     = b'whisper'
    renegotiate = b'renegotiate'

    handshake   = b'handshake'
    request     = b'request'
    response    = b'response'
    resend      = b'resend'
    peers       = b'peers'
    compression = b'compression'

    gzip = b'gzip'
    bz2  = b'bz2'
    lzma = b'lzma'

user_salt    = str(uuid.uuid4()).encode()
compression = [flags.gzip, flags.bz2]  # This should be in order of preference. IE: gzip is best, then bz2, then none

try:
    import lzma
    compression.append(flags.lzma)
except:
    pass

# Utility method/class section; feel free to mostly ignore

base_58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


def to_base_58(i):  # returns bytes
    """Takes an integer and returns its corresponding base_58 string"""
    string = ""
    while i:
        string = base_58[i % 58] + string
        i = i // 58
    return string.encode()


def from_base_58(string):  # returns int (or long)
    """Takes a base_58 string and returns its corresponding integer"""
    decimal = 0
    if isinstance(string, bytes):
        string = string.decode()
    for char in string:
        decimal = decimal * 58 + base_58.index(char)
    return decimal


def getUTC():  # returns int
    """Returns the current unix time in UTC"""
    import calendar, time
    return calendar.timegm(time.gmtime())


def compress(msg, method):  # takes bytes, returns bytes
    """Shortcut method for compression"""
    if method == flags.gzip:
        return zlib.compress(msg)
    elif method == flags.bz2:
        return bz2.compress(msg)
    elif method == flags.lzma:
        return lzma.compress(msg)
    else:
        raise Exception('Unknown compression method')


def decompress(msg, method):  # takes bytes, returns bytes
    """Shortcut method for decompression"""
    if method == flags.gzip:
        return zlib.decompress(msg, zlib.MAX_WBITS | 32)
    elif method == flags.bz2:
        return bz2.decompress(msg)
    elif method == flags.lzma:
        return lzma.decompress(msg)
    else:
        raise Exception('Unknown decompression method')


def intersect(*args):  # returns list
    """Returns the ordered intersection of all given iterables, where the order is defined by the first iterable"""
    if not all(args):
        return []
    intersection = args[0]
    for l in args[1:]:
        intersection = [item for item in intersection if item in l]
    return intersection


def get_lan_ip():
    """Retrieves the LAN ip. Expanded from http://stackoverflow.com/a/28950776"""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('8.8.8.8', 23))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.shutdown(socket.SHUT_RDWR)


class protocol(namedtuple("protocol", ['sep', 'subnet', 'encryption'])):
    @property
    def id(self):
        h = hashlib.sha256(''.join([str(x) for x in self] + [version]).encode())
        return to_base_58(int(h.hexdigest(), 16))

default_protocol = protocol("\x1c\x1d\x1e\x1f", '', "Plaintext")  # PKCS1_v1.5")


class base_connection(object):
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
            self.__print__(data, time.time(), level=5)
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except:
                pass
            return False
        self.buffer.append(data)
        self.time = getUTC()
        if not self.active and self.find_terminator():
            self.__print__(self.buffer, self.expected, self.find_terminator(), level=4)
            self.expected = struct.unpack("!L", ''.encode().join(self.buffer))[0] + 4
            self.active = True
        return True

    def find_terminator(self):
        """Returns whether the definied return sequences is found"""
        return len(''.encode().join(self.buffer)) == self.expected

    def fileno(self):
        return self.sock.fileno()

    def __print__(self, *args, **kargs):
        """Private method to print if level is <= self.server.debug_level"""
        self.server.__print__(*args, **kargs)


class base_daemon(object):
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

    def __print__(self, *args, **kargs):
        """Private method to print if level is <= self.server.debug_level"""
        self.server.__print__(*args, **kargs)


class base_socket(object):
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

    @property
    def status(self):
        return self.daemon.exceptions or "Nominal"   

    @property
    def outgoing(self):
        """IDs of outgoing connections"""
        return [handler.id for handler in self.routing_table.values() if handler.outgoing]

    @property
    def incoming(self):
        """IDs of incoming connections"""
        return [handler.id for handler in self.routing_table.values() if not handler.outgoing]

    def __print__(self, *args, **kargs):
        """Private method to print if level is <= self.__debug_level"""
        if kargs.get('level') <= self.debug_level:
            print(*args)


class message(namedtuple("message", ['msg', 'sender', 'protocol', 'time', 'server'])):
    def reply(self, *args):
        """Replies to the sender if you're directly connected. Tries to make a connection otherwise"""
        if isinstance(self.sender, base_connection):
            self.sender.send(flags.whisper, flags.whisper, *args)
        elif self.server.routing_table.get(self.sender):
            self.server.routing_table.get(self.sender).send(flags.whisper, flags.whisper, *args)
        else:
            request_hash = hashlib.sha384(self.sender + to_base_58(getUTC())).hexdigest()
            request_id = to_base_58(int(request_hash, 16))
            self.server.send(request_id, self.sender, type=flags.request)
            self.server.requests.update({request_id: [flags.whisper, flags.whisper] + list(args)})
            print("You aren't connected to the original sender. This reply is not guarunteed, but we're trying to make a connection and put the message through.")

    def __repr__(self):
        string = "message(type=" + repr(self.packets[0]) + ", packets=" + repr(self.packets[1:]) + ", sender="
        if isinstance(self.sender, base_connection):
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
            msg_hash = hashlib.sha384(self.msg.encode() + to_base_58(self.time))
        else:
            msg_hash = hashlib.sha384(self.msg + to_base_58(self.time))            
        return to_base_58(int(msg_hash.hexdigest(), 16))


class pathfinding_message(object):
    @classmethod
    def feed_string(cls, protocol, string, sizeless=False, compressions=None):
        """Constructs a pathfinding_message from a string."""
        if not sizeless:
            assert struct.unpack('!L', string[:4])[0] == len(string[4:]), \
                "Must assert struct.unpack('!L', string[:4])[0] == len(string[4:])"
            string = string[4:]
        compression_fail = False
        for method in intersect(compressions, compression):  # second is module scope compression
            try:
                string = decompress(string, method)
                compression_fail = False
                break
            except:
                compression_fail = True
                continue
        packets = string.split(protocol.sep.encode())
        msg = cls(protocol, packets[0], packets[1], packets[4:], compression=compressions)
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
        payload_hash = hashlib.sha384(payload_string + self.time_58)
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