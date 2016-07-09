from __future__ import print_function
import hashlib, json, random, select, socket, struct, sys, traceback
from .base import flags, compression, to_base_58, from_base_58, getUTC, \
                intersect, protocol, get_socket, base_connection, message, \
                base_daemon, base_socket, pathfinding_message, json_compressions

default_protocol = protocol('chord', "Plaintext")  # SSL")
k = 160  # SHA-1 namespace
limit = 2**k
hashes = ['sha1', 'sha224', 'sha256', 'sha384', 'sha512']

if sys.version_info >= (3,):
    xrange = range

def distance(a, b):
    """This is a clockwise ring distance function.
    It depends on a globally defined k, the key size.
    The largest possible node id is 2**k (or limit)."""
    if a == b:
        return 0
    elif a < b:
        return b - a
    else:
        return limit + b - a

def most_common(lst):
    """Returns the most common element in a list"""
    return max(set(lst), key=lst.count)

class chord_connection(base_connection):
    def found_terminator(self):
        pass

    @property
    def id_10(self):
        return from_base_58(self.id)

class chord_daemon(base_daemon): 
    def mainloop(self):
        while self.alive:
            pass

class chord_socket(base_socket):
    def __init__(self, addr, port, prot=default_protocol, out_addr=None, debug_level=0):
        super(chord_socket, self).__init__(addr, port, prot, out_addr, debug_level)
        self.data = {method: {} for method in hashes}
        self.daemon = chord_daemon(addr, port, self)

    @property
    def id_10(self):
        return from_base_58(self.id)

    def dump_data(self, start, end=None):
        i = start
        ret = {method: {} for method in methods}
        for method in self.data:
            for key in self.data[method]:
                if key >= start % limit and (not end or key < end % limit):
                    print(method, key, self.data)
                    ret[method].update({key: self.data[method][key]})
        return ret

    def connect(self, addr, port):
        raise NotImplemented

    def __findFinger__(self, key):
        current=self
        for x in xrange(k):
            if distance(current.id_10, key) > \
               distance(self.finger[x].id_10, key):
                current=self.finger[x]
        return current

    def __lookup(self, method, key):
        raise NotImplemented

    def lookup(self, key):
        if not isinstance(key, bytes):
            key = str(key).encode()
        keys = [int(hashlib.new(algo, key).hexdigest(), 16) % limit for algo in methods]
        vals = [self.__lookup(method, x) for method, x in zip(methods, keys)]  # TODO: see if these work with generators
        common = most_common(vals)
        if common is not None and vals.count(common) > len(methods) // 2:
            return common
        raise KeyError("This key does not have an agreed-upon value", vals)

    def __getitem__(self, key):
        return self.lookup(key)

    def __store(self, method, key, value):
        raise NotImplemented

    def update(self, update_dict):
        for key in update_dict:
            value = update_dict[key]
            if not isinstance(key, bytes):
                key = str(key).encode()
            keys = [int(hashlib.new(algo, key).hexdigest(), 16) % limit for algo in methods]
            for method, x in zip(methods, keys):
                self.__store(method, x, value)

    def __setitem__(self, key, value):
        return self.update({key: value})