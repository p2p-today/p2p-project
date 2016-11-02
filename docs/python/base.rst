Base Module
===============


.. automodule:: py2p.base
	:members:
	:exclude-members: flags, protocol
	:special-members: __init__, __iter__
	:undoc-members:

	.. autoclass:: flags
		:exclude-members: x

		.. autoattribute:: reserved

		**Main flags:**

		- .. autoattribute:: flags.broadcast
			:annotation:
		- .. autoattribute:: waterfall
			:annotation:
		- .. autoattribute:: whisper
			:annotation:
		- .. autoattribute:: renegotiate
			:annotation:
		- .. autoattribute:: ping
			:annotation:
		- .. autoattribute:: pong
			:annotation:

		**Sub-flags:**

		- .. autoattribute:: broadcast
			:annotation:
		- .. autoattribute:: compression
			:annotation:
		- .. autoattribute:: whisper
			:annotation:
		- .. autoattribute:: handshake
			:annotation:
		- .. autoattribute:: ping
			:annotation:
		- .. autoattribute:: pong
			:annotation:
		- .. autoattribute:: notify
			:annotation:
		- .. autoattribute:: peers
			:annotation:
		- .. autoattribute:: request
			:annotation:
		- .. autoattribute:: resend
			:annotation:
		- .. autoattribute:: response
			:annotation:
		- .. autoattribute:: store
			:annotation:
		- .. autoattribute:: retrieve
			:annotation:

		**Python-implemented compression methods:**

		- .. autoattribute:: bz2
			:annotation:
		- .. autoattribute:: gzip
			:annotation:
		- .. autoattribute:: lzma
			:annotation:
		- .. autoattribute:: zlib
			:annotation:

		**Other implementations' and/or planned compression methods:**

		- .. autoattribute:: bwtc
			:annotation:
		- .. autoattribute:: context1
			:annotation:
		- .. autoattribute:: defsum
			:annotation:
		- .. autoattribute:: dmc
			:annotation:
		- .. autoattribute:: fenwick
			:annotation:
		- .. autoattribute:: huffman
			:annotation:
		- .. autoattribute:: lzjb
			:annotation:
		- .. autoattribute:: lzjbr
			:annotation:
		- .. autoattribute:: lzp3
			:annotation:
		- .. autoattribute:: mtf
			:annotation:
		- .. autoattribute:: ppmd
			:annotation:
		- .. autoattribute:: simple
			:annotation:

	.. autoclass:: protocol
		:exclude-members: id