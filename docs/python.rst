Python Implementation
=====================

This section contains information specific to the Python implementation of p2p.today. The python version is considered the reference implementation, and is where most experimenting on new protocol ideas will come from. Most users will only need to pay attention to the tutorial and last few sections (mesh, sync, chord). The rest is for developers who are interested in helping out.

Contents:

.. toctree::
    :maxdepth: 2

    python/tutorial
    python/base
    python/cbase
    python/utils
    python/messages
    python/flags
    python/mesh
    python/sync
    python/chord


Supported Transport Methods
~~~~~~~~~~~~~~~~~~~~~~~~~~~

+----------+------------------------------------------+
| Protocol |             Protocol  Object             |
+==========+==========================================+
| TCP      | ``py2p.base.Protocol(app, 'Plaintext')`` |
+----------+------------------------------------------+
| TLS/SSL  | ``py2p.base.Protocol(app, 'SSL')``       |
+----------+------------------------------------------+
