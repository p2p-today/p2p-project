.. p2p-project documentation master file, created by
   sphinx-quickstart on Tue Aug  2 13:07:12 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to p2p.today's documentation!
=====================================

Goal
~~~~

We are trying to make peer-to-peer networking easy. Right now there are very few libraries which allow multiple languages to use the same distributed network.

We're aiming to fix that by providing several network models, which you can use simply by creating an object. These objects will have the simplest API possible to do the job, as well as some features under the hood which you can hook into.

What We Have
~~~~~~~~~~~~

There are several projects in the work right now. Several of these could be considered stable, but we're going to operate under the "beta" label for some time now.

Base Network Structures
~~~~~~~~~~~~~~~~~~~~~~~

All of our networks will be built on common base classes. Because of this, we can guarantee some network features.

#. Networks will have as much common codebase as possible
#. Networks will have opportunistic compression across the board
#. Node IDs will be generated in a consistent manner
#. Command codes will be consistent across network types

Mesh Network
~~~~~~~~~~~~

This is our unorganized network. It operates under three simple rules:

#. The first node to broadcast sends the message to all its peers
#. Each node which receives a message relays the message to each of its peers, except the node which sent it to them
#. Nodes do not relay a message they have seen before

Using these principles you can create a messaging network which scales linearly with the number of nodes.

Currently there is an implementation in :doc:`Python <./python/mesh>` and :doc:`Javascript <./javascript/mesh>`. More tractable documentation can be found in their tutorial sections. For a more in-depth explanation you can see :doc:`it's specifications <./protocol/mesh>` or `this slideshow <http://slides.p2p.today/>`_.

Sync Table
~~~~~~~~~~

This is an extension of the above network. It inherits all of the message sending properties, while also syncronizing a local dictionary-like object.

The only limitation is that it can only have string-like keys and values. There is also an optional "leasing" system, which is enabled by default. This means that a user can own a particular key for a period of time.

Currently there is an implementation in :doc:`Python <./python/sync>` and :doc:`Javascript <./javascript/sync>`. More tractable documentation can be found in their tutorial sections. Protocol specifications are in progress.

Chord Table
~~~~~~~~~~~

This is a type of `distributed hash table <https://en.wikipedia.org/wiki/Distributed_hash_table>`_ based on an `MIT paper <https://pdos.csail.mit.edu/papers/chord:sigcomm01/chord_sigcomm.pdf>`_ which defined it.

The idea is that you can use this as a dictionary-like object. The only limitation is that it can only have string-like keys and values. It uses five separate hash tables for hash collision avoidance and data backup in case a node unexpectedly exits.

Currently there is an implementation in :doc:`Python <./python/chord>` and :doc:`Javascript <./javascript/chord>`. More tractable documentation can be found in their tutorial sections. Protocol specifications are in progress.

Contributing, Credits, and Licenses
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Contributors are always welcome! Information on how you can help is located on the :doc:`Contributing page <./CONTRIBUTING_LINK>`.

Credits and License are located on :doc:`their own page <./License>`.

Donate
~~~~~~

Bitcoin: `1BwVXxPj9JSEUoAx3HvcNjjJTHb2qsyjUr <https://blockchain.info/address/1BwVXxPj9JSEUoAx3HvcNjjJTHb2qsyjUr>`_

Previous Versions
~~~~~~~~~~~~~~~~~

- `0.4 <https://v0-4.p2p.today/>`_
- `0.5 <https://v0-5.p2p.today/>`_
- `develop <https://dev-docs.p2p.today/>`_
- `master <https://p2p.today/>`_

Contents
========

.. toctree::
    :maxdepth: 1

    protocol
    python
    javascript
    c
    cpp
    java
    go
    CONTRIBUTING_LINK
    License

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
