Flag Definitions
================

Main Flags
++++++++++

These flags will denote the primary purpose of a message.

- broadcast     = ``"\x00"``
- waterfall     = ``"\x01"``
- whisper       = ``"\x02"``
- renegotiate   = ``"\x03"``
- ping          = ``"\x04"``
- pong          = ``"\x05"``

Sub-Flags
+++++++++

These flags will denote the secondary purpose, or a more specific purpose, of a message.

- broadcast     = ``"\x00"``
- compression   = ``"\x01"``
- whisper       = ``"\x02"``
- handshake     = ``"\x03"``
- ping          = ``"\x04"``
- pong          = ``"\x05"``
- notify        = ``"\x06"``
- peers         = ``"\x07"``
- request       = ``"\x08"``
- resend        = ``"\x09"``
- response      = ``"\x0A"``
- store         = ``"\x0B"``
- retrieve      = ``"\x0C"``

Compression Flags
+++++++++++++++++

These flags will denote standard compression methods.

All
~~~

- bwtc      = ``"\x14"``
- bz2       = ``"\x10"``
- context1  = ``"\x15"``
- defsum    = ``"\x16"``
- dmc       = ``"\x17"``
- fenwick   = ``"\x18"``
- gzip      = ``"\x11"``
- huffman   = ``"\x19"``
- lzjb      = ``"\x1A"``
- lzjbr     = ``"\x1B"``
- lzma      = ``"\x12"``
- lzp3      = ``"\x1C"``
- mtf       = ``"\x1D"``
- ppmd      = ``"\x1E"``
- simple    = ``"\x1F"``
- zlib      = ``"\x13"``

Python Implemented
~~~~~~~~~~~~~~~~~~

- bz2
- gzip
- lzma
- zlib

.. note::
    Only on systems where these modules are available

C++ Planned
~~~~~~~~~~~

- gzip
- zlib

Javascript Implemented
~~~~~~~~~~~~~~~~~~~~~~

- gzip
- zlib

Reserved Flags
++++++++++++++

These define the flags that other applications should *not* use, as they either are (or will be) used by the standard protocol.

Currently, this is all single byte characters from ``0x00`` to ``0x20``. This list may be expanded later.
