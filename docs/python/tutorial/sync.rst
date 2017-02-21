Sync Socket
~~~~~~~~~~~

This is an extension of the :doc:`MeshSocket <./mesh>` which syncronizes a common :py:class:`dict`. It works by providing an extra handler to store data. This exposes the entire :py:class:`dict` API.

.. note::

    This is a fairly inefficient architecture for write intensive applications. For cases where the majority of access is reading, or for small networks, this is ideal. For larger networks with infrequent access, you should use the :doc:`chord <./chord>` socket.

Basic Usage
-----------

There are three limitations compared to a normal :py:class:`dict`.

1. Keys can only be :py:class:`bytes`-like objects
2. Keys are automatically translated to :py:class:`bytes`
3. By default, this implements a leasing system which prevents you from changing values set by others for a certain time

You can override the last restriction by constructing with ``leasing=False``, like so:

.. code-block:: python

    >>> from py2p import sync
    >>> sock = sync.SyncSocket('0.0.0.0', 4444, leasing=False)

The only other API differences between this and :py:class:`~py2p.mesh.MeshSocket` are for access to this dictionary. They are as follows.

:py:meth:`~py2p.sync.SyncSocket.get` / :py:meth:`~py2p.sync.SyncSocket.__getitem__`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A value can be retrieved by using the :py:meth:`~py2p.sync.SyncSocket.get` method, or alternately with :py:meth:`~py2p.sync.SyncSocket.__getitem__`. These calls are both ``O(1)``, as they read from a local :py:class:`dict`.

.. code-block:: python

    >>> foo = sock.get('test key', None)        # Returns None if there is nothing at that key
    >>> bar = sock[b'test key']                 # Raises KeyError if there is nothing at that key
    >>> assert bar == foo == sock[u'test key']  # Because of the translation mentioned below, these are the same key

It is important to note that keys are all translated to :py:class:`bytes` before being used, so it is required that you use a :py:class:`bytes`-like object. It is also safer to manually convert :py:class:`unicode` keys to :py:class:`bytes`, as there are sometimes inconsistencies betwen the Javascript and Python implementation. If you notice one of these, please file a bug report.

:py:meth:`~py2p.sync.SyncSocket.set` / :py:meth:`~py2p.sync.SyncSocket.__setitem__`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A value can be stored by using the :py:meth:`~py2p.sync.SyncSocket.set` method, or alternately with :py:meth:`~py2p.chord.chord_socket.__setitem__`. These calls are worst case ``O(n)``, as it has to change values on other nodes. More accurately, the delay between your node knowing of the change and the last node knowing of the change is between ``O(log(n))`` and ``O(n)``.

.. code-block:: python

    >>> sock.set('test key', 'value')
    >>> sock[b'test key'] = b'value'
    >>> sock[u'测试'] = 'test'

Like above, keys and values are all translated to :py:class:`bytes` before being used, so it is required that you use a :py:class:`bytes`-like object.

This will raise a :py:class:`KeyError` if another node has set this value already. Their lease will expire one hour after they set it. If two leases are started at the same UTC second, the tie is settled by doing a string compare of their IDs.

Any node which sets a value can change this value as well. Changing the value renews the lease on it.

:py:meth:`~py2p.sync.SyncSocket.__delitem__`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Any node which owns a key, can clear its value. Doing this will relinquish your lease on that value. Like the above, this call is worst case ``O(n)``.

.. code-block:: python

    >>> del sock['test']

:py:meth:`~py2p.sync.SyncSocket.update`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The update method is simply a wrapper which updates based on a fed :py:class:`dict`. Essentially it runs the following:

.. code-block:: python

    >>> for key, value in update_dict.items():
    ...     sock[key] = value

:py:meth:`~py2p.sync.SyncSocket.keys` / :py:meth:`~py2p.sync.SyncSocket.values` / :py:meth:`~py2p.sync.SyncSocket.items`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These methods are analagous to the ones in Python's :py:class:`dict`. The main difference is that they emulate the Python 3 behavior. So if you call these from Python 2, they will still return an iterator, rather than a list.

:py:meth:`~py2p.sync.SyncSocket.pop` / :py:meth:`~py2p.sync.SyncSocket.popitem`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These methods are also analagous to the ones in Python's :py:class:`dict`. The main difference is that if the leasing system is active, calling this method may throw an error if you don't "own" whatever key is popped.

Events
------

In addition to the above, and those of :py:class:`~py2p.mesh.MeshSocket`, the :py:class:`~py2p.sync.SyncSocket` object has two Events.

First there's |SyncSocket_onupdate|_. This is called whenever an association is updated.

.. code-block:: python

    >>> @sock.on('update')
    >>> def handle_key_update(conn, key, new_data, meta):
    ...     # conn is a reference to the socket
    ...     print("An association was updated: {} -> {}".format(key, new_data))
    ...     print("This change was made by {} at unix time {}".format(meta.owner, meta.timestamp))
    ...

This class has one other event: |SyncSocket_ondelete|_. This is called every time an association is removed.

.. code-block:: python

    >>> @sock.on('delete')
    >>> def handle_deleted_key(conn, key):
    ...     # conn is a reference to the socket
    ...     print("A key was deleted: {}".format(key))
    ...

Advanced Usage
--------------

Refer to :doc:`the mesh socket tutorial <./mesh>`

.. |MeshSocket_onconnect| replace:: :py:func:`~py2p.mesh.MeshSocket.Event 'connect'`
.. _MeshSocket_onconnect: ../mesh.html#MeshSocket.Event%20'connect'

.. |MeshSocket_onmessage| replace:: :py:func:`~py2p.mesh.MeshSocket.Event 'message'`
.. _MeshSocket_onmessage: ../mesh.html#MeshSocket.Event%20'message'

.. |SyncSocket_onupdate| replace:: :py:func:`~py2p.sync.SyncSocket.Event 'update'`
.. _SyncSocket_onupdate: ../sync.html#SyncSocket.Event%20'update'

.. |SyncSocket_ondelete| replace:: :py:func:`~py2p.sync.SyncSocket.Event 'delete'`
.. _SyncSocket_ondelete: ../sync.html#SyncSocket.Event%20'delete'
