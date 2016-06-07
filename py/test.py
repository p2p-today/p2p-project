import datetime, random, sys, time, uuid
import p2p

if sys.version_info[0] > 2:
    xrange = range

def main():
    test_base_58(1000)
    test_intersect(200)
    test_getUTC(20)
    test_compression(1000)

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

if __name__ == '__main__':
    main()