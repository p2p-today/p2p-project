IDs and Encoding
================

Knowing the overall message structure is great, but it’s not very
useful if you can’t construct the metadata. To do this, there are
four parts.

base\_58
++++++++

This encoding is taken from Bitcoin. If you’ve ever seen a Bitcoin
address, you’ve seen base\_58 encoding in action. The goal behind
it is to provide data compression without compromising its human
readability. Base\_58, for the purposes of this protocol, is
defined by the following python methods.

.. code-block:: python

    base_58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

    def to_base_58(i):
        string = ""
        while i:
            string = base_58[i % 58] + string
            i = i // 58    # Floor division is needed to prevent floats
        return string.encode()

    def from_base_58(string):
        if isinstance(string, bytes):
            string = string.decode()
        decimal = 0
        for char in string:
            decimal = decimal * 58 + base_58.index(char)
        return decimal

Subnets
+++++++

The last element is the ‘subnet ID’ we referred to in the previous
section. This object is used to weed out undesired connections. If
someone has the wrong protocol object, then your node will reject
them from connecting. A rough definition would be as follows:

.. code-block:: python

   class protocol(namedtuple("protocol", ['subnet', 'encryption'])):
       @property
       def id(self):
           info = [str(x) for x in self] + [protocol_version]
           h = hashlib.sha256(''.join(info).encode())
           return to_base_58(int(h.hexdigest(), 16))

Or more explicitly in javascript:

.. code-block:: javascript

   class protocol {
       constructor(subnet, encryption) {
           this.subnet = subnet;
           this.encryption = encryption;
       }

       get id() {
           var info = [this.subnet, this.encryption, protocol_version];
           var hash = SHA256(info.join(''));
           return to_base_58(BigInt(hash, 16));
       }
   }

Node IDs
++++++++

A node ID is taken from a SHA-384 hash of three other elements.
First, your outward facing address. Second, the ID of your subnet.
Third, a ‘user salt’ generated on startup. This hash is then
converted into base\_58.

Message IDs
+++++++++++

A message ID is also a SHA-384 hash. In this case, it is on a
message’s payload and its timestamp.

To get the hash, first join each packet together in order. Append
to this the message’s timestamp in base\_58. The ID you will use
is the hash of this string, encoded into base\_58.