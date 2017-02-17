Sync Socket
~~~~~~~~~~~

This is an extension of the :doc:`mesh_socket <./mesh>` which syncronizes a common :js:class:`Object`. It works by providing an extra handler to store data. This exposes the entire :py:class:`dict` API.

.. note::

    This is a fairly inefficient architecture for write intensive applications. For cases where the majority of access is reading, or for small networks, this is ideal. For larger networks where a significant portion of your operations are writing values, you should wait for the chord socket to come into beta.

Basic Usage
-----------

There are three limitations compared to a normal :js:class:`Object`.

1. Keys and values must be translatable to a :js:class:`Buffer`
2. Keys and values are automatically translated to a :js:class:`Buffer`
3. By default, this implements a leasing system which prevents you from changing values set by others for a certain time

You can override the last restriction by constructing with ``leasing`` set to ``false``, like so:

.. code-block:: javascript

    > const sync = require('js2p').sync;
    > let sock = new sync.sync_socket('0.0.0.0', 4444, false);

Note that the ``leasing`` parameter is supplied *before* a :js:class:`~js2p.base.protocol`.

The only other API differences between this and :js:class:`~js2p.mesh.mesh_socket` are for access to this dictionary. They are as follows:

:js:func:`~js2p.sync.sync_socket.get`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A value can be retrieved by using the :js:func:`~js2p.sync.sync_socket.get` method. This is reading from a local :js:class:`Object`, so speed shouldn't be a factor.

.. code-block:: javascript

    > let foo = sock.get('test key', null)  // Returns null if there is nothing at that key
    > let bar = sock.get('test key')        // Returns undefined if there is nothing at that key

It is important to note that keys are all translated to a :js:class:`Buffer` before being used.

:js:func:`~js2p.sync.sync_socket.set`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A value can be stored by using the :js:func:`~js2p.sync.sync_socket.set` method. These calls are worst case ``O(n)``, as it has to change values on other nodes. More accurately, the delay between your node knowing of the change and the last node knowing of the change is between ``O(log(n))`` and ``O(n)``.

.. code-block:: javascript

    > sock.set('test key', 'value');
    > sock.set('测试', 'test');

Like above, keys and values are all translated to :js:class:`Buffer` before being used

This will raise an :js:class:`Error` if another node has set this value already. Their lease will expire one hour after they set it. If two leases are started at the same UTC second, the tie is settled by doing a string compare of their IDs.

Any node which sets a value can change this value as well. Changing the value renews the lease on it.

:js:func:`~js2p.sync.sync_socket.del`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Any node which owns a key, can clear its value. Doing this will relinquish your lease on that value. Like the above, this call is worst case ``O(n)``.

.. code-block:: javascript

    > sock.del('test');

:js:func:`~js2p.sync.sync_socket.update`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The update method is simply a wrapper which updates based on a fed :js:class:`Object`. Essentially it runs the following:

.. code-block:: javascript

    > for (var key of update_dict)  {
    ... sock.set(key, update_dict[key]);
    ... }

:js:func:`~js2p.sync.sync_socket.keys` / :js:func:`~js2p.sync.sync_socket.values` / :js:func:`~js2p.sync.sync_socket.items`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These methods are analagous to the ones in Python's :py:class:`dict`. The main difference is that they emulate the Python 3 behavior. So, they will still return an generator, rather than a list.

:js:func:`~js2p.sync.sync_socket.pop` / :js:func:`~js2p.sync.sync_socket.popitem`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These methods are also analagous to the ones in Python's :py:class:`dict`. The main difference is that if the leasing system is active, calling this method may throw an error if you don't "own" whatever key is popped.

Events
------

In addition to the above, and those of :js:class:`~js2p.mesh.mesh_socket`, the :js:class:`~js2p.sync.sync_socket` object has two :js:class:`Event` s.

First there's :js:func:`~js2p.sync.sync_socket Event 'update'`. This is called whenever an association is updated.

.. code-block:: javascript

    > sock.on('update', (conn, key, new_data, meta)=>{
    ... // conn is a reference to the socket
    ... console.log(`${key} was updated to have value ${new_data}`);
    ... console.log(`This change was made by ${meta.owner} at unix time ${meta.timestamp}`);
    ... });

This class has one other event: :js:func:`~js2p.sync.sync_socket Event 'delete'`. This is called every time an association is removed.

.. code-block:: javascript

    > sock.on('delete', (conn, key)=>{
    ... console.log(`The association with key ${key} was deleted`);
    ... });

Advanced Usage
--------------

Refer to :doc:`the mesh socket tutorial <./mesh>`

Use In A Browser
----------------

Refer to :doc:`the mesh socket tutorial <./mesh>`
