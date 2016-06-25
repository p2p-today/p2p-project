import datetime, hashlib, os, random, struct, sys, time, uuid
from functools import partial
from .. import base

if sys.version_info[0] > 2:
    xrange = range

def try_identity(in_func, out_func, data_gen, iters):
    for i in xrange(iters):
        test = data_gen()
        assert test == out_func(in_func(test))

def test_base_58(iters=1000):
    max_val = 2**32 - 1
    data_gen = partial(random.randint, 0, max_val)
    try_identity(base.to_base_58, base.from_base_58, data_gen, iters)

def test_intersect(iters=200):
    max_val = 2**12 - 1
    for i in xrange(iters):
        pair1 = sorted([random.randint(0, max_val), random.randint(0, max_val)])
        pair2 = sorted([random.randint(0, max_val), random.randint(0, max_val)])
        cross1 = [pair1[0], pair2[0]]
        cross2 = [pair1[1], pair2[1]]
        if max(cross1) < min(cross2):
            assert base.intersect(range(*pair1), range(*pair2)) == \
                                list(range(max(cross1), min(cross2)))
        else:
            assert base.intersect(range(*pair1), range(*pair2)) == []

def test_getUTC(iters=20):
    while iters:
        nowa, nowb = datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1), base.getUTC()
        assert nowa.days * 86400 + nowa.seconds in xrange(nowb-1, nowb+2)  # 1 second error margin
        time.sleep(random.random())
        iters -= 1

def test_compression(iters=100):
    for i in xrange(iters):
        test = os.urandom(36)
        for method in base.compression:
            assert test == base.decompress(base.compress(test, method), method)
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
    protocol = base.default_protocol
    for i in xrange(iters):
        length = random.randint(0, max_val)
        array = [os.urandom(36) for x in xrange(length)]
        msg = base.pathfinding_message(protocol, base.flags.broadcast, 'TEST SENDER', array)
        assert array == msg.payload
        assert msg.packets == [base.flags.broadcast, 'TEST SENDER'.encode(), msg.id, msg.time_58] + array
        for method in base.compression:
            msg.compression = []
            string = base.compress(msg.string[4:], method)
            string = struct.pack('!L', len(string)) + string
            msg.compression = [method]
            assert msg.string == string
            comp = base.pathfinding_message.feed_string(string, False, [method])
            assert msg.string == comp.string
            # Test certain errors
            try:
                base.pathfinding_message.feed_string(string, True, [method])
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
                base.pathfinding_message.feed_string(string)
            except:
                pass
            else:  # pragma: no cover
                raise Exception("Erroneously parses compressed message as plaintext %s" % string)

def test_protocol(iters=200):
    for i in range(iters):
        sub = str(uuid.uuid4())
        enc = str(uuid.uuid4())
        test = base.protocol(sub, enc)
        assert test.subnet == test[0] == sub
        assert test.encryption == test[1] == enc
        p_hash = hashlib.sha256(''.join([sub, enc, base.version]).encode())
        assert int(p_hash.hexdigest(), 16) == base.from_base_58(test.id)

def test_message_sans_network(iters=1000):
    for i in range(iters):
        sub = str(uuid.uuid4())
        enc = str(uuid.uuid4())
        sen = str(uuid.uuid4())
        pac = [os.urandom(36) for i in range(10)]
        prot = base.protocol(sub, enc)
        base_msg = base.pathfinding_message(prot, base.flags.broadcast, sen, pac)
        test = base.message(base_msg, None)
        assert test.packets == pac
        assert test.msg == base_msg
        assert test.sender == sen
        assert test.protocol == prot
        assert test.id == base_msg.id
        assert sen in repr(test)