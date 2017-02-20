Flag Definitions
================

Main Flags
++++++++++

These flags will denote the primary purpose of a message.

- broadcast     = ``0x00``
- renegotiate   = ``0x01``
- whisper       = ``0x02``
- ping          = ``0x03``
- pong          = ``0x04``

Sub-Flags
+++++++++

These flags will denote the secondary purpose, or a more specific purpose, of a message.

- broadcast     = ``0x00``
- compression   = ``0x01``
- whisper       = ``0x02``
- ping          = ``0x03``
- pong          = ``0x04``
- handshake     = ``0x05``
- notify        = ``0x06``
- peers         = ``0x07``
- request       = ``0x08``
- resend        = ``0x09``
- response      = ``0x0A``
- store         = ``0x0B``
- retrieve      = ``0x0C``

Compression Flags
+++++++++++++++++

These flags will denote standard compression methods.

All
~~~

- bwtc      = ``0x14``
- bz2       = ``0x10``
- context1  = ``0x15``
- defsum    = ``0x16``
- dmc       = ``0x17``
- fenwick   = ``0x18``
- gzip      = ``0x11``
- huffman   = ``0x19``
- lzjb      = ``0x1A``
- lzjbr     = ``0x1B``
- lzma      = ``0x12``
- lzp3      = ``0x1C``
- mtf       = ``0x1D``
- ppmd      = ``0x1E``
- simple    = ``0x1F``
- snappy    = ``0x20``
- zlib      = ``0x13``

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

Currently, this is all integers from ``0x00`` to ``0x30``. This list may be expanded later.
