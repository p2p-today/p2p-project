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

Refer to :doc:`the mesh socket tutorial <./mesh>`
