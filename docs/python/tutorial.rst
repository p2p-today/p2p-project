Tutorial
========

Mesh Socket
~~~~~~~~~~~

Basic Usage
-----------

The mesh schema is used as an alert and messaging network. Its primary purpose is to ensure message delivery to every participant in the network.

To connect to a mesh network, use the :py:class:`~py2p.mesh.mesh_socket` object. this is instantiated as follows:

.. code-block:: python

    >>> from py2p import mesh
    >>> sock = mesh.mesh_socket('0.0.0.0', 4444)

Using ``'0.0.0.0'`` will automatically grab your LAN address. Using an outbound internet connection requires a little more work. First, ensure that you have a port forward set up (NAT busting is not in the scope of this project). Then specify your outward address as follows:

.. code-block:: python

    >>> from py2p import mesh
    >>> sock = mesh.mesh_socket('0.0.0.0', 4444, out_addr=('35.24.77.21', 44565))

In addition, SSL encryption can be enabled if `cryptography <https://cryptography.io/en/latest/installation/>`_ is installed. This works by specifying a custom :py:class:`~py2p.base.protocol` object, like so:

.. code-block:: python

    >>> from py2p import mesh, base
    >>> sock = mesh.mesh_socket('0.0.0.0', 4444, prot=base.protocol('mesh', 'SSL'))

Eventually that will be the default, but while things are being tested it will default to plaintext. If `cryptography <https://cryptography.io/en/latest/installation/>`_ is not installed, this will generate an :py:exc:`ImportError`

Specifying a different protocol object will ensure that the node *only* can connect to people who share its object structure. So if someone has ``'mesh2'`` instead of ``'mesh'``, it will fail to connect. You can see the current default by looking at :py:data:`py2p.mesh.default_protocol`.

Unfortunately, this failure is currently silent. Because this is asynchronous in nature, raising an :py:exc:`Exception` is not possible. Because of this, it's good to perform the following check after connecting:

.. code-block:: python

    >>> from py2p import mesh
    >>> import time
    >>> sock = mesh.mesh_socket('0.0.0.0', 4444)
    >>> sock.connect('192.168.1.14', 4567)
    >>> time.sleep(1)
    >>> assert sock.routing_table

To send a message, use the :py:meth:`~py2p.mesh.mesh_socket.send` method. Each argument supplied will correspond to a packet that the peer receives. In addition, there are two keyed arguments you can use. ``flag`` will specify how other nodes relay this. These flags are defined in :py:class:`py2p.base.flags` . ``broadcast`` will indicate that other nodes are supposed to relay it. ``whisper`` will indicate that your peers are *not* supposed to relay it. ``type`` will specify what actions other nodes are supposed to take on it. It defaults to ``broadcast``, which indicates no change from the norm.

.. code-block:: python

    >>> sock.send('this is', 'a test')

Receiving is a bit simpler. When the :py:meth:`~py2p.mesh.mesh_socket.recv` method is called, it returns a :py:class:`~py2p.base.message` object (or ``None`` if there are no messages). This has a number of methods outlined which you can find by clicking its name. Most notably, you can get the packets in a message with :py:attr:`.message.packets`, and reply directly with :py:meth:`.message.reply`.

.. code-block:: python

    >>> sock.send('Did you get this?')  # A peer then replies
    >>> msg = sock.recv()
    >>> print(msg)
    message(type=b'whisper', packets=[b'yes', b'I did'], sender=b'6VnYj9LjoVLTvU3uPhy4nxm6yv2wEvhaRtGHeV9wwFngWGGqKAzuZ8jK6gFuvq737V')
    >>> print(msg.packets)
    [b'whisper', b'yes', b'I did']
    >>> for msg in sock.recv(10):
    ...     msg.reply("Replying to a list")

Advanced Usage
--------------

In addition to this, you can register a custom handler for incoming messages. This is appended to the end of the default handlers. These handlers are then called in a similar way to Javascripts ``Array.some()``. In other words, when a handler returns something true-like, it stops calling handlers.

When writing your handler, keep in mind that you are only passed a :py:class:`~py2p.base.message` object and a :py:class:`~py2p.mesh.mesh_connection`. Fortunately you can get access to everything you need from these objects.

.. code-block:: python

    >>> from py2p import mesh, base
    >>> def register_1(msg, handler):   # Takes in a message and mesh_connection
    ...     packets = msg.packets       # This grabs a copy of the packets. Slightly more efficient to store this once.
    ...     if packets[1] == b'test':   # This is the condition we want to act under
    ...         msg.reply(b"success")   # This is the response we should give
    ...         return True             # This tells the daemon we took an action, so it should stop calling handlers
    ...
    >>> def register_2(msg, handler):   # This is a slightly different syntax
    ...     packets = msg.packets
    ...     if packets[1] == b'test':
    ...         handler.send(base.flags.whisper, base.flags.whisper, b"success")  # One could instead reply to the node who relayed the message
    ...         return True
    ...
    >>> sock = mesh.mesh_socket('0.0.0.0', 4444)
    >>> sock.register_handler(register_1)  # The handler is now registered

If this does not take two arguments, :py:meth:`~py2p.base.base_socket.register_handler` will raise a :py:exc:`ValueError`.

To help debug these services, you can specify a :py:attr:`~py2p.base.base_socket.debug_level` in the constructor. Using a value of 5, you can see when it enters into each handler, as well as every message which goes in or out.

Sync Socket
~~~~~~~~~~~

This is an extension of the :py:class:`~py2p.mesh.mesh_socket` which syncronizes a common :py:class:`dict`. It works by providing an extra handler to store data. This does not expose the entire :py:class:`dict` API, but it exposes a substantial subset, and we're working to expose more.

Basic Usage
-----------

There are three limitations compared to a normal :py:class:`dict`.

1. Keys and values can only be :py:class:`bytes`-like objects
2. Keys and values are automatically translated to :py:class:`bytes`
3. A leasing system prevents you from changing values set by others

The only API differences between this and :py:class:`~py2p.mesh.mesh_socket` are for access to this dictionary. They are as follows.

:py:meth:`~py2p.sync.sync_socket.get` / :py:meth:`~py2p.sync.sync_socket.__getitem__`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A value can be retrieved by using the :py:meth:`~py2p.sync.sync_socket.get` method, or alternately with :py:meth:`~py2p.sync.sync_socket.__getitem__`. These calls are both ``O(n)``, as they read from local variables.

.. code-block:: python

    >>> foo = sock.get('test key', None)        # Returns None if there is nothing at that key
    >>> bar = sock[b'test key']                 # Raises KeyError if there is nothing at that key
    >>> assert bar == foo == sock[u'test key']  # Because of the translation mentioned below, these are the same key

It is important to note that keys are all translated to :py:class:`bytes` before being used, so it is required that you use a :py:class:`bytes`-like object. It is also safer to manually convert :py:class:`unicode` keys to :py:class:`bytes`, as there are sometimes inconsistencies betwen the Javascript and Python implementation. If you notice one of these, please file a bug report.

:py:meth:`~py2p.sync.sync_socket.set` / :py:meth:`~py2p.sync.sync_socket.__setitem__`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A value can be stored by using the :py:meth:`~py2p.sync.sync_socket.set` method, or alternately with :py:meth:`~py2p.chord.chord_socket.__setitem__`.

.. code-block:: python

    >>> sock.set('test key', 'value')
    >>> sock[b'test key'] = b'value'

Like above, keys and values are all translated to :py:class:`bytes` before being used, so it is required that you use a :py:class:`bytes`-like object.

This will raise a :py:class:`KeyError` if another node has set this value already. Their lease will expire one hour after they set it. If two leases are started at the same UTC second, the tie is settled by doing a string compare of their IDs.

Any node which sets a value can change this value as well. Changing the value renews the lease on it.

:py:meth:`~py2p.sync.sync_socket.__delitem__`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Any node which owns a key, can clear its value. Doing this will relinquish your lease on that value.

.. code-block:: python

    >>> del sock['test']

:py:meth:`~py2p.sync.sync_socket.update`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The update method is simply a wrapper which updates based on a fed :py:class:`dict`. Essentially it runs the following:

.. code-block:: python

    >>> for key in update_dict:
    ...     sock[key] = update_dict[key]

Advanced Usage
--------------

Refer to `Mesh Socket: Advanced Usage <#advanced-usage>`_


Chord Socket
~~~~~~~~~~~~

.. warning::

    This module is partly unstable, and should be regarded as "pre-alpha".

    If you're considering using this, please wait until this warning is removed. Expected beta status is by end of November 2016.

Basic Usage
-----------

The chord schema is used as a distributed hash table. Its primary purpose is to ensure data syncronization between peers. While it's not entirely :py:class:`dict`-like, it has a substantial subset of this API.

To connect to a chord network, use the :py:class:`~py2p.chord.chord_socket` object. this is instantiated as follows:

.. code-block:: python

    >>> from py2p import chord
    >>> sock = chord.chord_socket('0.0.0.0', 4444, k=2)
    >>> sock.join()  # This indicates you want to store data

There are two arguments to explain here.

The keyword ``k`` specifies the maximum number of seeding nodes on the network. In other words, for a given ``k``, you can have up to ``2**k`` nodes storing data, and as few as ``k``. ``k`` is also the maximum number of requests you can expect to issue for a given piece of data. So lookup time will be ``O(k)``.

And like in :py:class:`~py2p.mesh.mesh_socket`, using ``'0.0.0.0'`` will automatically grab your LAN address. Using an outbound internet connection requires a little more work. First, ensure that you have a port forward set up (NAT busting is not in the scope of this project). Then specify your outward address as follows:

.. code-block:: python

    >>> from py2p import chord
    >>> sock = chord.chord_socket('0.0.0.0', 4444, k=2 out_addr=('35.24.77.21', 44565))
    >>> sock.join()  # This indicates you want to store data

In addition, SSL encryption can be enabled if `cryptography <https://cryptography.io/en/latest/installation/>`_ is installed. This works by specifying a custom :py:class:`~py2p.base.protocol` object, like so:

.. code-block:: python

    >>> from py2p import chord, base
    >>> sock = chord.chord_socket('0.0.0.0', 4444, k=2, prot=base.protocol('chord', 'SSL'))

Eventually that will be the default, but while things are being tested it will default to plaintext. If `cryptography <https://cryptography.io/en/latest/installation/>`_ is not installed, this will generate an :py:exc:`ImportError`

Specifying a different protocol object will ensure that the node *only* can connect to people who share its object structure. So if someone has ``'chord2'`` instead of ``'chord'``, it will fail to connect. You can see the current default by looking at :py:data:`py2p.chord.default_protocol`.

This same check is performed for the ``k`` value provided. The full check which happens is essentially:

.. code-block:: python

    assert your_protocol.id + to_base_58(your_k) == peer_protocol.id + to_base_58(peer_k)

Unfortunately, this failure is currently silent. Because this is asynchronous in nature, raising an :py:exc:`Exception` is not possible. Because of this, it's good to perform the following check after connecting:

.. code-block:: python

    >>> from py2p import chord
    >>> import time
    >>> sock = chord.chord_socket('0.0.0.0', 4444, k=2)
    >>> sock.connect('192.168.1.14', 4567)
    >>> time.sleep(1)
    >>> assert sock.routing_table or sock.awaiting_ids

Using the constructed table is very easy. Several :py:class:`dict`-like methods have been implemented.

:py:meth:`~py2p.chord.chord_socket.get`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A value can be retrieved by using the :py:meth:`~py2p.chord.chord_socket.get` method, or alternately with :py:meth:`~py2p.chord.chord_socket.__getitem__`.

.. code-block:: python

    >>> foo = sock.get('test key', None)  # Returns None if there is nothing at that key
    >>> bar = sock[b'test key']           # Raises KeyError if there is nothing at that key

It is important to note that keys are all translated to :py:class:`bytes` before being used, so it is required that you use a :py:class:`bytes`-like object. It is also safer to manually convert :py:class:`unicode` keys to :py:class:`bytes`, as there are sometimes inconsistencies betwen the Javascript and Python implementation. If you notice one of these, please file a bug report.

:py:meth:`~py2p.chord.chord_socket.set`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A value can be stored by using the :py:meth:`~py2p.chord.chord_socket.set` method, or alternately with :py:meth:`~py2p.chord.chord_socket.__setitem__`.

.. code-block:: python

    >>> sock.set('test key', 'value')
    >>> sock[b'test key'] = b'value'

Like above, keys and values are all translated to :py:class:`bytes` before being used, so it is required that you use a :py:class:`bytes`-like object.

:py:meth:`~py2p.chord.chord_socket.update`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The update method is simply a wrapper which updates based on a fed :py:class:`dict`. Essentially it runs the following:

.. code-block:: python

    >>> for key in update_dict:
    ...     sock[key] = update_dict[key]

Advanced Usage
--------------

Refer to `Mesh Socket: Advanced Usage <#advanced-usage>`_
