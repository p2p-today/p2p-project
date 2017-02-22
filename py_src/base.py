"""A library to store common functions and protocol definitions"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import with_statement

import inspect
import socket

from hashlib import (sha256, sha384)
from itertools import chain
from logging import (getLogger, INFO, DEBUG)
from sys import version_info
from threading import (Lock, Thread, current_thread)
from traceback import format_exc
from uuid import uuid4

from umsgpack import (packb, unpackb, UnsupportedTypeException)
from pyee import EventEmitter
from typing import (cast, Any, Callable, Dict, Iterable, List, NamedTuple,
                    Sequence, Tuple, Union)

from .utils import (getUTC, intersect, get_lan_ip, get_socket, sanitize_packet,
                    inherit_doc, log_entry)

_MsgPackable__ = Union[None, int, float, str, bytes]
_MsgPackable_ = Union[_MsgPackable__, List[_MsgPackable__], Tuple[
    _MsgPackable__, ...], Dict[str, _MsgPackable__]]
_MsgPackable = Union[_MsgPackable_, List[_MsgPackable_], Tuple[
    _MsgPackable_, ...], Dict[str, _MsgPackable_]]
MsgPackable = Union[_MsgPackable, List[_MsgPackable], Tuple[_MsgPackable, ...],
                    Dict[str, _MsgPackable]]

protocol_version = "0.6"
node_policy_version = "757"

version = '.'.join((protocol_version, node_policy_version))

plock = Lock()


class flags():
    """A namespace to hold protocol-defined flags"""
    # Reserved set of bytes
    reserved = tuple(range(0x30))

    # main flags
    broadcast = 0x00  # also sub-flag
    renegotiate = 0x01
    whisper = 0x02  # also sub-flag
    ping = 0x03  # Unused, but reserved
    pong = 0x04  # Unused, but reserved

    # sub-flags
    # broadcast = 0x00
    compression = 0x01
    # whisper = 0x02
    # ping = 0x03
    # pong = 0x04
    handshake = 0x05
    notify = 0x06
    peers = 0x07
    request = 0x08
    resend = 0x09
    response = 0x0A
    store = 0x0B
    retrieve = 0x0C
    retrieved = 0x0D

    # implemented compression methods
    bz2 = 0x10
    gzip = 0x11
    lzma = 0x12
    zlib = 0x13
    snappy = 0x20

    # non-implemented compression methods (based on list from compressjs):
    bwtc = 0x14
    context1 = 0x15
    defsum = 0x16
    dmc = 0x17
    fenwick = 0x18
    huffman = 0x19
    lzjb = 0x1A
    lzjbr = 0x1B
    lzp3 = 0x1C
    mtf = 0x1D
    ppmd = 0x1E
    simple = 0x1F


user_salt = str(uuid4()).encode()


def compress(msg, method):
    #type: (bytes, int) -> bytes
    """Shortcut method for compression

    Args:
        msg:    The message you wish to compress, the type required is
                    defined by the requested method
        method: The compression method you wish to use. Supported
                    (assuming installed):

                    - :py:class:`~base.flags.gzip`
                    - :py:class:`~base.flags.zlib`
                    - :py:class:`~base.flags.bz2`
                    - :py:class:`~base.flags.lzma`

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
        compressor = zlib.compressobj(zlib.Z_DEFAULT_COMPRESSION,
                                      zlib.DEFLATED, wbits)
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
    #type: (bytes, int) -> bytes
    """Shortcut method for decompression

    Args:
        msg:    The message you wish to decompress, the type required is
                    defined by the requested method
        method: The decompression method you wish to use. Supported
                    (assuming installed):

                    - :py:class:`~base.flags.gzip`
                    - :py:class:`~base.flags.zlib`
                    - :py:class:`~base.flags.bz2`
                    - :py:class:`~base.flags.lzma`

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


# This should be in order of preference, with None being implied as last
compression = []

# Compression testing section

try:
    import snappy
    if hasattr(snappy, 'compress'):
        decompress(compress(b'test', flags.snappy), flags.snappy)
        compression.append(flags.snappy)
except Exception:  # pragma: no cover
    getLogger('py2p.base').info("Unable to load snappy compression")

try:
    import zlib
    if hasattr(zlib, 'compressobj'):
        decompress(compress(b'test', flags.zlib), flags.zlib)
        decompress(compress(b'test', flags.gzip), flags.gzip)
        compression.extend((flags.zlib, flags.gzip))
except Exception:  # pragma: no cover
    getLogger('py2p.base').info("Unable to load gzip/zlib compression")

try:
    import bz2
    if hasattr(bz2, 'compress'):
        decompress(compress(b'test', flags.bz2), flags.bz2)
        compression.append(flags.bz2)
except Exception:  # pragma: no cover
    getLogger('py2p.base').info("Unable to load bz2 compression")

try:
    import lzma
    if hasattr(lzma, 'compress'):
        decompress(compress(b'test', flags.lzma), flags.lzma)
        compression.append(flags.lzma)
except Exception:  # pragma: no cover
    getLogger('py2p.base').info("Unable to load lzma compression")


def pack_value(l, i):
    #type: (int, int) -> bytes
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
    ret = bytearray(l)
    for x in range(l - 1, -1, -1):  # Iterate over length backwards
        ret[x] = i & 0xFF
        i >>= 8
        if i == 0:
            break
    if i:
        raise ValueError("Value not allocatable in size given")
    return bytes(ret)


def unpack_value(string):
    #type: (Union[bytes, bytearray, str]) -> int
    """For a string, return the packed value inside of it

    Args:
        string: A string or bytes-like object

    Returns:
        An integral value interpreted from this, as if it were a
        big-endian, unsigned integral
    """
    val = 0
    for char in bytearray(sanitize_packet(string)):
        val = val << 8
        val += char
    return val


base_58 = b'123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


def to_base_58(i):
    #type: (int) -> bytes
    """Takes an integer and returns its corresponding base_58 string

    Args:
        i: The integral value you wish to encode

    Returns:
        A :py:class:`bytes` object which contains the base_58 string

    Raises:
        TypeError: If you feed a non-integral value
    """
    string = b""
    while i:
        idx = i % 58
        string = base_58[idx:idx + 1] + string
        i //= 58
    if not string:
        string = base_58[0:1]
    return string


def from_base_58(string):
    #type: (Union[bytes, bytearray, str]) -> int
    """Takes a base_58 string and returns its corresponding integer

    Args:
        string: The base_58 value you wish to decode (string, bytes,
                    or bytearray)

    Returns:
        Returns integral value which corresponds to the fed string
    """
    decimal = 0
    for char in sanitize_packet(string):
        decimal = decimal * 58 + base_58.index(cast(bytes, char))
    return decimal


class Protocol(
        NamedTuple("_Protocol", [('subnet', str), ('encryption', str)])):
    """Defines service variables so that you can reject connections looking
    for a different service

    Attributes:
        subnet:     The subnet flag this Protocol uses
        encryption: The encryption method this Protocol uses
        id:         The SHA-256 based ID of this Protocol
    """
    __slots__ = ()

    @property
    def id(self):
        #type: (Protocol) -> str
        """The SHA-256-based ID of the Protocol"""
        h = sha256(''.join(str(x) for x in self).encode())
        h.update(protocol_version.encode())
        return to_base_58(int(h.hexdigest(), 16)).decode()


default_protocol = Protocol('', "Plaintext")  # SSL")


class InternalMessage(object):
    """An object used to build and parse protocol-defined message structures"""
    __slots__ = ('__msg_type', '__time', '__sender', '__payload', '__string',
                 '__compression', '__id', 'compression_fail', '__full_string')

    @classmethod
    def __sanitize_string(cls, string, sizeless=False):
        #type: (Any, Union[bytes, bytearray, str], bool) -> bytes
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
        _string = sanitize_packet(string)
        if not sizeless:
            if unpack_value(_string[:4]) != len(_string[4:]):
                raise AssertionError(
                    "Real message size {} != expected size {}. "
                    "Buffer given: {}".format(
                        len(_string), unpack_value(_string[:4]) + 4, _string))
            _string = _string[4:]
        return _string

    @classmethod
    def __decompress_string(cls, string, compressions=None):
        #type: (Any, bytes, Union[None, Iterable[int]]) -> Tuple[bytes, bool]
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
    def feed_string(cls, string, sizeless=False, compressions=None):
        #type: (Any, Union[bytes, bytearray, str], bool, Union[None, Iterable[int]]) -> InternalMessage
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
        _string = cls.__sanitize_string(string, sizeless)
        # Then we attempt to decompress
        _string, compression_fail = cls.__decompress_string(_string,
                                                            compressions)
        id_ = _string[0:32]
        serialized = _string[32:]
        checksum = sha256(serialized).digest()
        assert id_ == checksum, "Checksum failed: {} != {}".format(id_,
                                                                   checksum)
        packets = unpackb(serialized)
        msg = cls(packets[0],
                  packets[1],
                  packets[3:],
                  compression=compressions)
        msg.time = packets[2]
        msg.compression_fail = compression_fail
        msg._InternalMessage__id = checksum
        msg._InternalMessage__string = serialized
        # msg.__string = _string
        return msg

    def __init__(
            self,  #type: InternalMessage
            msg_type,  #type: MsgPackable
            sender,  #type: bytes
            payload,  #type: Iterable[MsgPackable, ...]
            compression=None,  #type: Union[None, Iterable[int, ...]]
            timestamp=None  #type: Union[None, int]
    ):  #type: (...) -> None
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
        self.__msg_type = msg_type
        self.__sender = sender
        self.__payload = tuple(payload)
        self.__time = timestamp or getUTC()
        self.__id = None  #type: Union[None, bytes]
        self.__string = None  #type: Union[None, bytes]
        self.__full_string = None  #type: Union[None, bytes]
        self.compression_fail = False

        if compression:
            self.__compression = tuple(compression)  #type: Tuple[int, ...]
        else:
            self.__compression = ()

    @property
    def payload(self):
        #type: (InternalMessage) -> Tuple[MsgPackable, ...]
        """Returns a :py:class:`tuple` containing the message payload encoded
        as :py:class:`bytes`
        """
        return self.__payload

    @property
    def compression_used(self):
        #type: (InternalMessage) -> Union[None, int]
        """Returns the compression method this message is using"""
        for method in intersect(compression, self.compression):
            return method
        return None

    def __clear_cache(self):
        #type: (InternalMessage) -> None
        self.__full_string = None
        self.__string = None
        self.__id = None

    @property
    def msg_type(self):
        #type: (InternalMessage) -> MsgPackable
        return self.__msg_type

    @msg_type.setter
    def msg_type(self, val):
        #type: (InternalMessage, MsgPackable) -> None
        self.__clear_cache()
        self.__msg_type = val

    @property
    def sender(self):
        #type: (InternalMessage) -> bytes
        return self.__sender

    @sender.setter
    def sender(self, val):
        #type: (InternalMessage, bytes) -> None
        self.__clear_cache()
        self.__sender = val

    @property
    def compression(self):
        #type: (InternalMessage) -> Tuple[int, ...]
        return self.__compression

    @compression.setter
    def compression(self, val):
        #type: (InternalMessage, Iterable[int]) -> None
        new_comps = intersect(compression, val)
        old_comp = self.compression_used
        if (old_comp, ) != new_comps[0:1]:
            self.__full_string = None
        self.__compression = tuple(val)

    @property
    def time(self):
        #type: (InternalMessage) -> int
        return self.__time

    @time.setter
    def time(self, val):
        #type: (InternalMessage, int) -> None
        self.__clear_cache()
        self.__time = val

    @property
    def time_58(self):
        #type: (InternalMessage) -> bytes
        """Returns this message's timestamp in base_58"""
        return to_base_58(self.__time)

    @property
    def id(self):
        #type: (InternalMessage) -> bytes
        """Returns the message id"""
        if not self.__id:
            payload_hash = sha256(self.__non_len_string)
            self.__id = payload_hash.digest()
        return self.__id

    @property
    def packets(self):
        #type: (InternalMessage) -> Tuple[MsgPackable, ...]
        """Returns the full :py:class:`tuple` of packets in this message
        encoded as :py:class:`bytes`, excluding the header
        """
        return ((self.__msg_type, self.__sender, self.time) + self.payload)

    @property
    def __non_len_string(self):
        #type: (InternalMessage) -> bytes
        """Returns a :py:class:`bytes` object containing the entire message,
        excepting the total length header

        Raises:

            TypeError: If any of the arguments are not serializable. This
                        means your objects must be one of the following:

                        - :py:class:`bool`
                        - :py:class:`float`
                        - :py:class:`int` (if ``2**64 > x > -2**63``)
                        - :py:class:`str`
                        - :py:class:`bytes`
                        - :py:class:`unicode`
                        - :py:class:`tuple`
                        - :py:class:`list`
                        - :py:class:`dict` (if all keys are :py:class:`unicode`)
        """
        if not self.__string:
            try:
                self.__string = packb(self.packets)
            except UnsupportedTypeException as e:
                raise TypeError(*e.args)
        return self.__string

    @property
    def string(self):
        #type: (InternalMessage) -> bytes
        """Returns a :py:class:`bytes` representation of the message

        Raises:
            TypeError: See :py:func:`~py2p.base.InternalMessage._InternalMessage__non_len_string`
        """
        if not all((self.__id, self.__string, self.__full_string)):
            id_ = self.id
            ret = b''.join((id_, self.__non_len_string))
            compression_used = self.compression_used
            if compression_used:
                ret = compress(ret, compression_used)
            self.__full_string = b''.join((pack_value(4, len(ret)), ret))
        return self.__full_string

    def __len__(self):
        #type: (InternalMessage) -> int
        return len(self.string)


class BaseConnection(object):
    """The base class for a connection"""
    __slots__ = ('sock', 'server', 'outgoing', 'buffer', 'id', 'time', 'addr',
                 'compression', 'last_sent', 'expected', 'active')

    @log_entry('py2p.base.BaseConnection.__init__', DEBUG)
    def __init__(self, sock, server, outgoing=False):
        #type: (BaseConnection, Any, BaseSocket, bool) -> None
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
        self.id = None  #type: Union[None, bytes]
        self.time = getUTC()
        self.addr = None  #type: Union[None, Tuple[str, int]]
        self.compression = []  #type: List[int]
        self.last_sent = ()  #type: Tuple[MsgPackable, ...]
        self.expected = 4
        self.active = False

    def send_InternalMessage(self, msg):
        #type: (BaseConnection, InternalMessage) -> InternalMessage
        """Sends a preconstructed message

        Args:
            msg: The :py:class:`~py2p.base.IntenalMessage` you wish to send

        Returns:
            the :py:class:`~py2p.base.IntenalMessage` object you just sent, or
            ``None`` if the sending was unsuccessful
        """
        msg.compression = self.compression  #type: ignore
        if msg.msg_type in (flags.whisper, flags.broadcast):
            self.last_sent = msg.payload
        self.__print__("Sending %s to %s" % (msg.packets, self), level=4)
        if msg.compression_used:
            self.__print__(
                "Compressing with %s" % repr(msg.compression_used), level=4)
        try:
            self.sock.send(msg.string)
            return msg
        except (IOError, socket.error) as e:  # pragma: no cover
            self.server.daemon.exceptions.append(format_exc())
            self.server.disconnect(self)

    def send(self, msg_type, *args, **kargs):
        #type: (BaseConnection, MsgPackable, *MsgPackable, **Union[bytes, int]) -> InternalMessage
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
        #type: (BaseConnection) -> Protocol
        """Returns server.protocol"""
        return self.server.protocol

    def collect_incoming_data(self, data):
        #type: (BaseConnection, Union[bytes, bytearray]) -> bool
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
        #type: (BaseConnection) -> bool
        """Returns whether the defined return sequences is found"""
        return len(self.buffer) >= self.expected

    def found_terminator(self):
        #type: (BaseConnection) -> InternalMessage
        """Processes received messages"""
        raw_msg, self.buffer = bytes(self.buffer[:self.expected]), \
                               self.buffer[self.expected:]
        self.__print__("Received: %s" % repr(raw_msg), level=6)
        self.active = len(self.buffer) > 4
        if self.active:
            self.expected = unpack_value(bytes(self.buffer[:4])) + 4
        else:
            self.expected = 4
        msg = InternalMessage.feed_string(raw_msg, False, self.compression)
        return msg

    def handle_renegotiate(self, packets):
        #type: (BaseConnection, Sequence[MsgPackable]) -> bool
        """The handler for connection renegotiations

        This is to deal with connection maintenance. For instance, it could
        be that a compression method fails to decode on the other end, and a
        node will need to renegotiate which methods it is using. Hence the
        name of the flag associated with it, "renegotiate".

        Args:
            packets:    A :py:class:`tuple` containing the packets received
                            in this message

        Returns:
            ``True`` if an action was taken, ``False`` if not
        """
        if packets[0] == flags.renegotiate:
            if packets[4] == flags.compression:
                encoded_methods = packets[5]
                respond = (self.compression != encoded_methods)
                self.compression = list(cast(Iterable[int], encoded_methods))
                self.__print__(
                    "Compression methods changed to: %s" %
                    repr(self.compression),
                    level=2)
                if respond:
                    self.send(flags.renegotiate, flags.compression,
                              cast(Tuple[int, ...],
                                   intersect(compression, self.compression)))
                return True
            elif packets[4] == flags.resend:
                self.send(*self.last_sent)
                return True
        return False

    def fileno(self):
        #type: (BaseConnection) -> int
        """Mirror for the fileno() method of the connection's
        underlying socket
        """
        return self.sock.fileno()

    def __print__(self, *args, **kargs):
        #type: (BaseConnection, *Any, **int) -> None
        """Private method to print if level is <= self.server.debug_level

        Args:
            *args:   Each argument you wish to feed to the print method
            **kargs: One keyword is used here: level, which defines the
                         lowest value of self.server.debug_level at which
                         the message will be printed
        """
        self.server.__print__(*args, **kargs)


class BaseDaemon(object):
    """The base class for a daemon"""
    __slots__ = ('server', 'sock', 'exceptions', 'alive', '_logger',
                 'main_thread', 'daemon', 'conn_type')

    @log_entry('py2p.base.BaseDaemon.__init__', DEBUG)
    def __init__(self, addr, port, server):
        #type: (Any, str, int, BaseSocket) -> None
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
        self.exceptions = []  #type: List[str]
        self.alive = True
        self._logger = getLogger(
            '{}.{}.{}'.format(self.__class__.__module__,
                              self.__class__.__name__, self.server.id))
        self.main_thread = current_thread()
        self.daemon = Thread(target=self.mainloop)
        self.daemon.start()

    @property
    def protocol(self):
        #type: (BaseDaemon) -> Protocol
        """Returns server.protocol"""
        return self.server.protocol

    def kill_old_nodes(self, handler):
        #type: (BaseDaemon, BaseConnection) -> None
        """Cleans out connections which never finish a message"""
        if handler.active and handler.time < getUTC() - 60:
            self.server.disconnect(handler)

    def process_data(self, handler):
        #type: (BaseDaemon, BaseConnection) -> None
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
                node_id = repr(handler.id or handler)
                self.__print__(
                    "Node %s has disconnected from the network" % node_id,
                    level=1)
            else:
                self.__print__(
                    "There was an unhandled exception with peer id %s. This "
                    "peer is being disconnected, and the relevant exception "
                    "is added to the debug queue. If you'd like to report "
                    "this, please post a copy of your MeshSocket.status to "
                    "git.p2p.today/issues." % handler.id,
                    level=0)
                self.exceptions.append(format_exc())
            self.server.disconnect(handler)
            self.server.request_peers()

    def __del__(self):
        #type: (BaseDaemon) -> None
        self.alive = False
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except:  # pragma: no cover
            pass

    @inherit_doc(BaseConnection.__print__)
    def __print__(self, *args, **kargs):
        #type: (BaseDaemon, *Any, **int) -> None
        self.server.__print__(*args, **kargs)


class BaseSocket(EventEmitter, object):
    """
    The base class for a peer-to-peer socket abstractor

    .. inheritance-diagram:: py2p.base.BaseSocket
    """
    __slots__ = ('protocol', 'debug_level', 'routing_table', 'awaiting_ids',
                 'out_addr', 'id', '_logger', '__handlers', '__closed')

    @log_entry('py2p.base.BaseSocket.__init__', DEBUG)
    def __init__(
            self,  #type: Any
            addr,  #type: str
            port,  #type: int
            prot=default_protocol,  #type: Protocol
            out_addr=None,  #type: Union[None, Tuple[str, int]]
            debug_level=0  #type: int
    ):  #type: (...) -> None
        """Initializes a peer to peer socket

        Args:
            addr:        The address you wish to bind to (ie: "192.168.1.1")
            port:        The port you wish to bind to (ie: 44565)
            prot:        The protocol you wish to operate over, defined by a
                             :py:class:`py2p.base.Protocol` object
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
        object.__init__(self)
        EventEmitter.__init__(self)
        self.protocol = prot
        self.debug_level = debug_level
        self.routing_table = {}  #type: Dict[bytes, BaseConnection]
        # In format {ID: handler}
        self.awaiting_ids = []  #type: List[BaseConnection]
        # Connected, but not handshook yet
        if out_addr:  # Outward facing address, if you're port forwarding
            self.out_addr = out_addr
        elif addr == '0.0.0.0':
            self.out_addr = get_lan_ip(), port
        else:
            self.out_addr = addr, port
        info = (str(self.out_addr).encode(), prot.id.encode(), user_salt)
        h = sha384(b''.join(info))
        self.id = to_base_58(int(h.hexdigest(), 16))  #type: bytes
        self._logger = getLogger('{}.{}.{}'.format(
            self.__class__.__module__, self.__class__.__name__, self.id))
        self.__handlers = [
        ]  #type: List[Callable[[Message, BaseConnection], Union[bool, None]]]
        self.__closed = False

    def close(self):
        #type: (BaseSocket) -> None
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
            for conn in chain(
                    tuple(self.routing_table.values()), self.awaiting_ids):
                self.disconnect(conn)
            self.__closed = True

    if version_info >= (3, ):

        def register_handler(self, method):
            #type: (BaseSocket, Callable[[Message, BaseConnection], Union[bool, None]]) -> None
            """Register a handler for incoming method.

            Args:
                method: A function with two given arguments. Its signature
                            should be of the form ``handler(msg, handler)``,
                            where msg is a :py:class:`py2p.base.Message`
                            object, and handler is a
                            :py:class:`py2p.base.BaseConnection` object. It
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
            #type: (BaseSocket, Callable[[Message, BaseConnection], Union[bool, None]]) -> None
            """Register a handler for incoming method.

            Args:
                method: A function with two given arguments. Its signature
                            should be of the form ``handler(msg, handler)``,
                            where msg is a :py:class:`py2p.base.Message`
                            object, and handler is a
                            :py:class:`py2p.base.BaseConnection` object. It
                            should return ``True`` if it performed an action,
                            to reduce the number of handlers checked.

            Raises:
                ValueError: If the method signature doesn't parse correctly
            """
            args = inspect.getargspec(method)
            if (args[1:] != (None, None, None) or
                    len(args[0]) != (3 if args[0][0] == 'self' else 2)):
                raise ValueError(
                    "This method must contain exactly two arguments "
                    "(or three if first is self)")
            self.__handlers.append(method)

    def handle_msg(self, msg, conn):
        #type: (BaseSocket, Message, BaseConnection) -> Union[bool, None]
        """Decides how to handle various message types, allowing some to be
        handled automatically

        Args:
            msg:    A :py:class:`py2p.base.Message` object
            conn:   A :py:class:`py2p.base.BaseConnection` object

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
        #type: (BaseSocket) -> Union[str, List[str]]
        """The status of the socket.

        Returns:
            ``"Nominal"`` if all is going well, or a list of unexpected
            (Exception, traceback) tuples if not
        """
        return self.daemon.exceptions or "Nominal"

    @property
    def outgoing(self):
        #type: (BaseSocket) -> Iterable[bytes]
        """IDs of outgoing connections"""
        return (handler.id for handler in self.routing_table.values()
                if handler.outgoing)

    @property
    def incoming(self):
        #type: (BaseSocket) -> Iterable[bytes]
        """IDs of incoming connections"""
        return (handler.id for handler in self.routing_table.values()
                if not handler.outgoing)

    def __print__(self, *args, **kargs):
        #type: (BaseSocket, *Any, **int) -> None
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
        #type: (BaseSocket) -> None
        if not self.__closed:
            self.close()


class Message(object):
    """An object which gets returned to a user, containing all necessary
    information to parse and reply to a message
    """
    __slots__ = ('msg', 'server')

    def __init__(self, msg, server):
        #type: (Message, InternalMessage, BaseSocket) -> None
        """Initializes a Message object

        Args:
            msg:    A :py:class:`py2p.base.InternalMessage` object
            server: A :py:class:`py2p.base.BaseSocket` object
        """
        self.msg = msg
        self.server = server

    @property
    def time(self):
        #type: (Message) -> int
        """The time this Message was sent at"""
        return self.msg.time

    @property  #type: ignore
    @inherit_doc(InternalMessage.time_58)
    def time_58(self):
        #type: (Message) -> bytes
        return self.msg.time_58

    @property
    def sender(self):
        #type: (Message) -> bytes
        """The ID of this Message's sender"""
        return self.msg.sender

    @property  #type: ignore
    @inherit_doc(InternalMessage.id)
    def id(self):
        #type: (Message) -> bytes
        return self.msg.id

    @property  #type: ignore
    @inherit_doc(InternalMessage.payload)
    def packets(self):
        #type: (Message) -> Tuple[MsgPackable, ...]
        return self.msg.payload

    @inherit_doc(InternalMessage.__len__)
    def __len__(self):
        #type: (Message) -> int
        return self.msg.__len__()

    def __repr__(self):
        #type: (Message) -> str
        packets = self.packets
        return "Message(type={}, packets={}, sender={})".format(
            packets[0], packets[1:], self.sender)

    def reply(self, *args):
        #type: (Message, *MsgPackable) -> None
        """Replies to the sender if you're directly connected. Tries to make
        a connection otherwise

        Args:
            *args: Each argument given is a packet you wish to send. This is
                       prefixed with base.flags.whisper, so the other end will
                       receive ``[base.flags.whisper, *args]``
        """
        self.server._logger.debug(
            'Initiating a direct reply to Message ID {}'.format(self.id))
        if self.server.routing_table.get(self.sender):
            self.server.routing_table.get(self.sender).send(
                flags.whisper, flags.whisper, *args)
        else:
            self.server._logger.debug('Requesting connection for direct reply'
                                      ' to Message ID {}'.format(self.id))
            request_hash = sha384(self.sender + to_base_58(
                getUTC())).hexdigest()
            request_id = to_base_58(int(request_hash, 16))
            self.server.send(request_id, self.sender, type=flags.request)
            to_send = (flags.whisper, flags.whisper
                       )  #type: Tuple[MsgPackable, ...]
            self.server.requests[request_id] = to_send + args
            self.server._logger.critical(
                "You aren't connected to the original sender. This reply is "
                "not guarunteed, but we're trying to make a connection and "
                "put the message through.")
