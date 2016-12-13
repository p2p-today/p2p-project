Python Implementation
=====================

This section contains information specific to the Python implementation of p2p.today. The python version is considered the reference implementation, and is where most experimenting on new protocol ideas will come from. Most users will only need to pay attention to the tutorial and last few sections (mesh, sync, chord, kademlia). The rest is for developers who are interested in helping out.

Contents:

.. toctree::
    :maxdepth: 2

    python/tutorial
    python/base
    python/cbase
    python/utils
    python/mesh
    python/sync
    python/chord
    python/kademlia


Supported Transport Methods
~~~~~~~~~~~~~~~~~~~~~~~~~~~

+----------+------------------------------------------+
| Protocol |             Protocol  Object             |
+==========+==========================================+
| TCP      | ``py2p.base.protocol(app, 'Plaintext')`` |
+----------+------------------------------------------+
| SSL      | ``py2p.base.protocol(app, 'SSL')``        |
+----------+------------------------------------------+
