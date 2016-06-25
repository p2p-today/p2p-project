import os, random, socket, sys, uuid
from functools import partial
from .. import net
from .test_base import try_identity

if sys.version_info[0] > 2:
    xrange = range

def test_bin_recovery(iters=1000):
    max_val = 2**256
    data_gen = partial(random.randint, 0, max_val)
    try_identity(net.int_to_bin, net.bin_to_int, data_gen, iters)

def test_packet_construction(iters=100):
    max_msg_len = 2**16
    max_pack_len = 8196 // 8 - 11
    min_pack_len = 354 // 8 - 11
    for i in xrange(iters):
        msg = os.urandom(random.randint(1, max_msg_len))
        pack_len = random.randint(min_pack_len, max_pack_len)
        packets = net.construct_packets(msg, pack_len)
        parsed_msg = b''.join(packets)
        num_headers = net.bin_to_int(parsed_msg[0:4])
        num_packets = net.bin_to_int(parsed_msg[4:num_headers+4])
        assert num_packets == len(packets)
        assert parsed_msg[num_headers+4:] == msg

def test_net_properties(iters=6):
    keysize = 1024
    for i in xrange(iters):
        if net.uses_RSA:
            keysize = random.choice([1024, 746, 618, 490, 362, 354])
        f = net.secure_socket(silent=True, keysize=keysize)
        assert f.keysize == keysize
        assert f.recv_charlimit == net.charlimit(keysize)
        del f

def test_net_sans_network(iters=3):
    for i in xrange(iters):
        f = net.secure_socket(silent=True, keysize=1024)
        test = os.urandom(random.randint(1, 117))
        f.settimeout(1)
        assert f.verify(test, f.sign(test, 'SHA-512'), f.pub)
        assert test == net.decrypt(net.encrypt(test, f.pub), f.priv)
        del f

def test_net_dup(iters=3):
    for i in xrange(iters):
        f = net.secure_socket(silent=True, keysize=1024)
        g = f.dup()
        # Both should be None
        assert f.peer_keysize == g.peer_keysize
        # Test key data in one go
        assert (f.pub, f.priv, f.keysize) == (g.pub, g.priv, g.keysize)
        # Test socket metadata in one go
        assert (f.type, f.family, f.proto) == (g.type, g.family, g.proto)
        del f, g

def test_net_connection(iters=3):
    keysizef = 1024
    keysizeg = 1024
    for i in xrange(iters):
        if net.uses_RSA:
            keysizef = random.choice([1024, 746, 618, 490, 362, 354])
            keysizeg = random.choice([1024, 746, 618, 490, 362, 354])
        f = net.secure_socket(silent=True, keysize=keysizef)
        g = net.secure_socket(silent=False, keysize=keysizeg)
        print(keysizef, keysizeg)
        f.bind(('localhost', 4444+i))
        f.listen(5)
        g.connect(('localhost', 4444+i))
        conn, addr = f.accept()
        test = str(uuid.uuid4()).encode()
        conn.send(test)
        assert test == g.recv(4) + g.recv(4) + g.recv()
        g.shutdown(socket.SHUT_RDWR)
        g.close()
        assert conn.recv() == ''
        del conn, f, g

def test_net_errors(iters=3):
    for i in xrange(iters):
        f = net.secure_socket(silent=True, keysize=1024)
        try:
            net.decrypt(b'a' * (f.keysize // 8), f.priv)
        except net.decryption_error:
            pass
        else:  # pragma: no cover
            raise Exception()
        try:
            net.verify(b'a' * (f.keysize // 8), b'b' * (f.keysize // 8), f.pub)
        except net.verification_error:
            pass
        else:  # pragma: no cover
            raise Exception()
        del f