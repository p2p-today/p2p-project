import random, sys, uuid
from .. import net

if sys.version_info[0] > 2:
    xrange = range

def test_net_sans_network(iters=3):
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
        # assert f.fileno() == g.fileno()  # This only works in python2, apparently
        assert f.type == g.type
        assert f.family == g.family
        assert f.proto == g.proto
        try:
            net.decrypt('a'.encode() * (f.keysize // 8), f.priv)
        except net.decryption_error:
            pass
        else:  # pragma: no cover
            assert False
        try:
            net.verify('a'.encode() * (f.keysize // 8), 'b'.encode() * (f.keysize // 8), f.pub)
        except net.verification_error:
            pass
        else:  # pragma: no cover
            assert False
        del f, g

def test_net_connection(iters=3):
    keysizef = 1024
    keysizeg = 1024
    for i in xrange(iters):
        if net.uses_RSA:
            keysizef = random.choice([1024, 746, 618, 490, 362, 354])
            keysizeg = random.choice([1024, 746, 618, 490, 362, 354])
        f = net.secure_socket(silent=True, keysize=keysizef)
        g = net.secure_socket(silent=True, keysize=keysizeg)
        print(keysizef, keysizeg)
        f.bind(('localhost', 4444+i))
        f.listen(5)
        g.connect(('localhost', 4444+i))
        conn, addr = f.accept()
        test = str(uuid.uuid4()).encode()
        conn.send(test)
        assert test == g.recv()
        f.close()
        g.close()
        del conn, f, g