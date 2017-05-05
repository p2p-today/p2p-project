Javascript Implementation
=========================

This section contains information specific to the Javascript implementation of p2p.today. Most users will only need to pay attention to the tutorial and last few sections (mesh, sync, chord). The rest is for developers who are interested in helping out.

Contents:

.. toctree::
    :maxdepth: 2

    javascript/tutorial
    javascript/base
    javascript/utils
    javascript/mesh
    javascript/sync
    javascript/chord


Supported Transport Methods
~~~~~~~~~~~~~~~~~~~~~~~~~~~

+------------+----------------------------------------------+
|  Protocol  |               Protocol  Object               |
+============+==============================================+
| TCP        | ``new js2p.base.Protocol(app, 'Plaintext')`` |
+------------+----------------------------------------------+
| TLS/SSL    | ``new js2p.base.Protocol(app, 'SSL')``       |
+------------+----------------------------------------------+
| Websocket  | ``new js2p.base.Protocol(app, 'ws')``        |
+------------+----------------------------------------------+
| WSS (soon) | ``new js2p.base.Protocol(app, 'wss')``       |
+------------+----------------------------------------------+
