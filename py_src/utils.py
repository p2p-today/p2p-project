from __future__ import print_function
from __future__ import with_statement

import base64
import calendar
import os
import pickle
import shutil
import socket
import tempfile
import time


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
        return IP


def getUTC():  # returns int
    """Returns the current unix time in UTC"""
    return calendar.timegm(time.gmtime())


def get_socket(protocol, serverside=False):
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


def most_common(tmp):
    """Returns the most common element in a list"""
    lst = []
    for item in tmp:
        if isinstance(item, awaiting_value):
            lst.append(item.value)
        else:
            lst.append(item)
    return max(set(lst), key=lst.count)


class file_dict(object):
    def __init__(self, start=None):
        self.__dir = tempfile.mkdtemp().encode()
        if start:
            self.update(start)

    def __del__(self):
        shutil.rmtree(self.__dir)

    def __construct_name(self, key):
        dump = pickle.dumps(key)
        name = base64.urlsafe_b64encode(dump)
        path = os.path.join(self.__dir, name)
        return path

    def __deconstruct_name(self, key):
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
        for key in d:
            self.__setitem__(key, d[key])

    def __getitem__(self, key):
        try:
            name = self.__construct_name(key)
            f = open(name, "rb")
            ret = pickle.load(f)
            f.close()
            return ret
        except:
            raise KeyError(key) 

    def get(self, key, ret=None):
        try:
            return self.__getitem__(key)
        except:
            return ret

    def __iter__(self):
        return (self.__deconstruct_name(key) for key in os.listdir(self.__dir))

    def values(self):
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