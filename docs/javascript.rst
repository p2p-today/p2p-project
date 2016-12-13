Javascript Implementation
=========================

This section contains information specific to the Javascript implementation of p2p.today. Most users will only need to pay attention to the tutorial and last few sections (mesh, sync, chord, kademlia). The rest is for developers who are interested in helping out.

Contents:

.. toctree::
    :maxdepth: 2

    javascript/tutorial
    javascript/base
    javascript/utils
    javascript/mesh
    javascript/sync
    javascript/chord
    javascript/kademlia


Supported Transport Methods
~~~~~~~~~~~~~~~~~~~~~~~~~~~

+------------+----------------------------------------------+
|  Protocol  |               Protocol  Object               |
+============+==============================================+
| TCP        | ``new js2p.base.protocol(app, 'Plaintext')`` |
+------------+----------------------------------------------+
| Websocket  | ``new js2p.base.protocol(app, 'ws')``        |
+------------+----------------------------------------------+
| WSS (soon) | ``new js2p.base.protocol(app, 'wss')``       |
+------------+----------------------------------------------+
