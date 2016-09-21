Serialization
=============

.. raw:: html

    <link rel="stylesheet" href="../_static/code_wrap.css" type="text/css">

The first step to any of this is being able to understand messages sent
through the network. To do this, you need to build a parser. Each
message can be considered to have three segments: a header, metadata,
and payload. The header is used to figure out the size of a message, as
well as how to divide up its various packets. The metadata is used to
assist propagation functions. And the payload is what the user on the
other end receives.

A more formal definition would look like:

.. code-block:: none

    Size of message    - 4 (big-endian) bytes defining the size of the message
    ------------------------All below may be compressed------------------------
    Size of packet 0   - 4 bytes defining the plaintext size of packet 0
    Size of packet 1   - 4 bytes defining the plaintext size of packet 1
    ...
    Size of packet n-1 - 4 bytes defining the plaintext size of packet n-1
    Size of packet n   - 4 bytes defining the plaintext size of packet n
    ---------------------------------End Header--------------------------------
    Pathfinding header - [broadcast, waterfall, whisper, renegotiate]
    Sender ID          - A base_58 SHA384-based ID for the sender
    Message ID         - A base_58 SHA384-based ID for the message packets
    Timestamp          - A base_58 unix UTC timestamp of initial broadcast
    Payload packets
      Payload header   - [broadcast, whisper, handshake, peers, request, response]
      Payload contents

To understand this, let’s work from the bottom up. When a user wants to
construct a message, they feed a list of packets. For this example,
let’s say it’s ``['broadcast', 'test message']``. When this list is fed
into a node, it adds the metadata section as outlined below.

The first element is the pathfinding header. This alerts nodes to how
they should treat the message. If it is ``broadcast`` or ``waterfall``
they are to forward this message to their peers. If it is ``whisper``
they are not to do so. ``renegotiate`` is exclusivley used for
connection management.

Next is the sender ID, used to identify a user in your routing table. So
if a user wants to reply to a message, they look up this ID in their
routing table. As will be discussed below, there are methods you can
specifically request a user ID to connect to.

After this is a message ID and timestamp, used to filter out messages
that a node has seen before. This can also be used as a checksum.

``['broadcast', '6VnYj9LjoVLTvU3uPhy4nxm6yv2wEvhaRtGHeV9wwFngWGGqKAzuZ8jK6gFuvq737V',
'72tG7phqoAnoeWRKtWoSmseurpCtYg2wHih1y5ZX1AmUvihcH7CPZHThtm9LGvKtj7', '3EfSDb',
'broadcast', 'test message']``

One thing to notice is that the sender ID, message ID, and timestamp are
all in a strange encoding. This is base\_58, borrowed from Bitcoin. It’s
a way to encode numbers that allows for sufficient density while still
maintaining some human readability. This will get defined formally later
in the paper.

All of this still leaves out the header. Constructing this goes as follows:

For each packet, compute its length and pack this into four bytes. So a
message of length 6 would look like ``'\x00\x00\x00\x06'``. Take the resulting
string and prepend it to the packets. In this example, you would end up with:
``'\x00\x00\x00\t\x00\x00\x00B\x00\x00\x00B\x00\x00\x00\x06\x00\x00\x00\t\x00\x00\x00\x0cbroadcast6VnYj9LjoVLTvU3uPhy4nxm6yv2wEvhaRtGHeV9wwFngWGGqKAzuZ8jK6gFuvq737V7iSCRDcHZwYtxGbTCz1rwDbUkt7YrbAh2VdS4A75hRuM6xan2gjmZqiVjLkMqiHE3Q3EfSDbbroadcasttest message'``.

After running this message through whatever compression algorith which has
been negotiated with the node's peer, it compute the message's size, and pack
this into four bytes: ``'\x00\x00\x00\xc0'``. This results in a final message of:

``'\x00\x00\x00\xc0\x00\x00\x00\t\x00\x00\x00B\x00\x00\x00B\x00\x00\x00\x06\x00\x00\x00\t\x00\x00\x00\x0cbroadcast6VnYj9LjoVLTvU3uPhy4nxm6yv2wEvhaRtGHeV9wwFngWGGqKAzuZ8jK6gFuvq737V7iSCRDcHZwYtxGbTCz1rwDbUkt7YrbAh2VdS4A75hRuM6xan2gjmZqiVjLkMqiHE3Q3EfSDbbroadcasttest message'``