from __future__ import print_function
from __future__ import absolute_import

import hashlib
import os
import random
import struct
import sys
import uuid

import pytest

from functools import partial
from .. import base

if sys.version_info >= (3, ):
    xrange = range

def identity(in_func, out_func, data):
    assert data == out_func(in_func(data))


def try_identity(in_func, out_func, data_gen, iters):
    for _ in xrange(iters):
        identity(in_func, out_func, data_gen())


def gen_random_list(item_size, list_size):
    return tuple(os.urandom(item_size) for _ in xrange(list_size))


def test_base_58(benchmark, iters=1000):
    def data_gen():
        return (base.to_base_58, base.from_base_58, random.randint(0, 2**32 - 1)), {}
    benchmark.pedantic(identity, setup=data_gen, rounds=iters)


def test_compression(benchmark, iters=500):
    def test(data):
        for method in base.compression:
            compress = partial(base.compress, method=method)
            decompress = partial(base.decompress, method=method)
            identity(compress, decompress, data)

    def data_gen():
        return (os.urandom(36),), dict()

    benchmark.pedantic(test, setup=data_gen, rounds=iters//len(base.compression))


def test_compression_exceptions(iters=100):
    for _ in xrange(iters):
        test = os.urandom(36)
        with pytest.raises(Exception):
            base.compress(test, os.urandom(4))

        with pytest.raises(Exception):
            base.decompress(test, os.urandom(4))


def test_InternalMessage(benchmark, iters=500, impl=base):
    max_val = 2**8
    def setup():
        length = random.randint(0, max_val)
        array = gen_random_list(36, length)
        InternalMessage_serialization_validation(array, impl)
        InternalMessage_exceptions_validiation(array, impl)
        return (array, impl), {}

    benchmark.pedantic(
        InternalMessage_constructor_validation,
        setup=setup,
        rounds=iters)


def InternalMessage_constructor_validation(array, impl):
    msg = impl.InternalMessage(base.flags.broadcast, u'\xff', array)
    assert array == msg.payload
    assert msg.packets == (base.flags.broadcast, u'\xff'.encode('utf-8'),
                           msg.id, msg.time_58) + array
    p_hash = hashlib.sha384(b''.join(array + (msg.time_58, )))
    assert base.to_base_58(int(p_hash.hexdigest(), 16)) == msg.id
    assert impl.InternalMessage.feed_string(msg.string).id == msg.id

def InternalMessage_serialization_validation(array, impl):
    msg = impl.InternalMessage(base.flags.broadcast, u'\xff', array)
    if impl != base:
        assert base.InternalMessage.feed_string(msg.string).id == msg.id
    for method in impl.compression:
        msg.compression = []
        string = base.compress(msg.string[4:], method)
        string = struct.pack('!L', len(string)) + string
        msg.compression = [method]
        comp1 = impl.InternalMessage.feed_string(string, False, [method])
        comp2 = base.InternalMessage.feed_string(string, False, [method])
        assert msg.string == string == comp1.string == comp2.string


def InternalMessage_exceptions_validiation(array, impl):
    msg = impl.InternalMessage(base.flags.broadcast, 'TEST SENDER', array)
    for method in impl.compression:
        msg.compression = [method]
        with pytest.raises(Exception):
            impl.InternalMessage.feed_string(msg.string, True, [method])

        with pytest.raises(Exception):
            impl.InternalMessage.feed_string(msg.string[4:], False, [method])

        with pytest.raises(Exception):
            impl.InternalMessage.feed_string(msg.string)


def test_protocol(benchmark, iters=200, impl=base):
    def test(sub, enc, id_):
        print("constructing")
        test = impl.protocol(sub, enc)
        print("testing subnet equality")
        assert test.subnet == test[0] == sub
        print("testing encryption equality")
        assert test.encryption == test[1] == enc
        print("testing ID equality")
        assert id_ == test.id

    def setup():
        sub = str(uuid.uuid4())
        enc = str(uuid.uuid4())
        p_hash = hashlib.sha256(''.join(
            (sub, enc, base.protocol_version)).encode())
        return (sub, enc, base.to_base_58(int(p_hash.hexdigest(), 16))), {}

    benchmark.pedantic(test, setup=setup, rounds=iters)


def test_message_sans_network(benchmark, iters=1000):
    def setup():
        sen = str(uuid.uuid4())
        pac = gen_random_list(36, 10)
        base_msg = base.InternalMessage(base.flags.broadcast, sen, pac)
        return (sen, pac, base_msg), {}

    def test(sen, pac, base_msg):
        item = base.message(base_msg, None)
        assert item.packets == pac
        assert item.msg == base_msg
        assert item.sender == sen.encode()
        assert item.id == base_msg.id
        assert (item.time == base_msg.time ==
                base.from_base_58(item.time_58) ==
                base.from_base_58(base_msg.time_58))
        assert sen in repr(item)

    benchmark.pedantic(test, setup=setup, rounds=iters)
