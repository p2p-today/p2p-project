from __future__ import print_function
from __future__ import with_statement
from __future__ import unicode_literals

from calendar import timegm
from logging import getLogger
from socket import (socket, AF_INET, SOCK_DGRAM, SHUT_RDWR)
from time import gmtime

from typing import (cast, Any, Callable, Iterable, Tuple, Union)

from . import flags


def log_entry(name, level):
    # type: (str, int) -> Callable
    def annotation(function):
        # type: (Callable) -> Callable
        log = getLogger(name)

        def caller(*args, **kwargs):
            # type: (*Any, **Any) -> Any
            log.log(level, "Entering function {}".format(name))
            ret = function(*args, **kwargs)
            log.log(level, "Exiting function {}".format(name))
            return ret

        caller.__doc__ = function.__doc__
        caller.__name__ = function.__name__
        return caller

    metalogger = getLogger('py2p.utils.log_entry')
    metalogger.info('Adding log handler to {} at level {}'.format(name, level))
    return annotation


def inherit_doc(function):
    # type: (Callable) -> Callable
    """A decorator which allows you to inherit docstrings from a specified
    function."""
    logger = getLogger('py2p.utils.inherit_doc')
    logger.info('Parsing documentation inheritence for {}'.format(function))
    try:
        from custom_inherit import doc_inherit, google
        return doc_inherit(function, google)
    except:
        logger.info(
            'custom_inherit is not available. Using default documentation')
        return lambda x: x  # If unavailable, just return the function


def sanitize_packet(packet):
    # type: (Union[bytes, bytearray, str]) -> bytes
    """Function to sanitize a packet for InternalMessage serialization,
    or dict keying
    """
    if isinstance(packet, type(u'')):
        return cast(str, packet).encode('utf-8')
    elif isinstance(packet, bytearray):
        return bytes(packet)
    return cast(bytes, packet)


def intersect(*args):
    # type: (*Iterable[Any]) -> Tuple[Any, ...]
    """Finds the intersection of several iterables

    Args:
        *args:  Several iterables

    Returns:
        A :py:class:`tuple` containing the ordered intersection of all given
        iterables, where the order is defined by the first iterable

    Note:
        All items in your iterable must be hashable. In other words, they must
        fit in a :py:class:`set`
    """
    if not all(args):
        return ()
    iterator = iter(args)
    intersection = next(iterator)
    for l in iterator:
        s = set(l)
        intersection = (item for item in intersection if item in s)
    return tuple(intersection)


def get_lan_ip():
    # type: () -> str
    """Retrieves the LAN ip. Expanded from http://stackoverflow.com/a/28950776

    Note: This will return '127.0.0.1' if it is not connected to a network
    """
    s = socket(AF_INET, SOCK_DGRAM)  # type: socket
    try:
        # doesn't even have to be reachable
        s.connect(('8.8.8.8', 23))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.shutdown(SHUT_RDWR)
        return IP


def pack_value(l, i):
    # type: (int, int) -> bytes
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
    # type: (Union[bytes, bytearray, str]) -> int
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


def getUTC():
    # type: () -> int
    """Returns the current unix time in UTC

    Note: This will always return an integral value
    """
    return timegm(cast(Tuple, gmtime()))


def get_socket(protocol, serverside=False):
    # type: (Any, bool) -> Any
    """Given a protocol object, return the appropriate socket

    Args:
        protocol:   A py2p.base.protocol object
        serverside: Whether you are the server end of a connection
                        (default: False)

    Raises:
        ValueError: If your protocol object has an unknown encryption method

    Returns:
        A socket-like object
    """
    if protocol.encryption == "Plaintext":
        return socket()
    elif protocol.encryption == "SSL":
        # This is inline to prevent dependency issues
        from .ssl_wrapper import get_socket as _get_socket
        return _get_socket(serverside)
    else:  # pragma: no cover
        raise ValueError("Unkown encryption method")


class awaiting_value(object):
    """Proxy object for an asynchronously retrieved item"""

    def __init__(self, value=None):
        # type: (awaiting_value, Any) -> None
        self.value = value  # type: Union[None, bool, int, dict, bytes, str, list, tuple]
        self.callback = None  # type: Any

    def callback_method(self, method, key):
        # type: (str, str) -> None
        self.callback.send(flags.whisper, flags.retrieved, method, key,
                           self.value)

    def __repr__(self):
        # type: (awaiting_value) -> str
        return "<" + repr(self.value) + ">"


def most_common(tmp):
    # type: (Iterable[Any]) -> Tuple[Any, int]
    """Returns the most common element in a list

    Args:
        tmp:    A non-string iterable

    Returns:
        The most common element in the iterable

    Warning:
        If there are multiple elements which share the same count, it will
        return a random one.
    """
    lst = []
    for item in tmp:
        if isinstance(item, awaiting_value):
            lst.append(item.value)
        else:
            lst.append(item)
    try:
        ret = max(set(lst), key=lst.count)
    except TypeError:  # in case of unhashable
        ret = max(lst, key=lst.count)
    return ret, lst.count(ret)
