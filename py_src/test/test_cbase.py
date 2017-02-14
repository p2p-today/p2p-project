from __future__ import print_function
from __future__ import absolute_import

try:
    import hashlib
    import os
    import random
    import struct
    import sys
    import uuid

    from functools import partial
    from typing import Any

    from .. import base, cbase

    from . import test_base

    if sys.version_info >= (3, ):
        xrange = range

    def test_flags():
        #type: () -> None
        bf = base.flags
        cf = cbase.flags
        assert bf.reserved == cf.reserved

        # main flags
        bf_main = (bf.broadcast, bf.whisper, bf.renegotiate, bf.ping, bf.pong)
        cf_main = (cf.broadcast, cf.whisper, cf.renegotiate, cf.ping, cf.pong)
        assert bf_main == cf_main

        # sub-flags
        bf_sub = (bf.broadcast, bf.compression, bf.whisper, bf.handshake,
                  bf.ping, bf.pong, bf.notify, bf.peers, bf.request, bf.resend,
                  bf.response, bf.store, bf.retrieve)
        cf_sub = (cf.broadcast, cf.compression, cf.whisper, cf.handshake,
                  cf.ping, cf.pong, cf.notify, cf.peers, cf.request, cf.resend,
                  cf.response, cf.store, cf.retrieve)
        assert bf_sub == cf_sub

        # common compression methods
        assert (bf.zlib, bf.gzip, bf.snappy) == (cf.zlib, cf.gzip, cf.snappy)

    def test_protocol(benchmark):
        #type: (Any) -> None
        test_base.test_protocol(benchmark, impl=cbase)

    def test_InternalMessage(benchmark):
        #type: (Any) -> None
        test_base.test_InternalMessage(benchmark, impl=cbase)

except ImportError:
    pass
