Chord Socket
~~~~~~~~~~~~

This is an extension of the :doc:`mesh_socket <./mesh>` which syncronizes a common :py:class:`dict`. It works by providing some extra handlers to store data. This exposes the entire :py:class:`dict` API.

.. note::

    This is a fairly inefficient architecture for read intensive applications. For large databases which are infrequently changed, this is ideal. For smaller networks where there is significant access required, you should use the :doc:`sync <./sync>` socket.

Basic Usage
-----------

There are three limitations compared to a normal :py:class:`dict`.

1. Keys and values can only be :py:class:`bytes`-like objects
2. Keys and values are automatically translated to :py:class:`bytes`
3. Fetching values is significantly slower than for a :py:class:`dict`

The only API differences between this and :py:class:`~py2p.mesh.mesh_socket` are for access to this dictionary. They are as follows.

:py:meth:`~py2p.chord.chord_socket.get` / :py:meth:`~py2p.chord.chord_socket.__getitem__`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A value can be retrieved by using the :py:meth:`~py2p.chord.chord_socket.get` method, or alternately with :py:meth:`~py2p.chord.chord_socket.__getitem__`. These calls are about ``O(log(n))`` hops, as they approximately halve their search area with each hop.

.. code-block:: python

    >>> foo = sock.get('test key', None)        # Returns None if there is nothing at that key
    >>> bar = sock[b'test key']                 # Raises KeyError if there is nothing at that key
    >>> assert bar == foo == sock[u'test key']  # Because of the translation mentioned below, these are the same key

It is important to note that keys are all translated to :py:class:`bytes` before being used, so it is required that you use a :py:class:`bytes`-like object. It is also safer to manually convert :py:class:`unicode` keys to :py:class:`bytes`, as there are sometimes inconsistencies betwen the Javascript and Python implementation. If you notice one of these, please file a bug report.

:py:meth:`~py2p.chord.chord_socket.set` / :py:meth:`~py2p.chord.chord_socket.__setitem__`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A value can be stored by using the :py:meth:`~py2p.chord.chord_socket.set` method, or alternately with :py:meth:`~py2p.chord.chord_socket.__setitem__`. Like the above, these calls are about ``O(log(n))`` hops, as they approximately halve their search area with each hop.

.. code-block:: python

    >>> sock.set('test key', 'value')
    >>> sock[b'test key'] = b'value'
    >>> sock[u'测试'] = 'test'

Like above, keys and values are all translated to :py:class:`bytes` before being used, so it is required that you use a :py:class:`bytes`-like object.

:py:meth:`~py2p.chord.chord_socket.__delitem__`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This deletes an association. Like the above, this call is about ``O(log(n))``.

.. code-block:: python

    >>> del sock['test']

:py:meth:`~py2p.chord.chord_socket.update`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The update method is simply a wrapper which updates based on a fed :py:class:`dict`. Essentially it runs the following:

.. code-block:: python

    >>> for key, value in update_dict.items():
    ...     sock[key] = value

:py:meth:`~py2p.chord.chord_socket.keys` / :py:meth:`~py2p.chord.chord_socket.values` / :py:meth:`~py2p.chord.chord_socket.items`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These methods are analagous to the ones in Python's :py:class:`dict`. The main difference is that they emulate the Python 3 behavior. So if you call these from Python 2, they will still return an iterator, rather than a list.

In addition, you should always surround :py:meth:`~py2p.chord.chord_socket.values` and :py:meth:`~py2p.chord.chord_socket.items` in a try-catch for :py:class:`KeyError` and :py:class:`socket.error`. Because the data is almost always stored on other nodes, you cannot guaruntee that an item in :py:meth:`~py2p.chord.chord_socket.keys` is retrievable.

:py:meth:`~py2p.chord.chord_socket.pop` / :py:meth:`~py2p.chord.chord_socket.popitem`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These methods are also analagous to the ones in Python's :py:class:`dict`. The main difference is that, like the above, you should always surround these in a try-catch for :py:class:`KeyError` and :py:class:`socket.error`.

Advanced Usage
--------------

Refer to :doc:`the mesh socket tutorial <./mesh>`
