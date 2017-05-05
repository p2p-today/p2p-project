from __future__ import print_function
from __future__ import absolute_import

from hashlib import sha256
from os import urandom
from random import randint
from struct import pack
from sys import version_info

from pytest import (mark, raises)

from functools import partial

from umsgpack import packb
from typing import (Any, Callable, Dict, Tuple, Union)

from .. import (flags, messages)
from .test_base import gen_random_list
from .test_utils import identity

if version_info >= (3, ):
    xrange = range


@mark.run(order=1)
def test_compression(iters=500):
    # type: (int) -> None
    for _ in xrange(iters):
        data = urandom(36)
        for method in messages.compression:
            compress = partial(messages.compress, method=method)
            decompress = partial(messages.decompress, method=method)
            identity(compress, decompress, data)


@mark.run(order=1)
def test_compression_exceptions(iters=100):
    # type: (int) -> None
    for _ in xrange(iters):
        test = urandom(36)
        with raises(Exception):
            messages.compress(test, urandom(4))  # type: ignore

        with raises(Exception):
            messages.decompress(test, urandom(4))  # type: ignore


@mark.run(order=1)
def test_InternalMessage(benchmark, iters=500, impl=messages):
    # type: (Any, int, Any) -> None
    max_val = 2**8

    def setup():
        # type: () -> Tuple[Tuple, Dict]
        length = randint(0, max_val)
        array = gen_random_list(36, length)
        InternalMessage_serialization_validation(array, impl)
        InternalMessage_exceptions_validiation(array, impl)
        return (array, impl), {}

    benchmark.pedantic(
        InternalMessage_constructor_validation, setup=setup, rounds=iters)


def InternalMessage_constructor_validation(array, impl):
    # type: (Tuple[messages.MsgPackable, ...], Any) -> None
    msg = impl.InternalMessage(flags.broadcast, u'\xff', array)
    assert array == msg.payload
    assert msg.packets == (flags.broadcast, u'\xff', msg.time) + array
    p_hash = sha256(msg._InternalMessage__non_len_string)
    assert p_hash.digest() == msg.id
    assert impl.InternalMessage.feed_string(msg.string).id == msg.id


def InternalMessage_serialization_validation(array, impl):
    # type: (Tuple[messages.MsgPackable, ...], Any) -> None
    msg = impl.InternalMessage(flags.broadcast, u'\xff', array)
    if impl != messages:
        assert messages.InternalMessage.feed_string(msg.string).id == msg.id
    for method in impl.compression:
        msg.compression = []
        string = messages.compress(msg.string[4:], method)
        string = pack('!L', len(string)) + string
        msg.compression = [method]
        comp1 = impl.InternalMessage.feed_string(string, False, [method])
        comp2 = messages.InternalMessage.feed_string(string, False, [method])
        assert msg.string == string == comp1.string == comp2.string


def InternalMessage_exceptions_validiation(array, impl):
    # type: (Tuple[messages.MsgPackable, ...], Any) -> None
    msg = impl.InternalMessage(flags.broadcast, 'TEST SENDER', array)
    for method in impl.compression:
        msg.compression = [method]
        with raises(Exception):
            impl.InternalMessage.feed_string(msg.string, True, [method])

        with raises(Exception):
            impl.InternalMessage.feed_string(msg.string[4:], False, [method])

        with raises(Exception):
            impl.InternalMessage.feed_string(msg.string)
