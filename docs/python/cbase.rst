Base Module (C++ Implementation)
================================


.. automodule:: py2p.cbase
	:members:
	:undoc-members:

	.. autoclass:: flags

		.. note::
			This is not actually a class, it just makes it formatted much neater to treat it as such. In the C++ implementation this is a module. You should not need to import it.

		**Main flags:**

		- .. data:: broadcast

		- .. data:: waterfall

		- .. data:: whisper

		- .. data:: renegotiate

		- .. data:: ping

		- .. data:: pong


		**Sub-flags:**

		- .. data:: broadcast

		- .. data:: compression

		- .. data:: whisper

		- .. data:: handshake

		- .. data:: ping

		- .. data:: pong

		- .. data:: notify

		- .. data:: peers

		- .. data:: request

		- .. data:: resend

		- .. data:: response

		- .. data:: store

		- .. data:: retrieve


		**C++-planned compression methods:**

		- .. data:: gzip

		- .. data:: zlib


		**Other implementations' and/or planned compression methods:**

		- .. data:: bwtc

		- .. data:: bz2

		- .. data:: context1

		- .. data:: defsum

		- .. data:: dmc

		- .. data:: fenwick

		- .. data:: huffman

		- .. data:: lzjb

		- .. data:: lzjbr

		- .. data:: lzma

		- .. data:: lzp3

		- .. data:: mtf

		- .. data:: ppmd

		- .. data:: simple


	.. autoclass:: py2p.cbase.pathfinding_message
		:members:
		:undoc-members:
		:special-members: __init__, __iter__

	.. autoclass:: py2p.cbase.protocol
		:members:
		:undoc-members:
		:special-members: __init__, __iter__