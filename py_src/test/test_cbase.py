from __future__ import print_function
from __future__ import absolute_import

try:
    from functools import partial
    from sys import version_info

    from pytest import mark
    from typing import Any

    from .. import (cbase, flags)

    from .test_base import test_Protocol as _test_Protocol
    from .test_messages import test_InternalMessage as _test_InternalMessage

    if version_info >= (3, ):
        xrange = range

    @mark.run(order=3)
    def test_flags():
        # type: () -> None
        cf = cbase.flags
        assert flags.reserved == cf.reserved

        # main flags
        flags_main = (flags.broadcast, flags.whisper, flags.renegotiate,
                      flags.ping, flags.pong)
        cf_main = (cf.broadcast, cf.whisper, cf.renegotiate, cf.ping, cf.pong)
        assert flags_main == cf_main

        # sub-flags
        flags_sub = (flags.broadcast, flags.compression, flags.whisper,
                     flags.handshake, flags.ping, flags.pong, flags.notify,
                     flags.peers, flags.request, flags.resend, flags.response,
                     flags.store, flags.retrieve)
        cf_sub = (cf.broadcast, cf.compression, cf.whisper, cf.handshake,
                  cf.ping, cf.pong, cf.notify, cf.peers, cf.request, cf.resend,
                  cf.response, cf.store, cf.retrieve)
        assert flags_sub == cf_sub

        # common compression methods
        assert (flags.zlib, flags.gzip, flags.snappy) == (cf.zlib, cf.gzip,
                                                          cf.snappy)

    def test_Protocol(benchmark):
        # type: (Any) -> None
        _test_Protocol(benchmark, impl=cbase)

    def test_InternalMessage(benchmark):
        # type: (Any) -> None
        _test_InternalMessage(benchmark, impl=cbase)

except ImportError:
    pass
