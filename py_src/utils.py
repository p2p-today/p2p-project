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

def intersect(*args):  # returns list
    """Finds the intersection of several iterables

    Args:
        *args:  Several iterables

    Returns:
        A list containing the ordered intersection of all given iterables,
        where the order is defined by the first iterable
    """
    if not all(args):
        return []
    intersection = args[0]
    for l in args[1:]:
        intersection = [item for item in intersection if item in l]
    return intersection


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
        serverside: Whether you are the server end of a connection (default: False)

    Raises:
        ValueError: If your protocol object has an unknown encryption method

    Returns:
        A socket-like object
    """
    if protocol.encryption == "Plaintext":
        return socket.socket()
    elif protocol.encryption == "SSL":
        from . import ssl_wrapper  # This is inline to prevent dependency issues
        return ssl_wrapper.get_socket(serverside)
    else:  # pragma: no cover
        raise ValueError("Unkown encryption method")


class awaiting_value(object):
    """Proxy object for an asynchronously retrieved item"""
    def __init__(self, value=-1):
        self.value = value
        self.callback = False

    def callback_method(self, method, key):
        self.callback.send(flags.whisper, flags.response, method, key, self.value)

    def __repr__(self):
        return repr(self.value)


def most_common(tmp):
    """Returns the most common element in a list

    Args:
        tmp:    A non-string iterable

    Returns:
        The most common element in the iterable

    Warning:
        If there are multiple elements which share the same count, it will return a random one.
    """
    lst = []
    for item in tmp:
        if isinstance(item, awaiting_value):
            lst.append(item.value)
        else:
            lst.append(item)
    return max(set(lst), key=lst.count)


class file_dict(object):
    """A dictionary-like object which stores objects on the disk rather than in memory"""
    def __init__(self, start=None):
        """Initializes a file_dict object

        Args:
            start:  A dictionary instance to copy the contents of (default: {})
        """
        self.__dir = tempfile.mkdtemp(suffix='.py2p').encode()
        if start:
            self.update(start)

    def __del__(self):
        shutil.rmtree(self.__dir)

    def __construct_name(self, key):
        """Constructs a filename for a given object

        Args:
            key:    The key you wish to translate to a filename
        """
        dump = pickle.dumps(key)
        name = base64.urlsafe_b64encode(dump)
        path = os.path.join(self.__dir, name)
        return path

    def __deconstruct_name(self, key):
        """Constructs an object from a given name

        Args:
            key:    The key you wish to translate to an object
        """
        _, name = os.path.split(key)
        decoded = base64.urlsafe_b64decode(name)
        load = pickle.loads(decoded)
        return load

    def __setitem__(self, key, value):
        name = self.__construct_name(key)
        f = open(name, "wb")
        pickle.dump(value, f)
        f.close()

    def update(self, d):
        """Updates the file_dict to contain the contents given

        Args:
            d:  A dictionary to get values from
        """
        for key in d:
            self.__setitem__(key, d[key])

    def __getitem__(self, key):
        try:
            name = self.__construct_name(key)
            f = open(name, "rb")
            ret = pickle.load(f)
            f.close()
            return ret
        except:  # pragma: no cover
            raise KeyError(key)

    def get(self, key, ret=None):
        """Gets an item, given a key, without raising a KeyError

        Args:
            key:    The key you're asking for
            ret:    The value it should return if the key is not found (default: None)
        """
        try:
            return self.__getitem__(key)
        except:
            return ret

    def __iter__(self):
        """Returns a generator containing the keys in the file_dict

        Warning:
            May raise errors if items are removed while parsing
        """
        return (self.__deconstruct_name(key) for key in os.listdir(self.__dir))

    def values(self):
        """Returns a generator containing the values in the file_dict

        Warning:
            May raise errors if items are removed while parsing
        """
        return (self.__getitem__(key) for key in self.__iter__())

    def __repr__(self):
        counter = 0
        keys = min(10, len(os.listdir(self.__dir)))
        string = "{"
        for key in self.__iter__():
            counter += 1
            string += "%s: %s, " % (repr(key), repr(self.__getitem__(key)))
            if counter == keys:
                if len(os.listdir(self.__dir)) > counter:
                    return string + "...}"
                break
        if counter == 0:
            return "{}"
        return string[:-2] + "}"