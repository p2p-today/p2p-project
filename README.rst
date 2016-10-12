.. |shippable| image:: https://img.shields.io/shippable/5750887b2a8192902e225466/develop.svg?maxAge=3600&label=Linux
    :target: https://app.shippable.com/projects/5750887b2a8192902e225466

.. |travis| image:: https://img.shields.io/travis/gappleto97/p2p-project/develop.svg?maxAge=3600&label=OSX
    :target: https://travis-ci.org/gappleto97/p2p-project

.. |appveyor| image:: https://img.shields.io/appveyor/ci/gappleto97/p2p-project/develop.svg?maxAge=3600&label=Windows
    :target: https://ci.appveyor.com/project/gappleto97/p2p-project

.. |codeclimate| image:: https://img.shields.io/codeclimate/github/gappleto97/p2p-project.svg?maxAge=3600
    :target: https://codeclimate.com/github/gappleto97/p2p-project

.. |codecov| image:: https://img.shields.io/codecov/c/github/gappleto97/p2p-project/develop.svg?maxAge=3600
    :target: https://codecov.io/gh/gappleto97/p2p-project

.. |waffleio_queued| image:: https://img.shields.io/waffle/label/gappleto97/p2p-project/queued.svg?maxAge=3600&labal=queued
    :target: https://waffle.io/gappleto97/p2p-project

.. |waffleio_in_progress| image:: https://img.shields.io/waffle/label/gappleto97/p2p-project/in%20progress.svg?maxAge=3600&labal=in%20progress
    :target: https://waffle.io/gappleto97/p2p-project

.. |waffleio_in_review| image:: https://img.shields.io/waffle/label/gappleto97/p2p-project/in%20review.svg?maxAge=3600&label=in%20review
    :target: https://waffle.io/gappleto97/p2p-project

To see a better formatted, more frequently updated version of this, please visit `docs.p2p.today <https://docs.p2p.today>`_, or for the develop branch, `dev-docs.p2p.today <https://dev-docs.p2p.today>`_.

Current build status:

|shippable| |travis| |appveyor| |codeclimate| |codecov|

|waffleio_queued| |waffleio_in_progress| |waffleio_in_review|

Compatability table:

+------------+------------+-------------+-------------+--------------+--------------------+-------------+-------------------+
|  Language  | Version    |                                           Feature                                               |
+------------+------------+-------------+-------------+--------------+--------------------+-------------+-------------------+
|            |            | Parser      | Compression | Mesh Network | Mesh Network (SSL) | Chord Table | Chord Table (SSL) |
+============+============+=============+=============+==============+====================+=============+===================+
| Python     | Python 2.7 | Yes         | Yes         | Yes          | Yes                | In Progress | In Progress       |
|            +------------+-------------+-------------+--------------+--------------------+-------------+-------------------+
|            | Python 3.3 | Yes         | Yes         | Yes          | Yes                | In Progress | In Progress       |
|            +------------+-------------+-------------+--------------+--------------------+-------------+-------------------+
|            | Python 3.4 | Yes         | Yes         | Yes          | Yes                | In Progress | In Progress       |
|            +------------+-------------+-------------+--------------+--------------------+-------------+-------------------+
|            | Python 3.5 | Yes         | Yes         | Yes          | Yes                | In Progress | In Progress       |
+------------+------------+-------------+-------------+--------------+--------------------+-------------+-------------------+
| Javascript | node.js 4  | Yes         | Yes         | In Progress  |                    |             |                   |
|            +------------+-------------+-------------+--------------+--------------------+-------------+-------------------+
|            | node.js 5  | Yes         | Yes         | In Progress  |                    |             |                   |
|            +------------+-------------+-------------+--------------+--------------------+-------------+-------------------+
|            | node.js 6  | Yes         | Yes         | In Progress  |                    |             |                   |
|            +------------+-------------+-------------+--------------+--------------------+-------------+-------------------+
|            | Chrome     | transpiled  | transpiled  |              |                    |             |                   |
|            +------------+-------------+-------------+--------------+--------------------+-------------+-------------------+
|            | Firefox    | transpiled  | transpiled  |              |                    |             |                   |
+------------+------------+-------------+-------------+--------------+--------------------+-------------+-------------------+
| C          |            | In Progress |             |              |                    |             |                   |
+------------+------------+-------------+-------------+--------------+--------------------+-------------+-------------------+
| C++        |            | Yes         |             |              |                    |             |                   |
+------------+------------+-------------+-------------+--------------+--------------------+-------------+-------------------+
| Java       |            | Yes         |             |              |                    |             |                   |
+------------+------------+-------------+-------------+--------------+--------------------+-------------+-------------------+
| Golang     |            | Yes         |             |              |                    |             |                   |
+------------+------------+-------------+-------------+--------------+--------------------+-------------+-------------------+

Goal
~~~~

We are trying to make peer-to-peer networking easy. Right now there's very few libraries which allow multiple languages to use the same distributed network.

We're aiming to fix that.

What We Have
~~~~~~~~~~~~

There are several projects in the work right now. Several of these could be considered stable, but we're going to operate under the "beta" label for some time now.

Message Serializer
~~~~~~~~~~~~~~~~~~

Serialization is the most important part for working with other languages. While there are several such schemes which work in most places, we made the decision to avoid these in general. We wanted something very lightweight, which could handle binary data, and operated as quickly as possible. This meant that "universal" serializers like JSON were out the window.

You can see more information about our serialization scheme in the `protocol documentation <./docs/protocol/serialization.rst>`_. We currently have a working parser in Python, Java, Javascript, C++, and Golang.

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

Currently there is an implementation in `Python <https:dev-docs.p2p.today/python/mesh>`_ and `Javascript <https:dev-docs.p2p.today/javascript/mesh>`. More tractable documentation can be found in their tutorial sections. For a more in-depth explanation you can see `it's specifications <https:dev-docs.p2p.today/protocol/mesh>`_ or `this slideshow <http://slides.p2p.today/>`_.

Chord Table
~~~~~~~~~~~

This is a type of `distributed hash table <https://en.wikipedia.org/wiki/Distributed_hash_table>`_ based on an `MIT paper <https://pdos.csail.mit.edu/papers/chord:sigcomm01/chord_sigcomm.pdf>`_ which defined it.

The idea is that you can use this as a dictionary-like object. The only caveat is that all keys and values *must* be strings. It uses five separate hash tables for hash collision avoidance and data backup in case a node unexpectedly exits.

Currently there is only an implementation in Python and it is highly experimental. This section will be updated when it's ready for more general use.

Contributing, Credits, and Licenses
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Contributors are always welcome! Information on how you can help is located on the `Contributing page <./CONTRIBUTING.rst>`_.

Credits and License are located on `their own page <./docs/License.rst>`_.
