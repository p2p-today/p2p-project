from __future__ import absolute_import

import struct

from decimal import Decimal
from fractions import Fraction
from functools import partial
from itertools import chain
from math import (log, ceil)
from sys import version_info

from .base import (pack_value, unpack_value)
from .utils import sanitize_packet

if version_info[0] >= 3:
    unicode = str
    long = int


class SerializableTuple(tuple):
    def __new__(cls, *args):
        types = (determine_type(x) for x in args)
        pairs = ((type_.serialize(x), type_) for x, type_ in zip(args, types))
        return cls.from_zip(pairs)

    def __getitem__(self, idx):
        if isinstance(idx, slice):
            if idx.step not in (1, None):
                raise IndexError("Does not support slicing by step other than 1")
            new_slice = slice(
                idx.start * 2 if idx.start is not None else None,
                idx.stop * 2 if idx.stop is not None else None,
                idx.step)
            return tuple.__new__(type(self), super(SerializableTuple, self).__getitem__(new_slice))
        return super(SerializableTuple, self).__getitem__(idx * 2)

    def __getslice__(self, a=None, b=None, c=None):
        return self.__getitem__(slice(a, b, c))

    def __len__(self):
        return super(SerializableTuple, self).__len__() // 2

    def __iter__(self):
        return (self[x] for x in range(len(self)))

    def __repr__(self):
        return "SerializableTuple{}".format(tuple(self.values()))

    def values(self):
        return (self.get(x) for x in range(len(self)))

    def types(self):
        return (self.getType(x) for x in range(len(self)))

    def get(self, idx):
        return self.getType(idx).deserialize(self[idx])

    def getType(self, idx):
        return super(SerializableTuple, self).__getitem__(idx * 2 + 1)

    def serialize(self, sizeless=False):
        headers = (struct.pack(">L", len(x)) for x in self)
        flags = (type_.flag for type_ in self.types())
        ret = b''.join(chain.from_iterable(zip(headers, flags, self)))
        if not sizeless:
            header = struct.pack(">L", len(ret))
            return b''.join((header, ret))
        return ret

    @classmethod
    def from_zip(cls, args):
        return tuple.__new__(cls, chain.from_iterable(args))

    @classmethod
    def deserialize(cls, string, sizeless=False):
        string = sanitize_packet(string)
        if not sizeless:
            if struct_unpack(">L", string[:4]) != len(string) - 4:
                raise AssertionError(
                    "Real message size {} != expected size {}. "
                    "Buffer given: {}".format(
                        len(string),
                        unpack_value(string[:4]) + 4,
                        string
                    ))
            string = string[4:]
        processed = 0
        packets, pack_types = [], []
        while processed < len(string):
            pack_len = unpack_value(string[processed:processed+4])
            processed += 4
            pack_types.append(types.from_flag(string[processed:processed+1]))
            processed += 1
            end = processed + pack_len
            packets.append(string[processed:end])
            processed = end
        return cls.from_zip(zip(packets, pack_types))

    @classmethod
    def serialize_iterable(cls, iterable, sizeless=False):
        if isinstance(iterable, cls):
            return cls.serialize(iterable, sizeless)
        return cls(*iterable).serialize(sizeless)

class Py2pType(object):
    __slots__ = ('flag', 'serialize', 'deserialize')

    def __init__(self, flag, serializer, deserializer):
        self.flag = flag
        self.serialize = serializer
        self.deserialize = deserializer

def struct_unpack(formatstr, data):
    return struct.unpack(formatstr, data)[0]

def big_int_serialize(i):
    buff = pack_value(int(log(abs(i), 256)) + 1, abs(i))
    if i < 0:
        return b'-' + buff
    return b'+' + buff

def big_int_deserialize(buff):
    val = unpack_value(buff[1:])
    if buff.startswith(b'-'):
        return -val
    return val

class types(object):
    buffer = Py2pType(b'\x30', lambda x: x, lambda x: x)
    string = Py2pType(b'\x31', sanitize_packet, bytes.decode)
    bigint = Py2pType(b'\x32', big_int_serialize, big_int_deserialize)
    uchar  = Py2pType(b'\x33',
                      partial(struct.pack, ">B"),
                      partial(struct_unpack, ">B"))
    char   = Py2pType(b'\x34',
                      partial(struct.pack, ">b"),
                      partial(struct_unpack, ">b"))
    uint16 = Py2pType(b'\x35',
                      partial(struct.pack, ">H"),
                      partial(struct_unpack, ">H"))
    int16  = Py2pType(b'\x36',
                      partial(struct.pack, ">h"),
                      partial(struct_unpack, ">h"))
    uint32 = Py2pType(b'\x37',
                      partial(struct.pack, ">L"),
                      partial(struct_unpack, ">L"))
    int32  = Py2pType(b'\x38',
                      partial(struct.pack, ">l"),
                      partial(struct_unpack, ">l"))
    uint64 = Py2pType(b'\x39',
                      partial(struct.pack, ">Q"),
                      partial(struct_unpack, ">Q"))
    int64  = Py2pType(b'\x3A',
                      partial(struct.pack, ">q"),
                      partial(struct_unpack, ">q"))
    array  = Py2pType(b'\x3B',
                      partial(SerializableTuple.serialize_iterable, sizeless=True),
                      partial(SerializableTuple.deserialize, sizeless=True))

    types = (buffer, string, bigint, char,
                uchar, uint16, int16, uint32,
                int32, uint64, int64, array)


    @classmethod
    def from_flag(cls, flag):
        for type_ in (cls.buffer, cls.string, cls.bigint, cls.char,
                      cls.uchar, cls.uint16, cls.int16, cls.uint32,
                      cls.int32, cls.uint64, cls.int64, cls.array):
            if flag == type_.flag:
                return type_
        return cls.buffer


def _determine_unsigned_subtype(x):
    if x < 256:
        return types.uchar
    elif x < 2**16:
        return types.uint16
    elif x < 2**32:
        return types.uint32
    elif x < 2**64:
        return types.uint64
    else:
        return types.bigint

def _determine_signed_subtype(x):
    if x > -127:
        return types.char
    elif x > -(2**15):
        return types.int16
    elif x > -(2**31):
        return types.int32
    elif x > -(2**63):
        return types.int64
    else:
        return types.bigint


def _determine_int_subtype(x):
    if x >= 0:
        return _determine_unsigned_subtype(x)
    else:
        return _determine_signed_subtype(x)


def determine_type(x):
    if isinstance(x, (int, long)):
        return _determine_int_subtype(x)
    elif isinstance(x, unicode):
        return types.string
    elif isinstance(x, (tuple, list, SerializableTuple)):
        return types.array
    elif isinstance(x, (float, Fraction, Decimal, complex)):
        raise ValueError("{} is an unsupported type: (float, Fraction, "
                         "Decimal, complex)".format(x))
    else:
        return types.buffer