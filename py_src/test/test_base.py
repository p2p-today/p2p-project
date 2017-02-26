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

from typing import (Any, Callable, Dict, Tuple, Union)

from .. import base
from ..messages import MsgPackable

if sys.version_info >= (3, ):
    xrange = range


def gen_random_list(item_size, list_size):
    #type: (int, int) -> Tuple[bytes, ...]
    return tuple(os.urandom(item_size) for _ in xrange(list_size))


def test_Protocol(benchmark, iters=200, impl=base):
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
        #type: (MsgPackable, MsgPackable, base.InternalMessage) -> None
        item = base.Message(base_msg, None)
        assert item.packets == pac
        assert item.msg == base_msg
        assert item.sender == sen
        assert item.id == base_msg.id
        assert (item.time == base_msg.time == base.from_base_58(item.time_58)
                == base.from_base_58(base_msg.time_58))
        assert sen in repr(item)

    benchmark.pedantic(test, setup=setup, rounds=iters)
