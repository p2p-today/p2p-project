import datetime, hashlib, random, struct, sys, threading, time, uuid
import p2p, net

if sys.version_info[0] > 2:
    xrange = range

def test_base_58(iters):
    max_val = 2**32 - 1
    for i in xrange(iters):
        test = random.randint(0, max_val)
        assert test == p2p.from_base_58(p2p.to_base_58(test))

def test_intersect(iters):
    max_val = 2**12 - 1
    for i in xrange(iters):
        pair1 = sorted([random.randint(0, max_val), random.randint(0, max_val)])
        pair2 = sorted([random.randint(0, max_val), random.randint(0, max_val)])
        cross1 = [pair1[0], pair2[0]]
        cross2 = [pair1[1], pair2[1]]
        if max(cross1) < min(cross2):
            assert p2p.intersect(range(*pair1), range(*pair2)) == \
                                list(range(max(cross1), min(cross2)))
        else:
            assert p2p.intersect(range(*pair1), range(*pair2)) == []

def test_getUTC(secs):
    while secs:
        a = datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)
        assert a.days * 86400 + a.seconds == p2p.getUTC()
        time.sleep(1)
        secs -= 1

def test_compression(iters):
    for i in xrange(iters):
        test = str(uuid.uuid4()).encode()
        for method in p2p.compression:
            assert test == p2p.decompress(p2p.compress(test, method), method)

def test_pathfinding_message(iters):
    max_val = 2**8
    protocol = p2p.default_protocol
    for i in xrange(iters):
        length = random.randint(0, max_val)
        array = [str(uuid.uuid4()).encode() for x in xrange(length)]
        msg = p2p.pathfinding_message(protocol, p2p.flags.broadcast, 'TEST SENDER', array)
        assert array == msg.payload
        assert msg.packets == [p2p.flags.broadcast, 'TEST SENDER'.encode(), msg.id, msg.time_58] + array
        for method in p2p.compression:
            msg.compression = []
            string = p2p.compress(msg.string[4:], method)
            string = struct.pack('!L', len(string)) + string
            msg.compression = [method]
            assert msg.string == string
            comp = p2p.pathfinding_message.feed_string(protocol, string, False, [method])
            assert msg.string == comp.string
            # Test certain errors
            try:
                p2p.pathfinding_message.feed_string(protocol, string, True, [method])
            except:
                pass
            else:  # pragma: no cover
                assert False, "Erroneously parses sized message with sizeless"
            try:
                p2p.pathfinding_message.feed_string(protocol, msg.string[4:], False, [method])
            except:
                pass
            else:  # pragma: no cover
                assert False, "Erroneously parses sizeless message with size"
            try:
                p2p.pathfinding_message.feed_string(protocol, string)
            except:
                pass
            else:  # pragma: no cover
                assert False, "Erroneously parses compressed message as plaintext"

def test_protocol(iters):
    for i in range(iters):
        sep = str(uuid.uuid4())
        sub = str(uuid.uuid4())
        enc = str(uuid.uuid4())
        test = p2p.protocol(sep, sub, enc)
        assert test.sep == sep
        assert test[0] == sep
        assert test.subnet == sub
        assert test[1] == sub
        assert test.encryption == enc
        assert test[2] == enc
        p_hash = hashlib.sha256(''.join([sep, sub, enc, p2p.version]).encode())
        assert int(p_hash.hexdigest(), 16) == p2p.from_base_58(test.id)
        assert test.id != p2p.default_protocol.id

def test_message_sans_network(iters):
    for i in range(iters):
        sep = str(uuid.uuid4())
        sub = str(uuid.uuid4())
        enc = str(uuid.uuid4())
        sen = str(uuid.uuid4())
        pac = [str(uuid.uuid4()) for i in range(10)]
        prot = p2p.protocol(sep, sub, enc)
        test = p2p.message(sep.join(pac), sen, prot, p2p.getUTC(), None)
        assert test.packets == pac
        assert test.msg == sep.join(pac)
        assert test[0] == sep.join(pac)
        assert test.sender == sen
        assert test[1] == sen
        assert test.protocol == prot
        assert test[2] == prot
        assert test[3] == test.time
        m_hash = hashlib.sha384((sep.join(pac) + p2p.to_base_58(test.time)).encode())
        assert int(m_hash.hexdigest(), 16) == p2p.from_base_58(test.id)

def test_net_sans_network(iters):
    for i in range(iters):
        f = net.secure_socket(silent=True, keysize=1024)
        test = str(uuid.uuid4()).encode()
        f.settimeout(1)
        assert f.keysize == 1024
        assert test == net.decrypt(net.encrypt(test, f.pub), f.priv)
        for op in ['best', 'SHA-512']:
            assert f.verify(test, f.sign(test, op), f.pub)
        g = f.dup()
        assert f.pub == g.pub
        assert f.priv == g.priv
        assert f.keysize == g.keysize
        assert f.peer_keysize == g.peer_keysize
        assert f.fileno() == g.fileno()
        assert f.type == g.type
        assert f.family == g.family
        assert f.proto == g.proto
        try:
            net.decrypt('a' * (f.keysize // 8), f.priv)
        except net.decryption_error:
            pass
        else:  # pragma: no cover
            assert False
        try:
            net.verify('a' * (f.keysize // 8), 'b' * (f.keysize // 8), f.pub)
        except net.verification_error:
            pass
        else:  # pragma: no cover
            assert False

def test_net_connection(iters):
    import net
    keysizef = 1024
    keysizeg = 1024
    for i in xrange(iters):
        if net.uses_RSA:
            keysizef = random.choice([1024, 745, 618, 490, 362, 354])
            keysizeg = random.choice([1024, 745, 618, 490, 362, 354])
        f = net.secure_socket(silent=True, keysize=keysizef)
        g = net.secure_socket(silent=True, keysize=keysizeg)
        f.bind(('localhost', 4444+i))
        f.listen(5)
        g.connect(('localhost', 4444+i))
        conn, addr = f.accept()
        test = str(uuid.uuid4()).encode()
        conn.send(test)
        assert test == g.recv()
        f.close()
        g.close()

def main():
    print("Testing base_58")
    test_base_58(1000)
    print("Testing intersect")
    test_intersect(200)
    print("Testing UTC fetch")
    test_getUTC(20)
    print("Testing compression methods")
    test_compression(1000)
    print("Testing protocol state machine")
    test_protocol(1000)
    print("Testing pathfinding state machine")
    test_pathfinding_message(200)
    print("Testing message state machine (sans network functions)")
    test_message_sans_network(1000)
    print("Testing secure socket methods")
    test_net_sans_network(2)
    print("Testing secure socket communications")
    test_net_connection(2)

if __name__ == '__main__':
    main()