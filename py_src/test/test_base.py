from __future__ import print_function
from __future__ import absolute_import

import hashlib
import os
import random
import struct
import sys
import uuid

from functools import partial
from .. import base

if sys.version_info >= (3, ):
    xrange = range

def try_identity(in_func, out_func, data_gen, iters):
    for _ in xrange(iters):
        test = data_gen()
        assert test == out_func(in_func(test))

def gen_random_list(item_size, list_size):
    return [os.urandom(item_size) for _ in xrange(list_size)]

def test_base_58(iters=1000):
    max_val = 2**32 - 1
    data_gen = partial(random.randint, 0, max_val)
    try_identity(base.to_base_58, base.from_base_58, data_gen, iters)

def test_compression(iters=100):
    for method in base.compression:
        compress = partial(base.compress, method=method)
        decompress = partial(base.decompress, method=method)
        data_gen = partial(os.urandom, 36)
        try_identity(compress, decompress, data_gen, iters)

def test_compression_exceptions(iters=100):
    for _ in xrange(iters):
        test = os.urandom(36)
        try:
            base.compress(test, os.urandom(4))
        except:
            pass
        else:  # pragma: no cover
            raise Exception("Unknown compression method should raise error")
        try:
            base.decompress(test, os.urandom(4))
        except:
            pass
        else:  # pragma: no cover
            raise Exception("Unknown compression method should raise error")

def test_pathfinding_message(iters=500):
    max_val = 2**8
    for _ in xrange(iters):
        length = random.randint(0, max_val)
        array = gen_random_list(36, length)
        pathfinding_message_constructor_validation(array)
        pathfinding_message_exceptions_validiation(array)

def pathfinding_message_constructor_validation(array):
    msg = base.pathfinding_message(base.flags.broadcast, 'TEST SENDER', array)
    assert array == msg.payload
    assert msg.packets == [base.flags.broadcast, 'TEST SENDER'.encode(), msg.id, msg.time_58] + array
    for method in base.compression:
        msg.compression = []
        string = base.compress(msg.string[4:], method)
        string = struct.pack('!L', len(string)) + string
        msg.compression = [method]
        comp = base.pathfinding_message.feed_string(string, False, [method])
        assert msg.string == string == comp.string

def pathfinding_message_exceptions_validiation(array):
    msg = base.pathfinding_message(base.flags.broadcast, 'TEST SENDER', array)
    for method in base.compression:
        msg.compression = [method]
        try:
            base.pathfinding_message.feed_string(msg.string, True, [method])
        except:
            pass
        else:  # pragma: no cover
            raise Exception("Erroneously parses sized message with sizeless: %s" % string)
        try:
            base.pathfinding_message.feed_string(msg.string[4:], False, [method])
        except:
            pass
        else:  # pragma: no cover
            raise Exception("Erroneously parses sizeless message with size %s" % string)
        try:
            base.pathfinding_message.feed_string(msg.string)
        except:
            pass
        else:  # pragma: no cover
            raise Exception("Erroneously parses compressed message as plaintext %s" % string)

def test_protocol(iters=200):
    for _ in range(iters):
        sub = str(uuid.uuid4())
        enc = str(uuid.uuid4())
        test = base.protocol(sub, enc)
        assert test.subnet == test[0] == sub
        assert test.encryption == test[1] == enc
        p_hash = hashlib.sha256(''.join([sub, enc, base.protocol_version]).encode())
        assert int(p_hash.hexdigest(), 16) == base.from_base_58(test.id)

def test_message_sans_network(iters=1000):
    for _ in range(iters):
        sen = str(uuid.uuid4())
        pac = gen_random_list(36, 10)
        base_msg = base.pathfinding_message(base.flags.broadcast, sen, pac)
        test = base.message(base_msg, None)
        assert test.packets == pac
        assert test.msg == base_msg
        assert test.sender == sen.encode()
        assert test.id == base_msg.id
        assert test.time == base_msg.time == base.from_base_58(test.time_58) == base.from_base_58(base_msg.time_58)
        assert sen in repr(test)