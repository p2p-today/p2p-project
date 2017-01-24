import sys

from os import urandom
from random import randint
from uuid import uuid4

from ..types import types

if sys.version_info >= (3, ):
    xrange = range
    unicode = str

def test_uchar():
    serialize = types.uchar.serialize
    deserialize = types.uchar.deserialize
    for i in (randint(0, (2**8) - 1) for _ in xrange(1000)):
        assert deserialize(serialize(i)) == i, i

def test_uint32():
    serialize = types.uint16.serialize
    deserialize = types.uint16.deserialize
    for i in (randint(0, (2**16) - 1) for _ in xrange(1000)):
        assert deserialize(serialize(i)) == i, i

def test_uint32():
    serialize = types.uint32.serialize
    deserialize = types.uint32.deserialize
    for i in (randint(0, (2**32) - 1) for _ in xrange(1000)):
        assert deserialize(serialize(i)) == i, i

def test_uint64():
    serialize = types.uint64.serialize
    deserialize = types.uint64.deserialize
    for i in (randint(0, (2**64) - 1) for _ in xrange(1000)):
        try:
            assert deserialize(serialize(i)) == i, i
        except Exception as e:
            raise Exception(e, i)

def test_char():
    serialize = types.char.serialize
    deserialize = types.char.deserialize
    for i in (randint(-(2**7), 2**7 - 1) for _ in xrange(1000)):
        assert deserialize(serialize(i)) == i, i

def test_int32():
    serialize = types.int16.serialize
    deserialize = types.int16.deserialize
    for i in (randint(-(2**15), 2**15 - 1) for _ in xrange(1000)):
        assert deserialize(serialize(i)) == i, i

def test_int32():
    serialize = types.int32.serialize
    deserialize = types.int32.deserialize
    for i in (randint(-(2**31), 2**31 - 1) for _ in xrange(1000)):
        assert deserialize(serialize(i)) == i, i

def test_int64():
    serialize = types.int64.serialize
    deserialize = types.int64.deserialize
    for i in (randint(-(2**63), 2**63 - 1) for _ in xrange(1000)):
        assert deserialize(serialize(i)) == i, i

def test_bigint():
    serialize = types.bigint.serialize
    deserialize = types.bigint.deserialize
    for i in (randint(-(2**128), 2**128 - 1) for _ in xrange(1000)):
        assert deserialize(serialize(i)) == i, i

def gen_random_items(i):
    for x in xrange(i):
        type_ = types.types[x % len(types.types)]
        if type_ == types.array:
            yield tuple(gen_random_items(randint(0,10)))
        elif type_ == types.buffer:
            yield urandom(randint(0, 16))
        elif type_ == types.string:
            yield unicode(uuid4())
        elif type_ == types.uchar:
            yield randint(0, 2**8 - 1)
        elif type_ == types.uint16:
            yield randint(0, 2**16 - 1)
        elif type_ == types.uint32:
            yield randint(0, 2**32 - 1)
        elif type_ == types.uint64:
            yield randint(0, 2**64 - 1)
        elif type_ == types.char:
            yield randint(-(2**7), 2**7 - 1)
        elif type_ == types.int16:
            yield randint(-(2**15), 2**15 - 1)
        elif type_ == types.int32:
            yield randint(-(2**31), 2**31 - 1)
        elif type_ == types.int64:
            yield randint(-(2**63), 2**63 - 1)
        elif type_ == types.bigint:
            yield randint(-(2**128), 2**128)

def test_SerializableTuple():
    serialize = types.array.serialize
    deserialize = types.array.deserialize
    for i in (randint(0, 1000) for _ in xrange(1000)):
        items = tuple(gen_random_items(i))
        assert tuple(deserialize(serialize(items)).values()) == items, items