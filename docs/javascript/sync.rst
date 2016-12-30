
Sync Module
===========

.. js:class:: js2p.sync.metatuple(owner, timestamp)

    This class is used to store metadata for a particular key

.. js:class:: js2p.sync.sync_socket(addr, port [, leasing [, protocol [, out_addr [, debug_level]]]])

    This is the class for mesh network socket abstraction. It inherits from :js:class:`js2p.mesh.mesh_socket`.
    Because of this inheritence, this can also be used as an alert network.

    This also implements and optional leasing system by default. This leasing system means that
    if node A sets a key, node B cannot overwrite the value at that key for an hour.

    This may be turned off by setting ``leasing`` to ``false`` to the constructor.

    :param string addr:                   The address you'd like to bind to
    :param number port:                   The port you'd like to bind to
    :param boolean leasing:               Whether this class's leasing system should be enabled (default: ``true``)
    :param js2p.base.protocol protocol:   The subnet you're looking to connect to
    :param array out_addr:                Your outward-facing address
    :param number debug_level:            The verbosity of debug prints

    .. js:function:: js2p.sync.sync_socket.__store(key, new_data, new_meta, error)

        Private API method for storing data

        :param key:        The key you wish to store data at
        :param new_data:   The data you wish to store in said key
        :param new_meta:   The metadata associated with this storage
        :param error:      A boolean which says whether to raise a :py:class:`KeyError` if you can't store there

        :raises Error: If someone else has a lease at this value, and ``error`` is not ``false``

    .. js:function:: js2p.sync.sync_socket._send_handshake_response(handler)

        Shortcut method to send a handshake response. This method is extracted from :js:func:`~js2p.mesh.mesh_socket.__handle_handshake`
        in order to allow cleaner inheritence from :js:class:`js2p.sync.sync_socket`


    .. js:function:: js2p.sync.sync_socket.__handle_store

        This callback is used to deal with data storage signals. Its two primary jobs are:

           - store data in a given key
           - delete data in a given key

           :param msg:        A :js:class:`~js2p.base.message`
           :param handler:    A :js:class:`~js2p.mesh.mesh_connection`

           :returns: Either ``true`` or ``undefined``

    .. js:function:: js2p.sync.sync_socket.get(key [, fallback])

        Retrieves the value at a given key

        :param key:       The key you wish to look up (must be transformable into a :js:class:`Buffer` )
        :param fallback:  The value it should return when the key has no data

        :returns: The value at the given key, or ``fallback``.

        :raises TypeError:    If the key could not be transformed into a :js:class:`Buffer`

    .. js:function:: js2p.sync.sync_socket.set(key, value)

        Sets the value at a given key

        :param key:   The key you wish to look up (must be transformable into a :js:class:`Buffer` )
        :param value: The key you wish to store (must be transformable into a :js:class:`Buffer` )

        :raises TypeError:    If a key or value could not be transformed into a :js:class:`Buffer`
        :raises:              See :js:func:`~js2p.sync.sync_socket.__store`

    .. js:function:: js2p.sync.sync_socket.update(update_dict)

        For each key/value pair in the given object, calls :js:func:`~js2p.sync.sync_socket.set`

        :param Object update_dict: An object with keys and values which can be transformed into a :js:class:`Buffer`

        :raises: See :js:func:`~js2p.sync.sync_socket.set`

    .. js:function:: js2p.sync.sync_socket.del(key)

        Clears the value at a given key

        :param key:   The key you wish to look up (must be transformable into a :js:class:`Buffer` )

        :raises TypeError:    If a key or value could not be transformed into a :js:class:`Buffer`
        :raises:              See :js:func:`~js2p.sync.sync_socket.set`

    .. js:function:: js2p.sync.sync_socket.keys()

        Returns a generator for all keys presently in the dictionary

        Because this data is changed asynchronously, the key is
        only garunteed to be present at the time of generation.

        :returns: A generator which yields :js:class:`Buffer`s

    .. js:function:: js2p.sync.sync_socket.values()

        Returns a generator for all values presently in the
        dictionary

        Because this data is changed asynchronously, the value is
        only garunteed to be accurate at the time of generation.

        :returns: A generator which yields :js:class:`Buffer`s

    .. js:function:: js2p.sync.sync_socket.items()

        Returns a generator for all associations presently in the
        dictionary

        Because this data is changed asynchronously, the association
        is only garunteed to be present at the time of generation.

        :returns: A generator which yields pairs of
                  :js:class:`Buffer`s

    .. js:function:: js2p.sync.sync_socket.pop(key [, fallback])

        Returns the value at a given key. As a side effect, it
        it deletes that key.

        :returns: A :js:class:`Buffer`

    .. js:function:: js2p.sync.sync_socket.popitem()

        Returns the association at a key. As a side effect, it
        it deletes that key.

        :returns: A pair of :js:class:`Buffer`s


