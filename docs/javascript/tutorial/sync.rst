Sync Socket
~~~~~~~~~~~

This is an extension of the :js:class:`~js2p.mesh.mesh_socket` which syncronizes a common :js:class:`Object`. It works by providing an extra handler to store data. This does not expose the entire :js:class:`Object` API, but it exposes a substantial subset, and we're working to expose more.

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

The only API differences between this and :js:class:`~js2p.mesh.mesh_socket` are for access to this dictionary. They are as follows.

:js:func:`~js2p.sync.sync_socket.get`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A value can be retrieved by using the :js:func:`~js2p.sync.sync_socket.get` method. This is reading from a local :js:class:`Object`, so speed shouldn't be a factor.

.. code-block:: javascript

    > let foo = sock.get('test key', null)  // Returns null if there is nothing at that key
    > let bar = sock.get('test key')        // Returns undefined if there is nothing at that key

It is important to note that keys are all translated to a :js:class:`Buffer` before being used.

:js:func:`~js2p.sync.sync_socket.set`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A value can be stored by using the :js:func:`~js2p.sync.sync_socket.set` method. These calls are ``O(n)``, as it has to change values on other nodes. More accurately, the delay between your node knowing of the change and the last node knowing of the change is ``O(n)``.

.. code-block:: javascript

    > sock.set('test key', 'value');
    > sock.set('测试', 'test');

Like above, keys and values are all translated to :js:class:`Buffer` before being used

This will raise an :js:class:`Error` if another node has set this value already. Their lease will expire one hour after they set it. If two leases are started at the same UTC second, the tie is settled by doing a string compare of their IDs.

Any node which sets a value can change this value as well. Changing the value renews the lease on it.

:js:func:`~js2p.sync.sync_socket.del`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Any node which owns a key, can clear its value. Doing this will relinquish your lease on that value. Like the above, this call is ``O(n)``.

.. code-block:: javascript

    > sock.del('test');

:js:func:`~js2p.sync.sync_socket.update`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The update method is simply a wrapper which updates based on a fed :js:class:`Object`. Essentially it runs the following:

.. code-block:: javascript

    > for (var key in update_dict)  {
    ... sock.set(key, update_dict[key]);
    ... }

Advanced Usage
--------------

Refer to :doc:`the mesh socket tutorial <./mesh>`
