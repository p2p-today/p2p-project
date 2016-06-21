import datetime, hashlib, os, random, struct, sys, time, uuid
from .. import base

if sys.version_info[0] > 2:
    xrange = range

def test_base_58(iters=1000):
    max_val = 2**32 - 1
    for i in xrange(iters):
        test = random.randint(0, max_val)
        assert test == base.from_base_58(base.to_base_58(test))

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
        assert nowa.days * 86400 + nowa.seconds == nowb
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
            assert False, "Unknown compression method should raise error"
        try:
            base.decompress(test, os.urandom(4))
        except:
            pass
        else:  # pragma: no cover
            assert False, "Unknown compression method should raise error"

def test_pathfinding_message(iters=500):
    max_val = 2**8
    protocol = base.default_protocol
    for i in xrange(iters):
        length = random.randint(0, max_val)
        array = [str(uuid.uuid4()).encode() for x in xrange(length)]  # TODO: Make this work with os.urandom(36)
        msg = base.pathfinding_message(protocol, base.flags.broadcast, 'TEST SENDER', array)
        assert array == msg.payload
        assert msg.packets == [base.flags.broadcast, 'TEST SENDER'.encode(), msg.id, msg.time_58] + array
        for method in base.compression:
            msg.compression = []
            string = base.compress(msg.string[4:], method)
            string = struct.pack('!L', len(string)) + string
            msg.compression = [method]
            assert msg.string == string
            comp = base.pathfinding_message.feed_string(protocol, string, False, [method])
            assert msg.string == comp.string
            # Test certain errors
            try:
                base.pathfinding_message.feed_string(protocol, string, True, [method])
            except:
                pass
            else:  # pragma: no cover
                assert False, "Erroneously parses sized message with sizeless: %s" % string
            try:
                base.pathfinding_message.feed_string(protocol, msg.string[4:], False, [method])
            except:
                pass
            else:  # pragma: no cover
                assert False, "Erroneously parses sizeless message with size %s" % string
            try:
                base.pathfinding_message.feed_string(protocol, string)
            except:
                pass
            else:  # pragma: no cover
                assert False, "Erroneously parses compressed message as plaintext %s" % string

def test_protocol(iters=200):
    for i in range(iters):
        sep = str(uuid.uuid4())
        sub = str(uuid.uuid4())
        enc = str(uuid.uuid4())
        test = base.protocol(sep, sub, enc)
        assert test.sep == sep
        assert test[0] == sep
        assert test.subnet == sub
        assert test[1] == sub
        assert test.encryption == enc
        assert test[2] == enc
        p_hash = hashlib.sha256(''.join([sep, sub, enc, base.version]).encode())
        assert int(p_hash.hexdigest(), 16) == base.from_base_58(test.id)
        assert test.id != base.default_protocol.id

def test_message_sans_network(iters=1000):
    for i in range(iters):
        sep = str(uuid.uuid4())
        sub = str(uuid.uuid4())
        enc = str(uuid.uuid4())
        sen = str(uuid.uuid4())
        pac = [str(uuid.uuid4()) for i in range(10)]
        prot = base.protocol(sep, sub, enc)
        test = base.message(sep.join(pac), sen, prot, base.getUTC(), None)
        assert test.packets == pac
        assert test.msg == sep.join(pac)
        assert test[0] == sep.join(pac)
        assert test.sender == sen
        assert test[1] == sen
        assert test.protocol == prot
        assert test[2] == prot
        assert test[3] == test.time
        m_hash = hashlib.sha384(sep.join(pac).encode() + base.to_base_58(test.time))
        assert int(m_hash.hexdigest(), 16) == base.from_base_58(test.id)
        assert sen in repr(test)