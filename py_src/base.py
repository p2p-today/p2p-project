"""A library to store common functions and protocol definitions"""

from __future__ import print_function
from __future__ import absolute_import

import hashlib
import inspect
import json
import socket
import struct
import sys
import threading
import traceback
import uuid

from collections import namedtuple
from .utils import getUTC, intersect, get_lan_ip, get_socket

protocol_version = "0.4"
node_policy_version = "231"

version = '.'.join([protocol_version, node_policy_version])

plock = threading.Lock()

class brepr(bytearray):
    """This class is used so that it prints the description, rather than the value"""
    def __init__(self, value, rep=None):
        super(brepr, self).__init__(value)
        self.__rep = (rep or value)
        
    def __repr__(self):
        return self.__rep

class flags():
    """A namespace to hold protocol-defined flags"""
    # Reserved set of bytes
    reserved = set([struct.pack('!B', x) for x in range(0x13)])

    # main flags
    broadcast   = brepr(b'\x00', rep='broadcast')   # also sub-flag
    waterfall   = brepr(b'\x01', rep='waterfall')
    whisper     = brepr(b'\x02', rep='whsiper')     # also sub-flag
    renegotiate = brepr(b'\x03', rep='renegotiate')
    ping        = brepr(b'\x04', rep='ping')        # Unused, but reserved
    pong        = brepr(b'\x05', rep='pong')        # Unused, but reserved

    # sub-flags
    compression = brepr(b'\x06', rep='compression')
    handshake   = brepr(b'\x07', rep='handshake')
    notify      = brepr(b'\x08', rep='notify')
    peers       = brepr(b'\x09', rep='peers')
    request     = brepr(b'\x0A', rep='request')
    resend      = brepr(b'\x0B', rep='resend')
    response    = brepr(b'\x0C', rep='response')
    store       = brepr(b'\x0D', rep='store')

    # compression methods
    gzip = brepr(b'\x10', rep='gzip')
    bz2  = brepr(b'\x11', rep='bz2')
    lzma = brepr(b'\x12', rep='lzma')

user_salt    = str(uuid.uuid4()).encode()
compression = []  # This should be in order of preference, with None being implied as last

# Compression testing section

try:
    import zlib
    compression.append(flags.gzip)
except:  # pragma: no cover
    pass

try:
    import bz2
    compression.append(flags.bz2)
except:  # pragma: no cover
    pass

try:
    import lzma
    compression.append(flags.lzma)
except:  # pragma: no cover
    pass

json_compressions = json.dumps([method.decode() for method in compression])

# Utility method/class section; feel free to mostly ignore

base_58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


def to_base_58(i):  # returns bytes
    """Takes an integer and returns its corresponding base_58 string"""
    string = ""
    while i:
        string = base_58[i % 58] + string
        i = i // 58
    if not string:
        string = base_58[0]
    return string.encode()


def from_base_58(string):  # returns int (or long)
    """Takes a base_58 string and returns its corresponding integer"""
    decimal = 0
    if isinstance(string, (bytes, bytearray)):
        string = string.decode()
    for char in string:
        decimal = decimal * 58 + base_58.index(char)
    return decimal


def compress(msg, method):  # takes bytes, returns bytes
    """Shortcut method for compression"""
    if method == flags.gzip:
        return zlib.compress(msg)
    elif method == flags.bz2:
        return bz2.compress(msg)
    elif method == flags.lzma:
        return lzma.compress(msg)
    else:  # pragma: no cover
        raise Exception('Unknown compression method')


def decompress(msg, method):  # takes bytes, returns bytes
    """Shortcut method for decompression"""
    if method == flags.gzip:
        return zlib.decompress(msg, zlib.MAX_WBITS | 32)
    elif method == flags.bz2:
        return bz2.decompress(msg)
    elif method == flags.lzma:
        return lzma.decompress(msg)
    else:  # pragma: no cover
        raise Exception('Unknown decompression method')


class protocol(namedtuple("protocol", ['subnet', 'encryption'])):
    """Defines service variables so that you can reject connections looking for a different service"""
    @property
    def id(self):
        h = hashlib.sha256(''.join([str(x) for x in self] + [protocol_version]).encode())
        return to_base_58(int(h.hexdigest(), 16))

default_protocol = protocol('', "Plaintext")  # PKCS1_v1.5")


class base_connection(object):
    """The base class for a connection"""
    def __init__(self, sock, server, outgoing=False):
        self.sock = sock
        self.server = server
        self.outgoing = outgoing
        self.buffer = []
        self.id = None
        self.time = getUTC()
        self.addr = None
        self.compression = []
        self.last_sent = []
        self.expected = 4
        self.active = False

    def send(self, msg_type, *args, **kargs):
        """Sends a message through its connection. The first argument is message type. All after that are content packets"""
        # This section handles waterfall-specific flags
        id = kargs.get('id', self.server.id)  # Latter is returned if key not found
        time = kargs.get('time', getUTC())
        # Begin real method
        msg = pathfinding_message(self.protocol, msg_type, id, list(args), self.compression)
        if msg_type in [flags.whisper, flags.broadcast]:
            self.last_sent = [msg_type] + list(args)
        self.__print__("Sending %s to %s" % ([msg.len] + msg.packets, self), level=4)
        if msg.compression_used: self.__print__("Compressing with %s" % msg.compression_used, level=4)
        try:
            self.sock.send(msg.string)
            return msg
        except (IOError, socket.error) as e:  # pragma: no cover
            self.server.daemon.exceptions.append((e, traceback.format_exc()))
            self.server.disconnect(self)

    @property
    def protocol(self):
        return self.server.protocol

    def collect_incoming_data(self, data):
        """Collects incoming data"""
        if not bool(data):
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

    def found_terminator(self):
        """Processes received messages"""
        raw_msg = ''.encode().join(self.buffer)
        self.expected = 4
        self.buffer = []
        self.active = False
        msg = pathfinding_message.feed_string(self.protocol, raw_msg, False, self.compression)
        return msg

    def handle_renegotiate(self, packets):
        if packets[0] == flags.renegotiate:
            if packets[4] == flags.compression:
                encoded_methods = [algo.encode() for algo in json.loads(packets[5].decode())]
                respond = (self.compression != encoded_methods)
                self.compression = encoded_methods
                self.__print__("Compression methods changed to: %s" % repr(self.compression), level=2)
                if respond:
                    decoded_methods = [algo.decode() for algo in intersect(compression, self.compression)]
                    self.send(flags.renegotiate, flags.compression, json.dumps(decoded_methods))
                return True
            elif packets[4] == flags.resend:
                self.send(*self.last_sent)
                return True

    def fileno(self):
        return self.sock.fileno()

    def __print__(self, *args, **kargs):
        """Private method to print if level is <= self.server.debug_level"""
        self.server.__print__(*args, **kargs)


class base_daemon(object):
    """The base class for a daemon"""    
    def __init__(self, addr, port, server):
        self.server = server
        self.sock = get_socket(self.protocol, True)
        self.sock.bind((addr, port))
        self.sock.listen(5)
        self.sock.settimeout(0.1)
        self.exceptions = []
        self.alive = True
        self.main_thread = threading.current_thread()
        self.daemon = threading.Thread(target=self.mainloop)
        self.daemon.start()

    @property
    def protocol(self):
        return self.server.protocol

    def kill_old_nodes(self, handler):
        """Cleans out connections which never finish a message"""
        if handler.active and handler.time < getUTC() - 60:
            self.server.disconnect(handler)

    def __del__(self):
        self.alive = False
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except:  # pragma: no cover
            pass

    def __print__(self, *args, **kargs):
        """Private method to print if level is <= self.server.debug_level"""
        self.server.__print__(*args, **kargs)


class base_socket(object):
    """The base class for a peer-to-peer socket"""
    def __init__(self, addr, port, prot=default_protocol, out_addr=None, debug_level=0):
        self.protocol = prot
        self.debug_level = debug_level
        self.routing_table = {}     # In format {ID: handler}
        self.awaiting_ids = []      # Connected, but not handshook yet
        if out_addr:                # Outward facing address, if you're port forwarding
            self.out_addr = out_addr
        elif addr == '0.0.0.0':
            self.out_addr = get_lan_ip(), port
        else:
            self.out_addr = addr, port
        info = [str(self.out_addr).encode(), prot.id, user_salt]
        h = hashlib.sha384(b''.join(info))
        self.id = to_base_58(int(h.hexdigest(), 16))
        self.__handlers = []
        self.__closed = False

    def close(self):
        if self.__closed:
            raise RuntimeError("Already closed")
        else:
            self.daemon.alive = False
            self.daemon.daemon.join()
            self.debug_level = 0
            try:
                self.daemon.sock.shutdown(socket.SHUT_RDWR)
            except:
                pass
            conns = list(self.routing_table.values()) + self.awaiting_ids
            for conn in conns:
                self.disconnect(conn)
            self.__closed = True

    if sys.version_info >= (3, ):
        def register_handler(self, method):
            """Register a handler for incoming method. Should be roughly of the form:
            def handler(msg, handler):
                packets = msg.packets
                if packets[0] == expected_value:
                    action()
                    return True
            """
            args = inspect.signature(method)
            if len(args.parameters) != (3 if args.parameters.get('self') else 2):
                raise ValueError("This method must contain exactly two arguments (or three if first is self)")
            self.__handlers.append(method)

    else:
        def register_handler(self, method):
            """Register a handler for incoming method. Should be roughly of the form:
            def handler(msg, handler):
                packets = msg.packets
                if packets[0] == expected_value:
                    action()
                    return True
            """
            args = inspect.getargspec(method)
            if args[1:] != (None, None, None) or len(args[0]) != (3 if args[0][0] == 'self' else 2):
                raise ValueError("This method must contain exactly two arguments (or three if first is self)")
            self.__handlers.append(method)

    def handle_msg(self, msg, conn):
        """Decides how to handle various message types, allowing some to be handled automatically"""
        for handler in self.__handlers:
            self.__print__("Checking handler: %s" % handler.__name__, level=4)
            if handler(msg, conn):
                self.__print__("Breaking from handler: %s" % handler.__name__, level=4)
                return True

    @property
    def status(self):
        """Returns "Nominal" if all is going well, or a list of unexpected (Excpetion, traceback) tuples if not"""
        return self.daemon.exceptions or "Nominal"

    def __print__(self, *args, **kargs):
        """Private method to print if level is <= self.__debug_level"""
        if kargs.get('level') <= self.debug_level:
            with plock:
                print(self.out_addr[1], *args)

    def __del__(self):
        if not self.__closed:
            self.close()


class pathfinding_message(object):
    """An object used to build and parse protocol-defined message structures"""
    @classmethod
    def feed_string(cls, protocol, string, sizeless=False, compressions=None):
        """Constructs a pathfinding_message from a string or bytes object.
        Possible errors:
            AttributeError: Fed a non-string, non-bytes argument
            AssertionError: Initial size header is incorrect
            Exception:      Unrecognized compression method fed in compressions
            struct.error:   Packet headers are incorrect OR unrecognized compression
            IndexError:     See struct.error"""
        # First section checks size header
        string = cls.sanitize_string(string, sizeless)
        # Then we attempt to decompress
        string, compression_fail = cls.decompress_string(string, compressions)
        # After this, we process the packet size headers
        packets = cls.process_string(string)
        msg = cls(protocol, packets[0], packets[1], packets[4:], compression=compressions)
        msg.time = from_base_58(packets[3])
        msg.compression_fail = compression_fail
        return msg

    @classmethod
    def sanitize_string(cls, string, sizeless=False):
        """Removes the size header for further processing. Also checks if the header is valid.
        Possible errors:
            AttributeError: Fed a non-string, non-bytes argument
            AssertionError: Initial size header is incorrect"""
        if not isinstance(string, (bytes, bytearray)):
            string = string.encode()
        if not sizeless:
            assert struct.unpack('!L', string[:4])[0] == len(string[4:]), \
                "Must assert struct.unpack('!L', string[:4])[0] == len(string[4:])"
            string = string[4:]
        return string

    @classmethod
    def decompress_string(cls, string, compressions=None):
        """Returns a tuple containing the decompressed bytes and a boolean as to whether decompression failed or not
        Possible errors:
            Exception:  Unrecognized compression method fed in compressions"""
        compression_fail = False
        for method in intersect(compressions, compression):  # second is module scope compression
            try:
                string = decompress(string, method)
                compression_fail = False
                break
            except:
                compression_fail = True
                continue
        return (string, compression_fail)

    @classmethod
    def process_string(cls, string):
        """Given a sanitized, plaintext string, returns a list of its packets
        Possible errors:
            struct.error:   Packet headers are incorrect OR not fed plaintext
            IndexError:     See struct.error"""
        processed, expected = 0, len(string)
        pack_lens, packets = [], []
        while processed != expected:
            pack_lens.extend(struct.unpack("!L", string[processed:processed+4]))
            processed += 4
            expected -= pack_lens[-1]
        # Then reconstruct the packets
        for index, length in enumerate(pack_lens):
            start = processed + sum(pack_lens[:index])
            end = start + length
            packets.append(string[start:end])
        return packets

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
        """Returns a list containing the message payload encoded as bytes"""
        for i, val in enumerate(self.__payload):
            if not isinstance(val, (bytes, bytearray)):
                self.__payload[i] = val.encode()
        return self.__payload

    @property
    def compression_used(self):
        """Returns the compression method this message is using"""
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
        payload_string = b''.join((bytes(pac) for pac in self.payload))
        payload_hash = hashlib.sha384(payload_string + self.time_58)
        return to_base_58(int(payload_hash.hexdigest(), 16))

    @property
    def packets(self):
        """Returns the full list of packets in this message encoded as bytes, excluding the header"""
        meta = [self.msg_type, self.sender, self.id, self.time_58]
        for i, val in enumerate(meta):
            if not isinstance(val, (bytes, bytearray)):
                meta[i] = val.encode()
        return meta + self.payload

    @property
    def __non_len_string(self):
        """Returns a bytes object containing the entire message, excepting the total length header"""
        packets = self.packets
        header = struct.pack("!" + str(len(packets)) + "L", 
                                    *[len(x) for x in packets])
        string = header + b''.join((bytes(pac) for pac in packets))
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
        """Return the struct-encoded length header"""
        return struct.pack("!L", self.__len__())


class message(object):
    """An object which gets returned to a user, containing all necessary information to parse and reply to a message"""
    def __init__(self, msg, server):
        if not isinstance(msg, pathfinding_message):  # pragma: no cover
            raise TypeError("message must be passed a pathfinding_message")
        self.msg = msg
        self.server = server

    @property
    def time(self):
        """The time this message was sent at"""
        return self.msg.time

    @property
    def time_58(self):
        """Returns the messages timestamp in base_58"""
        return self.msg.time_58

    @property
    def sender(self):
        """The ID of this message's sender"""
        return self.msg.sender

    @property
    def protocol(self):
        """The protocol this message was sent under"""
        return self.msg.protocol
    
    @property
    def id(self):
        """This message's ID"""
        return self.msg.id

    @property
    def packets(self):
        """Return the message's component packets, including it's type in position 0"""
        return self.msg.payload

    def __len__(self):
        return self.msg.__len__()

    def __repr__(self):
        packets = self.packets
        string = "message(type=" + repr(packets[0]) + ", packets=" + repr(packets[1:]) + ", sender="
        if isinstance(self.sender, base_connection):  # This should no longer happen, but just in case
            return string + repr(self.sender.addr) + ")"
        else:
            return string + repr(self.sender) + ")"

    def reply(self, *args):
        """Replies to the sender if you're directly connected. Tries to make a connection otherwise"""
        if self.server.routing_table.get(self.sender):
            self.server.routing_table.get(self.sender).send(flags.whisper, flags.whisper, *args)
        else:
            request_hash = hashlib.sha384(self.sender + to_base_58(getUTC())).hexdigest()
            request_id = to_base_58(int(request_hash, 16))
            self.server.send(request_id, self.sender, type=flags.request)
            self.server.requests.update({request_id: [flags.whisper, flags.whisper] + list(args)})
            print("You aren't connected to the original sender. This reply is not guarunteed, but we're trying to make a connection and put the message through.")
