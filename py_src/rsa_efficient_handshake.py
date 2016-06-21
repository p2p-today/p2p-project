import struct

def key_to_bin(key):
    arr = []
    while key:
        arr = [key % 256] + arr
        key //= 256
    return struct.pack("!" + "B" * len(arr), *arr)

def key_from_bin(key):
    arr = struct.unpack("!" + "B" * len(key), key)
    i = 0
    for n in arr:
        i *= 256
        i += n
    return i

def predict_len(keysize):
    length = (keysize + 7) // 8
    return length

def test(iters):
    for i in range(1, iters + 1):
        test = 2**i - 1
        assert test == key_from_bin(key_to_bin(test))
        assert len(key_to_bin(test)) == predict_len(i)