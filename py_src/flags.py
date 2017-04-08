"""A namespace to hold protocol-defined flags"""
# Reserved set of bytes
reserved = tuple(range(0x30))

# main flags
broadcast = 0x00  # also sub-flag
renegotiate = 0x01
whisper = 0x02  # also sub-flag
ping = 0x03  # Unused, but reserved
pong = 0x04  # Unused, but reserved

# sub-flags
# broadcast = 0x00
compression = 0x01
# whisper = 0x02
# ping = 0x03
# pong = 0x04
handshake = 0x05
notify = 0x06
peers = 0x07
request = 0x08
resend = 0x09
response = 0x0A
store = 0x0B
retrieve = 0x0C
retrieved = 0x0D
forward = 0x0E
new_paths = 0x0F
revoke_paths = 0x10
delta = 0x11

# implemented compression methods
bz2 = 0x10
gzip = 0x11
lzma = 0x12
zlib = 0x13
snappy = 0x20

# non-implemented compression methods (based on list from compressjs):
bwtc = 0x14
context1 = 0x15
defsum = 0x16
dmc = 0x17
fenwick = 0x18
huffman = 0x19
lzjb = 0x1A
lzjbr = 0x1B
lzp3 = 0x1C
mtf = 0x1D
ppmd = 0x1E
simple = 0x1F
