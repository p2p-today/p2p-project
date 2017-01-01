To see a better formatted, more frequently updated version of this, please visit [docs.p2p.today](https://docs.p2p.today), or for the develop branch, [dev-docs.p2p.today](https://dev-docs.p2p.today).

Current build status:

[![shippable](https://img.shields.io/shippable/5750887b2a8192902e225466/develop.svg?maxAge=3600&label=Linux)](https://app.shippable.com/projects/5750887b2a8192902e225466) [![travis](https://img.shields.io/travis/p2p-today/p2p-project/develop.svg?maxAge=3600&label=OSX)](https://travis-ci.org/p2p-today/p2p-project) [![appveyor](https://img.shields.io/appveyor/ci/gappleto97/p2p-project-fowii/develop.svg?maxAge=3600&label=Windows)](https://ci.appveyor.com/project/gappleto97/p2p-project-fowii) [![codeclimate](https://img.shields.io/codeclimate/github/gappleto97/p2p-project.svg?maxAge=3600)](https://codeclimate.com/github/gappleto97/p2p-project) [![codecov](https://img.shields.io/codecov/c/github/gappleto97/p2p-project/develop.svg?maxAge=3600)](https://codecov.io/gh/gappleto97/p2p-project)

[![waffleio\_queued](https://img.shields.io/waffle/label/p2p-today/p2p-project/queued.svg?maxAge=3600&labal=queued)](https://waffle.io/p2p-today/p2p-project) [![waffleio\_in\_progress](https://img.shields.io/waffle/label/p2p-today/p2p-project/in%20progress.svg?maxAge=3600&labal=in%20progress)](https://waffle.io/p2p-today/p2p-project) [![waffleio\_in\_review](https://img.shields.io/waffle/label/p2p-today/p2p-project/in%20review.svg?maxAge=3600&label=in%20review)](https://waffle.io/p2p-today/p2p-project)

Goal
====

We are trying to make peer-to-peer networking easy. Right now there's very few libraries which allow multiple languages to use the same distributed network.

We're aiming to fix that.

What We Have
============

There are several projects in the work right now. Several of these could be considered stable, but we're going to operate under the "beta" label for some time now.

Message Serializer
==================

Serialization is the most important part for working with other languages. While there are several such schemes which work in most places, we made the decision to avoid these in general. We wanted something very lightweight, which could handle binary data, and operated as quickly as possible. This meant that "universal" serializers like JSON were out the window.

You can see more information about our serialization scheme in the [protocol documentation](./docs/protocol/serialization.rst). We currently have a working parser in Python, Java, Javascript, C++, and Golang.

Base Network Structures
=======================

All of our networks will be built on common base classes. Because of this, we can guarantee some network features.

1.  Networks will have as much common codebase as possible
2.  Networks will have opportunistic compression across the board
3.  Node IDs will be generated in a consistent manner
4.  Command codes will be consistent across network types

Mesh Network
============

This is our unorganized network. It operates under three simple rules:

1.  The first node to broadcast sends the message to all its peers
2.  Each node which receives a message relays the message to each of its peers, except the node which sent it to them
3.  Nodes do not relay a message they have seen before

Using these principles you can create a messaging network which scales linearly with the number of nodes.

Currently there is an implementation in [Python](https:dev-docs.p2p.today/python/mesh) and Javascript &lt;https:dev-docs.p2p.today/javascript/mesh&gt;. More tractable documentation can be found in their tutorial sections. For a more in-depth explanation you can see [it's specifications](https:dev-docs.p2p.today/protocol/mesh) or [this slideshow](http://slides.p2p.today/).

Sync Table
==========

This is an extension of the above network. It inherits all of the message sending properties, while also syncronizing a local dictionary-like object.

The only limitation is that it can only have string-like keys and values. There is also an optional "leasing" system, which is enabled by default. This means that a user can own a particular key for a period of time.

Currently there is an implementation in [Python](https://dev-docs.p2p.today/python/sync) and [Javascript](https://dev-docs.p2p.today/javascript/sync). More tractable documentation can be found in their tutorial sections. Protocol specifications are in progress.

Chord Table
===========

This is a type of [distributed hash table](https://en.wikipedia.org/wiki/Distributed_hash_table) based on an [MIT paper](https://pdos.csail.mit.edu/papers/chord:sigcomm01/chord_sigcomm.pdf) which defined it.

The idea is that you can use this as a dictionary-like object. The only caveat is that all keys and values *must* be strings. It uses five separate hash tables for hash collision avoidance and data backup in case a node unexpectedly exits.

Currently there is only an implementation in Python and it is highly experimental. This section will be updated when it's ready for more general use.

Contributing, Credits, and Licenses
===================================

Contributors are always welcome! Information on how you can help is located on the [Contributing page](./CONTRIBUTING.rst).

Credits and License are located on [their own page](./docs/License.rst).

Donate
======

Bitcoin: [1BwVXxPj9JSEUoAx3HvcNjjJTHb2qsyjUr](https://blockchain.info/address/1BwVXxPj9JSEUoAx3HvcNjjJTHb2qsyjUr)
