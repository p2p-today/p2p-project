from __future__ import print_function
from __future__ import with_statement

import base64
import calendar
import os
import shutil
import socket
import tempfile
import time

try:
    import cPickle as pickle
except ImportError:
    import pickle


def _doc_merger(parent, child):
    if child:
        return child
    return parent


def inherit_doc(function):
    """A decorator which allows you to inherit docstrings from a specified
    function."""
    try:
        from custom_inherit import doc_inherit
        return doc_inherit(function, _doc_merger)
    except:
        return lambda x: x  # If unavailable, just return the function


def sanitize_packet(packet):
    """Function to sanitize a packet for pathfinding_message serialization,
    or dict keying
    """
    if isinstance(packet, type(u'')):
        return packet.encode('utf-8')
    elif not isinstance(packet, (bytes, bytearray)):
        return packet.encode('raw_unicode_escape')
    return packet


def intersect(*args):
    """Finds the intersection of several iterables

    Args:
        *args:  Several iterables

    Returns:
        A :py:class:`tuple` containing the ordered intersection of all given
        iterables, where the order is defined by the first iterable
    """
    if not all(args):
        return ()
    intersection = args[0]
    for l in args[1:]:
        intersection = (item for item in intersection if item in l)
    return tuple(intersection)


def get_lan_ip():
    """Retrieves the LAN ip. Expanded from http://stackoverflow.com/a/28950776

    Note: This will return '127.0.0.1' if it is not connected to a network
    """
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
        return IP


def getUTC():
    """Returns the current unix time in UTC

    Note: This will always return an integral value
    """
    return calendar.timegm(time.gmtime())


def get_socket(protocol, serverside=False):
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
        return socket.socket()
    elif protocol.encryption == "SSL":
        # This is inline to prevent dependency issues
        from . import ssl_wrapper
        return ssl_wrapper.get_socket(serverside)
    else:  # pragma: no cover
        raise ValueError("Unkown encryption method")


class awaiting_value(object):
    """Proxy object for an asynchronously retrieved item"""
    def __init__(self, value=-1):
        self.value = value
        self.callback = False

    def callback_method(self, method, key):
        from .base import flags
        self.callback.send(
            flags.whisper, flags.retrieved, method, key, self.value)

    def __repr__(self):
        return "<" + repr(self.value) + ">"


def most_common(tmp):
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
    ret = max(set(lst), key=lst.count)
    if lst.count(ret) == lst.count(-1):
        return -1, lst.count(ret)
    return ret, lst.count(ret)
