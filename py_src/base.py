"""A library to store common functions and protocol definitions"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import with_statement

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
from itertools import chain

from .utils import (
    getUTC, intersect, get_lan_ip, get_socket, sanitize_packet, inherit_doc)

protocol_version = "0.5"
node_policy_version = "607"

version = '.'.join((protocol_version, node_policy_version))

plock = threading.Lock()


class flags():
    """A namespace to hold protocol-defined flags"""
    # Reserved set of bytes
    reserved = [struct.pack('!B', x) for x in range(0x30)]

    # main flags
    broadcast = b'\x00'     # also sub-flag
    renegotiate = b'\x01'
    whisper = b'\x02'       # also sub-flag
    ping = b'\x03'          # Unused, but reserved
    pong = b'\x04'          # Unused, but reserved

    # sub-flags
    # broadcast = b'\x00'
    compression = b'\x01'
    # whisper = b'\x02'
    # ping = b'\x03'
    # pong = b'\x04'
    handshake = b'\x05'
    notify = b'\x06'
    peers = b'\x07'
    request = b'\x08'
    resend = b'\x09'
    response = b'\x0A'
    store = b'\x0B'
    retrieve = b'\x0C'
    retrieved = b'\x0D'

    # implemented compression methods
    bz2 = b'\x10'
    gzip = b'\x11'
    lzma = b'\x12'
    zlib = b'\x13'
    snappy = b'\x20'

    # non-implemented compression methods (based on list from compressjs):
    bwtc = b'\x14'
    context1 = b'\x15'
    defsum = b'\x16'
    dmc = b'\x17'
    fenwick = b'\x18'
    huffman = b'\x19'
    lzjb = b'\x1A'
    lzjbr = b'\x1B'
    lzp3 = b'\x1C'
    mtf = b'\x1D'
    ppmd = b'\x1E'
    simple = b'\x1F'


user_salt = str(uuid.uuid4()).encode()
# This should be in order of preference, with None being implied as last
compression = []

# Compression testing section

try:
    import snappy
    if hasattr(snappy, 'compress'):
        compression.append(flags.snappy)
except ImportError:  # pragma: no cover
    pass

try:
    import zlib
    if hasattr(zlib, 'compressobj'):
        compression.extend((flags.zlib, flags.gzip))
except ImportError:  # pragma: no cover
    pass

try:
    import bz2
    if hasattr(bz2, 'compress'):
        compression.append(flags.bz2)
except ImportError:  # pragma: no cover
    pass

try:
    import lzma
    if hasattr(lzma, 'compress'):
        compression.append(flags.lzma)
except ImportError:  # pragma: no cover
    pass

json_compressions = json.dumps([method.decode() for method in compression])


def compress(msg, method):
    """Shortcut method for compression

    Args:
        msg:    The message you wish to compress, the type required is
                    defined by the requested method
        method: The compression method you wish to use.
                    Supported (assuming installed):
                        :py:class:`~base.flags.gzip`,
                        :py:class:`~base.flags.zlib`,
                        :py:class:`~base.flags.bz2`,
                        :py:class:`~base.flags.lzma`

    Returns:
        Defined by the compression method, but typically the bytes of the
        compressed message

    Warning:
        The types fed are dependent on which compression method you use.
        Best to assume most values are :py:class:`bytes` or
        :py:class:`bytearray`

    Raises:
        A :py:class:`ValueError` if there is an unknown compression method,
            or a method-specific error
    """
    if method in (flags.gzip, flags.zlib):
        wbits = 15 + (16 * (method == flags.gzip))
        compressor = zlib.compressobj(
            zlib.Z_DEFAULT_COMPRESSION, zlib.DEFLATED, wbits)
        return compressor.compress(msg) + compressor.flush()
    elif method == flags.bz2:
        return bz2.compress(msg)
    elif method == flags.lzma:
        return lzma.compress(msg)
    elif method == flags.snappy:
        return snappy.compress(msg)
    else:  # pragma: no cover
        raise ValueError('Unknown compression method')


def decompress(msg, method):
    """Shortcut method for decompression

    Args:
        msg:    The message you wish to decompress, the type required is
                    defined by the requested method
        method: The decompression method you wish to use.
                    Supported (assuming installed):
                        :py:class:`~base.flags.gzip`,
                        :py:class:`~base.flags.zlib`,
                        :py:class:`~base.flags.bz2`,
                        :py:class:`~base.flags.lzma`

    Returns:
        Defined by the decompression method, but typically the bytes of the
        compressed message

    Warning:
        The types fed are dependent on which decompression method you use.
        Best to assume most values are :py:class:`bytes` or
        :py:class:`bytearray`

    Raises:
        A :py:class:`ValueError` if there is an unknown compression method,
            or a method-specific error
    """
    if method in (flags.gzip, flags.zlib):
        return zlib.decompress(msg, zlib.MAX_WBITS | 32)
    elif method == flags.bz2:
        return bz2.decompress(msg)
    elif method == flags.lzma:
        return lzma.decompress(msg)
    elif method == flags.snappy:
        return snappy.decompress(msg)
    else:  # pragma: no cover
        raise ValueError('Unknown decompression method')


if sys.version_info < (3, ):
    def pack_value(l, i):
        """For value i, pack it into bytes of size length

        Args:
            length: A positive, integral value describing how long to make
                        the packed array
            i:      A positive, integral value to pack into said array

        Returns:
            A bytes object containing the given value

        Raises:
            ValueError: If length is not large enough to contain the value
                            provided
        """
        ret = b""
        for x in range(l):
            ret = chr(i & 0xFF) + ret
            i = i >> 8
            if i == 0:
                break
        if i:
            raise ValueError("Value not allocatable in size given")
        return ("\x00" * (l - len(ret))) + ret

    def unpack_value(string):
        """For a string, return the packed value inside of it

        Args:
            string: A string or bytes-like object

        Returns:
            An integral value interpreted from this, as if it were a
            big-endian, unsigned integral
        """
        val = 0
        for char in string:
            val = val << 8
            val += ord(char)
        return val

else:
    def pack_value(l, i):
        """For value i, pack it into bytes of size length

        Args:
            length: A positive, integral value describing how long to make
                        the packed array
            i:      A positive, integral value to pack into said array

        Returns:
            A :py:class:`bytes` object containing the given value

        Raises:
            ValueError: If length is not large enough to contain the value
                            provided
        """
        ret = b""
        for x in range(l):
            ret = bytes([i & 0xFF]) + ret
            i = i >> 8
            if i == 0:
                break
        if i:
            raise ValueError("Value not allocatable in size given")
        return (b"\x00" * (l - len(ret))) + ret

    def unpack_value(string):
        """For a string, return the packed value inside of it

        Args:
            string: A string or bytes-like object

        Returns:
            An integral value interpreted from this, as if it were a
            big-endian, unsigned integral
        """
        val = 0
        if not isinstance(string, (bytes, bytearray)):
            string = bytes(string, 'raw_unicode_escape')
        val = 0
        for char in string:
            val = val << 8
            val += char
        return val


base_58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


def to_base_58(i):
    """Takes an integer and returns its corresponding base_58 string

    Args:
        i: The integral value you wish to encode

    Returns:
        A :py:class:`bytes` object which contains the base_58 string

    Raises:
        TypeError: If you feed a non-integral value
    """
    string = ""
    while i:
        string = base_58[i % 58] + string
        i = i // 58
    if not string:
        string = base_58[0]
    return string.encode()


def from_base_58(string):
    """Takes a base_58 string and returns its corresponding integer

    Args:
        string: The base_58 value you wish to decode (string, bytes,
                    or bytearray)

    Returns:
        Returns integral value which corresponds to the fed string
    """
    decimal = 0
    if isinstance(string, (bytes, bytearray)):
        string = string.decode()
    for char in string:
        decimal = decimal * 58 + base_58.index(char)
    return decimal


class protocol(namedtuple("protocol", ['subnet', 'encryption'])):
    """Defines service variables so that you can reject connections looking
    for a different service

    Attributes:
        subnet:     The subnet flag this protocol uses
        encryption: The encryption method this protocol uses
        id:         The SHA-256 based ID of this protocol
    """
    @property
    def id(self):
        """The SHA-256-based ID of the protocol"""
        h = hashlib.sha256(''.join(str(x) for x in self).encode())
        h.update(protocol_version.encode())
        return to_base_58(int(h.hexdigest(), 16))

default_protocol = protocol('', "Plaintext")  # SSL")


class InternalMessage(object):
    """An object used to build and parse protocol-defined message structures"""
    @classmethod
    def __sanitize_string(cls, string, sizeless=False):
        """Removes the size header for further processing.
        Also checks if the header is valid.

        Args:
            string:     The string you wish to sanitize
            sizeless:   Whether this string is missing a size header
                            (default: ``False``)

        Returns:
            The fed string without the size header

        Raises:
           AttributeError: Fed a non-string, non-bytes argument
           AssertionError: Initial size header is incorrect
        """
        if not isinstance(string, (bytes, bytearray)):
            string = string.encode()
        if not sizeless:
            if unpack_value(string[:4]) != len(string[4:]):
                raise AssertionError(
                    "Real message size {} != expected size {}. Buffer given: {}".format(
                        len(string),
                        unpack_value(string[:4]) + 4,
                        string
                    ))
            string = string[4:]
        return string

    @classmethod
    def __decompress_string(cls, string, compressions=None):
        """Returns a tuple containing the decompressed bytes and a boolean
        as to whether decompression failed or not

        Args:
            string:         The possibly-compressed message you wish to parse
            compressions:   A list of the standard compression methods this
                                message may be under (default: [])

        Returns:
            A decompressed version of the message

        Raises:
           ValueError:  Unrecognized compression method fed in compressions

        Warning:
            Do not feed it with the size header, it will throw errors
        """
        compression_fail = False
        # second is module scope compression
        for method in intersect(compressions, compression):
            try:
                string = decompress(string, method)
                compression_fail = False
                break
            except:
                compression_fail = True
                continue
        return (string, compression_fail)

    @classmethod
    def __process_string(cls, string):
        """Given a sanitized, plaintext string, returns a list of its packets

        Args:
            string: The message you wish to parse

        Returns:
            A list containing the message's packets

        Raises:
           IndexError: Packet headers are incorrect OR not fed plaintext

        Warning:
            Do not feed a message with the size header.
            Do not feed a compressed message.
        """
        processed = 0
        packets = []
        while processed < len(string):
            pack_len = unpack_value(string[processed:processed+4])
            processed += 4
            end = processed + pack_len
            packets.append(string[processed:end])
            processed = end
        return packets

    @classmethod
    def feed_string(cls, string, sizeless=False, compressions=None):
        """Constructs a InternalMessage from a string or bytes object.

        Args:
            string:         The string you wish to parse
            sizeless:       A boolean which describes whether this string has
                                its size header (default: it does)
            compressions:   A list containing the standardized compression
                                methods this message might be under
                                (default: [])

        Returns:
            A base.InternalMessage from the given string

        Raises:
           AttributeError: Fed a non-string, non-bytes argument
           AssertionError: Initial size header is incorrect
           ValueError:     Unrecognized compression method fed in compressions
           IndexError:     Packet headers are incorrect OR
                               unrecognized compression
        """
        # First section checks size header
        string = cls.__sanitize_string(string, sizeless)
        # Then we attempt to decompress
        string, compression_fail = cls.__decompress_string(
            string, compressions)
        # After this, we process the packet size headers
        packets = cls.__process_string(string)
        msg = cls(packets[0], packets[1], packets[4:],
                  compression=compressions)
        msg.time = from_base_58(packets[3])
        msg.compression_fail = compression_fail
        assert packets[2] == msg.id, "Checksum failed"
        return msg

    def __init__(self, msg_type, sender, payload, compression=None,
                 timestamp=None):
        """Initializes a InternalMessage instance

        Args:
            msg_type:       A bytes-like header for the message you wish
                                to send
            sender:         A bytes-like sender ID the message is using
            payload:        A iterable of bytes-like objects containing the
                                payload of the message
            compression:    A list of the compression methods this message
                                may use (default: [])
            timestamp:      The current UTC timestamp (as an integer)
                                (default: result of utils.getUTC())

        Raises:
            TypeError:  If you feed an object which cannot convert to bytes

        Warning:
            If you feed a unicode object, it will be decoded using utf-8.
            All other objects are treated as raw bytes. If you desire a
            particular codec, encode it yourself before feeding it in.
        """
        self.msg_type = sanitize_packet(msg_type)
        self.sender = sanitize_packet(sender)
        self.__payload = tuple(sanitize_packet(packet) for packet in payload)
        self.time = timestamp or getUTC()
        self.compression_fail = False

        if compression:
            self.compression = compression
        else:
            self.compression = []

    @property
    def payload(self):
        """Returns a :py:class:`tuple` containing the message payload encoded
        as :py:class:`bytes`
        """
        return self.__payload

    @property
    def compression_used(self):
        """Returns the compression method this message is using"""
        for method in intersect(compression, self.compression):
            return method
        return None

    @property
    def time_58(self):
        """Returns this message's timestamp in base_58"""
        return to_base_58(self.time)

    @property
    def id(self):
        """Returns the message id"""
        payload_string = b''.join(bytes(pac) for pac in self.payload)
        payload_hash = hashlib.sha384(payload_string + self.time_58)
        return to_base_58(int(payload_hash.hexdigest(), 16))

    @property
    def packets(self):
        """Returns the full :py:class:`tuple` of packets in this message
        encoded as :py:class:`bytes`, excluding the header
        """
        return ((self.msg_type, self.sender, self.id, self.time_58) +
                    self.payload)

    @property
    def __non_len_string(self):
        """Returns a :py:class:`bytes` object containing the entire message,
        excepting the total length header
        """
        packets = self.packets
        headers = (pack_value(4, len(x)) for x in packets)
        string = b''.join(chain.from_iterable(zip(headers, packets)))
        if self.compression_used:
            string = compress(string, self.compression_used)
        return string

    @property
    def string(self):
        """Returns a :py:class:`bytes` representation of the message"""
        string = self.__non_len_string
        return pack_value(4, len(string)) + string

    def __len__(self):
        return len(self.__non_len_string)

    @property
    def len(self):
        """Return the struct-encoded length header"""
        return pack_value(4, self.__len__())


class base_connection(object):
    """The base class for a connection"""
    def __init__(self, sock, server, outgoing=False):
        """Sets up a connection to another peer-to-peer socket

        Args:
            sock:       The connected socket object
            server:     A reference to your peer-to-peer socket
            outgoing:   Whether this connection is outgoing (default: False)
        """
        self.sock = sock
        self.server = server
        self.outgoing = outgoing
        self.buffer = bytearray()
        self.id = None
        self.time = getUTC()
        self.addr = None
        self.compression = []
        self.last_sent = []
        self.expected = 4
        self.active = False

    def send_InternalMessage(self, msg):
        """Sends a preconstructed message

        Args:
            msg: The :py:class:`~py2p.base.IntenalMessage` you wish to send

        Returns:
            the :py:class:`~py2p.base.IntenalMessage` object you just sent, or
            ``None`` if the sending was unsuccessful
        """
        msg.compression = self.compression
        if msg.msg_type in (flags.whisper, flags.broadcast):
            self.last_sent = msg.payload
        self.__print__(
            "Sending %s to %s" % ((msg.len,) + msg.packets, self), level=4)
        if msg.compression_used:
            self.__print__(
                "Compressing with %s" % repr(msg.compression_used), level=4)
        try:
            self.sock.send(msg.string)
            return msg
        except (IOError, socket.error) as e:  # pragma: no cover
            self.server.daemon.exceptions.append(traceback.format_exc())
            self.server.disconnect(self)

    def send(self, msg_type, *args, **kargs):
        """Sends a message through its connection.

        Args:
            msg_type:  Message type, corresponds to the header in a
                           :py:class:`~py2p.base.InternalMessage` object
            *args:     A list of bytes-like objects, which correspond to the
                           packets to send to you
            **kargs:   There are two available keywords:
            id:        The ID this message should appear to be sent from
                           (default: your ID)
            time:      The time this message should appear to be sent from
                           (default: now in UTC)

        Returns:
            the :py:class:`~py2p.base.IntenalMessage` object you just sent, or
            ``None`` if the sending was unsuccessful
        """
        # Latter is returned if key not found
        id = kargs.get('id', self.server.id)
        time = kargs.get('time') or getUTC()
        # Begin real method
        msg = InternalMessage(
            msg_type, id, args, self.compression, timestamp=time)
        return self.send_InternalMessage(msg)

    @property
    def protocol(self):
        """Returns server.protocol"""
        return self.server.protocol

    def collect_incoming_data(self, data):
        """Collects incoming data

        Args:
            data:   The most recently received :py:class:`bytes`

        Returns:
            ``True`` if the data collection was successful, ``False`` if the
            connection was closed
        """
        if not bool(data):
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except:
                pass
            return False
        self.buffer.extend(data)
        self.time = getUTC()
        if not self.active and self.find_terminator():
            self.__print__(
                self.buffer, self.expected, self.find_terminator(), level=4)
            self.expected = unpack_value(bytes(self.buffer[:4])) + 4
            self.active = True
        return True

    def find_terminator(self):
        """Returns whether the defined return sequences is found"""
        return len(self.buffer) >= self.expected

    def found_terminator(self):
        """Processes received messages"""
        raw_msg, self.buffer = bytes(self.buffer[:self.expected]), self.buffer[self.expected:]
        self.__print__("Received: %s" % repr(raw_msg), level=6)
        self.active = len(self.buffer) > 4
        if self.active:
            self.expected = unpack_value(bytes(self.buffer[:4])) + 4
        else:
            self.expected = 4
        msg = InternalMessage.feed_string(raw_msg, False, self.compression)
        return msg

    def handle_renegotiate(self, packets):
        """The handler for connection renegotiations

        This is to deal with connection maintenance. For instance, it could
        be that a compression method fails to decode on the other end, and a
        node will need to renegotiate which methods it is using. Hence the
        name of the flag associated with it, "renegotiate".

        Args:
            packets:    A :py:class:`tuple` containing the packets received
                            in this message

        Returns:
            ``True`` if an action was taken, ``None`` if not
        """
        if packets[0] == flags.renegotiate:
            if packets[4] == flags.compression:
                encoded_methods = [
                    algo.encode() for algo in json.loads(packets[5].decode())]
                respond = (self.compression != encoded_methods)
                self.compression = encoded_methods
                self.__print__("Compression methods changed to: %s" %
                               repr(self.compression), level=2)
                if respond:
                    decoded_methods = [
                        algo.decode() for algo in intersect(
                            compression, self.compression)]
                    self.send(flags.renegotiate, flags.compression,
                              json.dumps(decoded_methods))
                return True
            elif packets[4] == flags.resend:
                self.send(*self.last_sent)
                return True

    def fileno(self):
        """Mirror for the fileno() method of the connection's
        underlying socket
        """
        return self.sock.fileno()

    def __print__(self, *args, **kargs):
        """Private method to print if level is <= self.server.debug_level

        Args:
            *args:   Each argument you wish to feed to the print method
            **kargs: One keyword is used here: level, which defines the
                         lowest value of self.server.debug_level at which
                         the message will be printed
        """
        self.server.__print__(*args, **kargs)


class base_daemon(object):
    """The base class for a daemon"""
    def __init__(self, addr, port, server):
        """Sets up a daemon process for your peer-to-peer socket

        Args:
            addr:   The address you wish to bind to
            port:   The port you wish to bind to
            server: A reference to the peer-to-peer socket

        Raises:
            socket.error: The address you wanted is already in use
            ValueError:   If your peer-to-peer socket is set up with an
                              unknown encryption method
        """
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
        """Returns server.protocol"""
        return self.server.protocol

    def kill_old_nodes(self, handler):
        """Cleans out connections which never finish a message"""
        if handler.active and handler.time < getUTC() - 60:
            self.server.disconnect(handler)

    def process_data(self, handler):
        """Collects incoming data from nodes"""
        try:
            while not handler.find_terminator():
                if not handler.collect_incoming_data(handler.sock.recv(1024)):
                    self.__print__(
                        "disconnecting node %s while in loop" % handler.id,
                        level=6)
                    self.server.disconnect(handler)
                    self.server.request_peers()
                    return
            while handler.find_terminator():
                handler.found_terminator()
        except socket.timeout:  # pragma: no cover
            return  # Shouldn't happen with select, but if it does...
        except Exception as e:
            if (isinstance(e, socket.error) and
                    e.args[0] in (9, 104, 10053, 10054, 10058)):
                node_id = handler.id
                if not node_id:
                    node_id = repr(handler)
                self.__print__(
                    "Node %s has disconnected from the network" % node_id,
                    level=1)
            else:
                self.__print__(
                    "There was an unhandled exception with peer id %s. This "
                    "peer is being disconnected, and the relevant exception "
                    "is added to the debug queue. If you'd like to report "
                    "this, please post a copy of your mesh_socket.status to "
                    "git.p2p.today/issues." % handler.id,
                    level=0)
                self.exceptions.append(traceback.format_exc())
            self.server.disconnect(handler)
            self.server.request_peers()

    def __del__(self):
        self.alive = False
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except:  # pragma: no cover
            pass

    @inherit_doc(base_connection.__print__)
    def __print__(self, *args, **kargs):
        self.server.__print__(*args, **kargs)


class base_socket(object):
    """The base class for a peer-to-peer socket abstractor"""
    def __init__(self, addr, port, prot=default_protocol, out_addr=None,
                 debug_level=0):
        """Initializes a peer to peer socket

        Args:
            addr:        The address you wish to bind to (ie: "192.168.1.1")
            port:        The port you wish to bind to (ie: 44565)
            prot:        The protocol you wish to operate over, defined by a
                             :py:class:`py2p.base.protocol` object
            out_addr:    Your outward facing address. Only needed if you're
                             connecting over the internet. If you use '0.0.0.0'
                             for the addr argument, this will automatically be
                             set to your LAN address.
            debug_level: The verbosity you want this socket to use when
                             printing event data

        Raises:
            socket.error: The address you wanted could not be bound, or is
            otherwise used
        """
        self.protocol = prot
        self.debug_level = debug_level
        self.routing_table = {}  # In format {ID: handler}
        self.awaiting_ids = []   # Connected, but not handshook yet
        if out_addr:  # Outward facing address, if you're port forwarding
            self.out_addr = out_addr
        elif addr == '0.0.0.0':
            self.out_addr = get_lan_ip(), port
        else:
            self.out_addr = addr, port
        info = (str(self.out_addr).encode(), prot.id, user_salt)
        h = hashlib.sha384(b''.join(info))
        self.id = to_base_58(int(h.hexdigest(), 16))
        self.__handlers = []
        self.__closed = False

    def close(self):
        """If the socket is not closed, close the socket

        Raises:
            RuntimeError:   The socket was already closed
        """
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
            for conn in chain(tuple(self.routing_table.values()), self.awaiting_ids):
                self.disconnect(conn)
            self.__closed = True

    if sys.version_info >= (3, ):
        def register_handler(self, method):
            """Register a handler for incoming method.

            Args:
                method: A function with two given arguments. Its signature
                            should be of the form ``handler(msg, handler)``,
                            where msg is a :py:class:`py2p.base.message`
                            object, and handler is a
                            :py:class:`py2p.base.base_connection` object. It
                            should return ``True`` if it performed an action,
                            to reduce the number of handlers checked.

            Raises:
                ValueError: If the method signature doesn't parse correctly
            """
            args = inspect.signature(method)
            if (len(args.parameters) !=
                    (3 if args.parameters.get('self') else 2)):
                raise ValueError(
                    "This method must contain exactly two arguments "
                    "(or three if first is self)")
            self.__handlers.append(method)

    else:
        def register_handler(self, method):
            """Register a handler for incoming method.

            Args:
                method: A function with two given arguments. Its signature
                            should be of the form ``handler(msg, handler)``,
                            where msg is a :py:class:`py2p.base.message`
                            object, and handler is a
                            :py:class:`py2p.base.base_connection` object. It
                            should return ``True`` if it performed an action,
                            to reduce the number of handlers checked.

            Raises:
                ValueError: If the method signature doesn't parse correctly
            """
            args = inspect.getargspec(method)
            if (args[1:] != (None, None, None) or len(args[0]) !=
                    (3 if args[0][0] == 'self' else 2)):
                raise ValueError(
                    "This method must contain exactly two arguments "
                    "(or three if first is self)")
            self.__handlers.append(method)

    def handle_msg(self, msg, conn):
        """Decides how to handle various message types, allowing some to be
        handled automatically

        Args:
            msg:    A :py:class:`py2p.base.message` object
            conn:   A :py:class:`py2p.base.base_connection` object

        Returns:
            True if an action was taken, None if not.
        """
        for handler in self.__handlers:
            self.__print__("Checking handler: %s" % handler.__name__, level=4)
            if handler(msg, conn):
                self.__print__(
                    "Breaking from handler: %s" % handler.__name__, level=4)
                return True

    @property
    def status(self):
        """The status of the socket.

        Returns:
            ``"Nominal"`` if all is going well, or a list of unexpected
            (Exception, traceback) tuples if not
        """
        return self.daemon.exceptions or "Nominal"

    @property
    def outgoing(self):
        """IDs of outgoing connections"""
        return (handler.id for handler in self.routing_table.values()
                if handler.outgoing)

    @property
    def incoming(self):
        """IDs of incoming connections"""
        return (handler.id for handler in self.routing_table.values()
                if not handler.outgoing)

    def __print__(self, *args, **kargs):
        """Private method to print if level is <= self.debug_level

        Args:
            *args:   Each argument you wish to feed to the print method
            **kargs: One keyword is used here: level, which defines the
                         lowest value of self.debug_level at which the message
                         will be printed
        """
        if kargs.get('level', 0) <= self.debug_level:
            with plock:
                print(self.out_addr[1], *args)

    def __del__(self):
        if not self.__closed:
            self.close()


class message(object):
    """An object which gets returned to a user, containing all necessary
    information to parse and reply to a message
    """
    def __init__(self, msg, server):
        """Initializes a message object

        Args:
            msg:    A :py:class:`py2p.base.InternalMessage` object
            server: A :py:class:`py2p.base.base_socket` object
        """
        self.msg = msg
        self.server = server

    @property
    def time(self):
        """The time this message was sent at"""
        return self.msg.time

    @property
    @inherit_doc(InternalMessage.time_58)
    def time_58(self):
        return self.msg.time_58

    @property
    def sender(self):
        """The ID of this message's sender"""
        return self.msg.sender

    @property
    @inherit_doc(InternalMessage.id)
    def id(self):
        return self.msg.id

    @property
    @inherit_doc(InternalMessage.payload)
    def packets(self):
        return self.msg.payload

    @inherit_doc(InternalMessage.__len__)
    def __len__(self):
        return self.msg.__len__()

    def __repr__(self):
        packets = self.packets
        sender = self.sender
        # This should no longer happen, but just in case
        if isinstance(self.sender, base_connection):
            sender = sender.addr
        return "message(type={}, packets={}, sender={})".format(
            packets[0], packets[1:], sender)

    def reply(self, *args):
        """Replies to the sender if you're directly connected. Tries to make
        a connection otherwise

        Args:
            *args: Each argument given is a packet you wish to send. This is
                       prefixed with base.flags.whisper, so the other end will
                       receive ``[base.flags.whisper, *args]``
        """
        if self.server.routing_table.get(self.sender):
            self.server.routing_table.get(self.sender).send(
                flags.whisper, flags.whisper, *args)
        else:
            request_hash = hashlib.sha384(
                self.sender + to_base_58(getUTC())).hexdigest()
            request_id = to_base_58(int(request_hash, 16))
            self.server.send(request_id, self.sender, type=flags.request)
            self.server.requests[request_id] = (flags.whisper, flags.whisper) + tuple(args)
            print("You aren't connected to the original sender. This reply "
                  "is not guarunteed, but we're trying to make a connection"
                  " and put the message through.")
