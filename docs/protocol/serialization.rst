Serialization
=============

Serialization is much simpler than it used to be. Before, this set of libraries
had its own serialization scheme. This was generally a bad idea. It was alright
for sending strings, and good for a proof of concept, but it would have taken
far too much effort to maintain.

Now we rely on `msgpack <https://msgpack.org>`_ , with some small modifications.
Essentially, the process is capturable with the following JavaScript:

.. code:: javascript

    function serialize(msg, compressions)   {
        let to_serialize = [msg.type, msg.sender, msg.time, ...msg.payload];
        let bare_serialized = msgpack.encode(to_serialize);
        let checksum = SHA256(bare_serialized);  // should return binary digest
        let payload = compress(checksum + bare_serialized, compressions);
        let header = pack_big_endian_uint32(payload.length);
        return header + payload;
    }
