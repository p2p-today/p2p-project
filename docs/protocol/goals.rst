Protocol Goals
==============

Currently there are very few ways to set up a peer-to-peer network between different languages. There are several proocols out there, but all of them are very specialized, complicated, or both. This is not what we want in a language-agnostic protocol. While we may go after other goals in addition to these, our explicit goals will be laid out below:

Portable
++++++++

The underlying protocol should use only language agnostic features. That is to say, every message will be entirely of strings, and any formatting (like JSON) must be strictly laid out so that you can parse it without knowing the entirety of said formatting.

Any features which are not language agnostic **must** be optional. This includes things like compression, encryption, etc.

Fast
++++

Reconstructing a plaintext message with three, single-character, user-placed packets **must** take <1.5ms. (In this case, I'm judging off my laptop's time, rather than my desktop. I have a `Lenovo Carbon <http://it.nmu.edu/docs/thinkpad-specs#16s>`_ running Kubuntu 16.04.)

Dense
+++++

Where there are no disadvantages to the above, the resulting messages should be as dense as possible.

Abstracted
++++++++++

The resulting protocol **must** be capturable in an object. That is to say, one should be able to call properties of an object whose underlying structures may change at any time. Parsing a message should **never** require knowledge of network state, with the sole exception of compression.

Notes
+++++

These goals are subject to change in the future. If some awesome feature requires that packet reconstruction takes longer, this does not necessarily stop that feature from being implemented. The only hard rule is the portability one.

Also worthy of note is that backwards compatability *intentionally* is not on this list. It may be that version 0.4.* and 0.5.* can understand each other, but they will *actively reject* each other. This allows for an ease of change that isn't present if you require backwards compatability. After the 1.0 release, we will try and maintain backports that you can reliably access. If you can't through a package manager, you certainly can from the git releases.

In the next section, we will outline how you construct and serialize a message.