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

from umsgpack import packb
from typing import (Any, Callable, Dict, Tuple, Union)

from .. import base

if sys.version_info >= (3, ):
    xrange = range


def identity(in_func, out_func, data):
    #type: (Union[partial, Callable], Union[partial, Callable], Any) -> bool
    assert data == out_func(in_func(data))


def try_identity(in_func, out_func, data_gen, iters):
    #type: (Callable, Callable, Callable, int) -> bool
    for _ in xrange(iters):
        identity(in_func, out_func, data_gen())


def gen_random_list(item_size, list_size):
    #type: (int, int) -> Tuple[bytes, ...]
    return tuple(os.urandom(item_size) for _ in xrange(list_size))


def test_base_58(benchmark, iters=1000):
    #type: (Any, int) -> None
    def data_gen():
        #type: () -> Tuple[Tuple, Dict]
        return (base.to_base_58, base.from_base_58,
                random.randint(0, 2**32 - 1)), {}

    benchmark.pedantic(identity, setup=data_gen, rounds=iters)


def test_pack_value(benchmark, iters=1000):
    #type: (Any, int) -> None
    def data_gen():
        #type: () -> Tuple[Tuple, Dict]
        return (partial(base.pack_value, 128 // 8), base.unpack_value,
                random.randint(0, 2**128 - 1)), {}

    benchmark.pedantic(identity, setup=data_gen, rounds=iters)


def test_compression(iters=500):
    #type: (int) -> None
    for _ in xrange(iters):
        data = os.urandom(36)
        for method in base.compression:
            compress = partial(base.compress, method=method)
            decompress = partial(base.decompress, method=method)
            identity(compress, decompress, data)


def test_compression_exceptions(iters=100):
    #type: (int) -> None
    for _ in xrange(iters):
        test = os.urandom(36)
        with pytest.raises(Exception):
            base.compress(test, os.urandom(4))  #type: ignore

        with pytest.raises(Exception):
            base.decompress(test, os.urandom(4))  #type: ignore


def test_InternalMessage(benchmark, iters=500, impl=base):
    #type: (Any, int, Any) -> None
    max_val = 2**8

    def setup():
        #type: () -> Tuple[Tuple, Dict]
        length = random.randint(0, max_val)
        array = gen_random_list(36, length)
        InternalMessage_serialization_validation(array, impl)
        InternalMessage_exceptions_validiation(array, impl)
        return (array, impl), {}

    benchmark.pedantic(
        InternalMessage_constructor_validation, setup=setup, rounds=iters)


def InternalMessage_constructor_validation(array, impl):
    #type: (Tuple[base.MsgPackable, ...], Any) -> None
    msg = impl.InternalMessage(base.flags.broadcast, u'\xff', array)
    assert array == msg.payload
    assert msg.packets == (base.flags.broadcast, u'\xff', msg.time) + array
    p_hash = hashlib.sha256(msg._InternalMessage__non_len_string)
    assert p_hash.digest() == msg.id
    assert impl.InternalMessage.feed_string(msg.string).id == msg.id


def InternalMessage_serialization_validation(array, impl):
    #type: (Tuple[base.MsgPackable, ...], Any) -> None
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
    #type: (Tuple[base.MsgPackable, ...], Any) -> None
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
    #type: (Any, int, Any) -> None
    def test(sub, enc, id_):
        #type: (str, str, str) -> None
        print("constructing")
        if hasattr(impl, 'protocol'):
            Protocol = impl.protocol
        else:
            Protocol = impl.Protocol
        test = Protocol(sub, enc)
        print("testing subnet equality")
        assert test.subnet == test[0] == sub
        print("testing encryption equality")
        assert test.encryption == test[1] == enc
        print("testing ID equality")
        assert id_ == test.id

    def setup():
        #type: () -> Tuple[Tuple, Dict]
        sub = str(uuid.uuid4())
        enc = str(uuid.uuid4())
        p_hash = hashlib.sha256(
            ''.join((sub, enc, base.protocol_version)).encode())
        return (sub, enc,
                base.to_base_58(int(p_hash.hexdigest(), 16)).decode()), {}

    benchmark.pedantic(test, setup=setup, rounds=iters)


def test_Message_sans_network(benchmark, iters=1000):
    #type: (Any, int) -> None
    def setup():
        #type: () -> Tuple[Tuple, Dict]
        sen = str(uuid.uuid4())
        pac = gen_random_list(36, 10)
        base_msg = base.InternalMessage(base.flags.broadcast, sen, pac)
        return (sen, pac, base_msg), {}

    def test(sen, pac, base_msg):
        #type: (base.MsgPackable, base.MsgPackable, base.InternalMessage) -> None
        item = base.Message(base_msg, None)
        assert item.packets == pac
        assert item.msg == base_msg
        assert item.sender == sen
        assert item.id == base_msg.id
        assert (item.time == base_msg.time == base.from_base_58(item.time_58)
                == base.from_base_58(base_msg.time_58))
        assert sen in repr(item)

    benchmark.pedantic(test, setup=setup, rounds=iters)
