Flag Definitions
================

Main Flags
++++++++++

These flags will denote the primary purpose of a message.

- broadcast     = ``"\x00"``
- renegotiate   = ``"\x01"``
- whisper       = ``"\x02"``
- ping          = ``"\x03"``
- pong          = ``"\x04"``

Sub-Flags
+++++++++

These flags will denote the secondary purpose, or a more specific purpose, of a message.

- broadcast     = ``"\x00"``
- compression   = ``"\x01"``
- whisper       = ``"\x02"``
- ping          = ``"\x03"``
- pong          = ``"\x04"``
- handshake     = ``"\x05"``
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
- snappy    = ``"\x20"``
- zlib      = ``"\x13"``

Python Implemented
~~~~~~~~~~~~~~~~~~

- bz2
- gzip
- lzma
- snappy
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
- snappy
- zlib

Reserved Flags
++++++++++++++

These define the flags that other applications should *not* use, as they either are (or will be) used by the standard protocol.

Currently, this is all single byte characters from ``0x00`` to ``0x30``. This list may be expanded later.
