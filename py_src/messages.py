from hashlib import sha256
from logging import getLogger

from base58 import (b58encode_int, b58decode_int)
from umsgpack import (packb, unpackb, UnsupportedTypeException)
from typing import (Any, Dict, Iterable, List, Sequence, Tuple, Union)

from . import flags
from .utils import (pack_value, unpack_value, intersect, getUTC,
                    sanitize_packet)

_MsgPackable__ = Union[None, float, str, bytes]
_MsgPackable_ = Union[_MsgPackable__, List[_MsgPackable__], Tuple[
    _MsgPackable__, ...], Dict[Union[str, bytes], _MsgPackable__]]
_MsgPackable = Union[_MsgPackable_, List[_MsgPackable_], Tuple[
    _MsgPackable_, ...], Dict[Union[str, bytes], _MsgPackable_]]
MsgPackable = Union[_MsgPackable, List[_MsgPackable], Tuple[_MsgPackable, ...],
                    Dict[Union[str, bytes], _MsgPackable]]


def compress(msg, method):
    # type: (bytes, int) -> bytes
    """Shortcut method for compression

    Args:
        msg:    The message you wish to compress, the type required is
                    defined by the requested method
        method: The compression method you wish to use. Supported
                    (assuming installed):

                    - :py:data:`~py2p.flags.gzip`
                    - :py:data:`~py2p.flags.zlib`
                    - :py:data:`~py2p.flags.bz2`
                    - :py:data:`~py2p.flags.lzma`
                    - :py:data:`~py2p.flags.snappy`

    Returns:
        Defined by the compression method, but typically the bytes of the
        compressed message

    Warning:
        The types fed are dependent on which compression method you use.
        Best to assume most values are :py:class:`bytes` or
        :py:class:`bytearray`

    Raises:
        ValueError: if there is an unknown compression method, or a
            method-specific error
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
    # type: (bytes, int) -> bytes
    """Shortcut method for decompression

    Args:
        msg:    The message you wish to decompress, the type required is
                    defined by the requested method
        method: The decompression method you wish to use. Supported
                    (assuming installed):

                    - :py:data:`~py2p.flags.gzip`
                    - :py:data:`~py2p.flags.zlib`
                    - :py:data:`~py2p.flags.bz2`
                    - :py:data:`~py2p.flags.lzma`
                    - :py:data:`~py2p.flags.snappy`

    Returns:
        Defined by the decompression method, but typically the bytes of the
        compressed message

    Warning:
        The types fed are dependent on which decompression method you use.
        Best to assume most values are :py:class:`bytes` or
        :py:class:`bytearray`

    Raises:
        ValueError: if there is an unknown compression method, or a
            method-specific error
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
    getLogger('py2p.messages').info("Unable to load snappy compression")

try:
    import zlib
    if hasattr(zlib, 'compressobj'):
        decompress(compress(b'test', flags.zlib), flags.zlib)
        decompress(compress(b'test', flags.gzip), flags.gzip)
        compression.extend((flags.zlib, flags.gzip))
except Exception:  # pragma: no cover
    getLogger('py2p.messages').info("Unable to load gzip/zlib compression")

try:
    import bz2
    if hasattr(bz2, 'compress'):
        decompress(compress(b'test', flags.bz2), flags.bz2)
        compression.append(flags.bz2)
except Exception:  # pragma: no cover
    getLogger('py2p.messages').info("Unable to load bz2 compression")

try:
    import lzma
    if hasattr(lzma, 'compress'):
        decompress(compress(b'test', flags.lzma), flags.lzma)
        compression.append(flags.lzma)
except Exception:  # pragma: no cover
    getLogger('py2p.messages').info("Unable to load lzma compression")


class InternalMessage(object):
    """An object used to build and parse protocol-defined message structures"""
    __slots__ = ('__msg_type', '__time', '__sender', '__payload', '__string',
                 '__compression', '__id', 'compression_fail', '__full_string')

    @classmethod
    def __sanitize_string(cls, string, sizeless=False):
        # type: (Any, Union[bytes, bytearray, str], bool) -> bytes
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
        # type: (Any, bytes, Union[None, Iterable[int]]) -> Tuple[bytes, bool]
        """Returns a tuple containing the decompressed :py:class:`bytes` and a
        :py:class:`bool` as to whether decompression failed or not

        Args:
            string:         The possibly-compressed message you wish to parse
            compressions:   A list of the standard compression methods this
                                message may be under (default: ``[]``)

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
    def feed_string(
        cls,  # type: Any
        string,  # type: Union[bytes, bytearray, str]
        sizeless=False,  # type: bool
        compressions=None  # type: Union[None, Iterable[int]]
    ):  # type: (...) -> InternalMessage
        """Constructs a :py:class:`~py2p.messages.InternalMessage` from a string
        or :py:class:`bytes` object.

        Args:
            string:         The string you wish to parse
            sizeless:       A :py:class:`bool` which describes whether this
                                string has its size header (default: it does)
            compressions:   A iterable containing the standardized compression
                                methods this message might be under
                                (default: ``[]``)

        Returns:
            A :py:class:`~py2p.messages.InternalMessage` from the given string

        Raises:
           AttributeError: Fed a non-string, non-:py:class:`bytes` argument
           AssertionError: Initial size header is incorrect
           ValueError:     Unrecognized compression method fed in compressions
           IndexError:     Packet headers are incorrect OR
                               unrecognized compression
        """
        # First section checks size header
        _string = cls.__sanitize_string(string, sizeless)
        # Then we attempt to decompress
        _string, compression_fail = cls.__decompress_string(
            _string, compressions)
        id_ = _string[0:32]
        serialized = _string[32:]
        checksum = sha256(serialized).digest()
        assert id_ == checksum, "Checksum failed: {} != {}".format(
            id_, checksum)
        packets = unpackb(serialized)
        msg = cls(
            packets[0], packets[1], packets[3:], compression=compressions)
        msg.time = packets[2]
        msg.compression_fail = compression_fail
        msg._InternalMessage__id = checksum
        msg._InternalMessage__string = serialized
        # msg.__string = _string
        return msg

    def __init__(
            self,  # type: InternalMessage
            msg_type,  # type: MsgPackable
            sender,  # type: bytes
            payload,  # type: Iterable[MsgPackable]
            compression=None,  # type: Union[None, Iterable[int]]
            timestamp=None  # type: Union[None, int]
    ):  # type: (...) -> None
        """Initializes a :py:class:`~py2p.messages.InternalMessage` instance

        Args:
            msg_type:       A header for the message you wish to send
            sender:         A sender ID the message is using
            payload:        An iterable of objects containing the payload of
                                the message
            compression:    A list of the compression methods this message
                                may use (default: ``[]``)
            timestamp:      The current UTC timestamp (as an :py:class:`int`)
                                (default: result of
                                :py:func:`py2p.utils.getUTC`)

        Raises:
            TypeError:  If you feed an object which cannot be fed to msgpack
        """
        self.__msg_type = msg_type
        self.__sender = sender
        self.__payload = tuple(payload)
        self.__time = timestamp or getUTC()
        self.__id = None  # type: Union[None, bytes]
        self.__string = None  # type: Union[None, bytes]
        self.__full_string = None  # type: Union[None, bytes]
        self.compression_fail = False

        if compression:
            self.__compression = tuple(compression)  # type: Tuple[int, ...]
        else:
            self.__compression = ()

    @property
    def payload(self):
        # type: (InternalMessage) -> Tuple[MsgPackable, ...]
        """Returns a :py:class:`tuple` containing the message payload encoded
        as :py:class:`bytes`
        """
        return self.__payload

    @payload.setter
    def payload(self, value):
        # type: (InternalMessage, Sequence[MsgPackable]) -> None
        """Sets the payload to a new :py:class:`tuple`"""
        self.__clear_cache()
        self.__payload = tuple(value)

    @property
    def compression_used(self):
        # type: (InternalMessage) -> Union[None, int]
        """Returns the compression method this message is using"""
        for method in intersect(compression, self.compression):
            return method
        return None

    def __clear_cache(self):
        # type: (InternalMessage) -> None
        self.__full_string = None
        self.__string = None
        self.__id = None

    @property
    def msg_type(self):
        # type: (InternalMessage) -> MsgPackable
        return self.__msg_type

    @msg_type.setter
    def msg_type(self, val):
        # type: (InternalMessage, MsgPackable) -> None
        self.__clear_cache()
        self.__msg_type = val

    @property
    def sender(self):
        # type: (InternalMessage) -> bytes
        return self.__sender

    @sender.setter
    def sender(self, val):
        # type: (InternalMessage, bytes) -> None
        self.__clear_cache()
        self.__sender = val

    @property
    def compression(self):
        # type: (InternalMessage) -> Tuple[int, ...]
        return self.__compression

    @compression.setter
    def compression(self, val):
        # type: (InternalMessage, Iterable[int]) -> None
        new_comps = intersect(compression, val)
        old_comp = self.compression_used
        if (old_comp, ) != new_comps[0:1]:
            self.__full_string = None
        self.__compression = tuple(val)

    @property
    def time(self):
        # type: (InternalMessage) -> int
        return self.__time

    @time.setter
    def time(self, val):
        # type: (InternalMessage, int) -> None
        self.__clear_cache()
        self.__time = val

    @property
    def time_58(self):
        # type: (InternalMessage) -> bytes
        """Returns this message's timestamp in base_58"""
        return b58encode_int(self.__time)

    @property
    def id(self):
        # type: (InternalMessage) -> bytes
        """Returns the message id"""
        if not self.__id:
            payload_hash = sha256(self.__non_len_string)
            self.__id = payload_hash.digest()
        return self.__id

    @property
    def packets(self):
        # type: (InternalMessage) -> Tuple[MsgPackable, ...]
        """Returns the full :py:class:`tuple` of packets in this message
        encoded as :py:class:`bytes`, excluding the header
        """
        return ((self.__msg_type, self.__sender, self.time) + self.payload)

    @property
    def __non_len_string(self):
        # type: (InternalMessage) -> bytes
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
                        - :py:class:`dict` (if all keys are
                            :py:class:`unicode`)
        """
        if not self.__string:
            try:
                self.__string = packb(self.packets)
            except UnsupportedTypeException as e:
                raise TypeError(*e.args)
        return self.__string

    @property
    def string(self):
        # type: (InternalMessage) -> bytes
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
        # type: (InternalMessage) -> int
        return len(self.string)
