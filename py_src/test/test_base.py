from __future__ import print_function
from __future__ import absolute_import

from functools import partial
from hashlib import sha256
from os import urandom
from sys import version_info
from uuid import uuid4

from base58 import (b58encode_int as to_base_58, b58decode_int as from_base_58)
from pytest import mark
from typing import (Any, Dict, Tuple)

from .. import base
from ..messages import MsgPackable

if version_info >= (3, ):
    xrange = range


def gen_random_list(item_size, list_size):
    # type: (int, int) -> Tuple[bytes, ...]
    return tuple(urandom(item_size) for _ in xrange(list_size))


@mark.run(order=1)
def test_Protocol(benchmark, iters=200, impl=base):
    # type: (Any, int, Any) -> None
    def test(sub, enc, id_):
        # type: (str, str, str) -> None
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
        # type: () -> Tuple[Tuple, Dict]
        sub = str(uuid4())
        enc = str(uuid4())
        p_hash = sha256(''.join((sub, enc, base.protocol_version)).encode())
        return (sub, enc, to_base_58(int(p_hash.hexdigest(), 16))), {}

    benchmark.pedantic(test, setup=setup, rounds=iters)


@mark.run(order=2)
def test_Message_sans_network(benchmark, iters=1000):
    # type: (Any, int) -> None
    def setup():
        # type: () -> Tuple[Tuple, Dict]
        sen = str(uuid4()).encode()
        pac = gen_random_list(36, 10)
        base_msg = base.InternalMessage(base.flags.broadcast, sen, pac)
        return (sen, pac, base_msg), {}

    def test(sen, pac, base_msg):
        # type: (MsgPackable, MsgPackable, base.InternalMessage) -> None
        item = base.Message(base_msg, None)
        assert item.packets == pac
        assert item.msg == base_msg
        assert item.sender == sen
        assert item.id == base_msg.id
        assert (item.time == base_msg.time == from_base_58(item.time_58) ==
                from_base_58(base_msg.time_58))
        assert "{}".format(sen) in repr(item)

    benchmark.pedantic(test, setup=setup, rounds=iters)
