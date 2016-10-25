/**
* Sync Module
* ===========
*/

"use strict";

const base = require('./base.js');
const mesh = require('./mesh.js');

var m;

if( typeof exports !== 'undefined' ) {
    if( typeof module !== 'undefined' && module.exports ) {
        m = exports = module.exports;
    }
    m = exports;
}
else {
    root.sync = {};
    m = root;
}

m.default_protocol = new base.protocol('sync', 'Plaintext');

m.metatuple = class metatuple   {
    /**
    * .. js:class:: js2p.sync.metatuple(owner, timestamp)
    *
    *     This class is used to store metadata for a particular key
    */
    constructor(owner, timestamp)   {
        this.owner = owner;
        this.timestamp = timestamp;
    }
}

m.sync_socket = class sync_socket extends mesh.mesh_socket  {
    /**
    * .. js:class:: js2p.sync.sync_socket(addr, port [, leasing [, protocol [, out_addr [, debug_level]]]])
    *
    *     This is the class for mesh network socket abstraction. It inherits from :js:class:`js2p.mesh.mesh_socket`.
    *     Because of this inheritence, this can also be used as an alert network.
    *
    *     This also implements and optional leasing system by default. This leasing system means that
    *     if node A sets a key, node B cannot overwrite the value at that key for an hour.
    *
    *     This may be turned off by setting ``leasing`` to ``false`` to the constructor.
    *
    *     :param string addr:                   The address you'd like to bind to
    *     :param number port:                   The port you'd like to bind to
    *     :param boolean leasing:               Whether this class's leasing system should be enabled (default: ``true``)
    *     :param js2p.base.protocol protocol:   The subnet you're looking to connect to
    *     :param array out_addr:                Your outward-facing address
    *     :param number debug_level:            The verbosity of debug prints
    */
    constructor(addr, port, leasing, protocol, out_addr, debug_level)   {
        if (!protocol)  {
            protocol = m.default_protocol;
        }
        let lease_descriptor = (leasing !== false) ? '1' : '0';
        let protocol_used = new base.protocol(protocol.subnet + lease_descriptor, protocol.encryption);
        super(addr, port, protocol_used, out_addr, debug_level);
        this.data = {};
        this.metadata = {};
        const self = this;
        this.register_handler(function handle_store(msg, conn)  {return self.__handle_store(msg, conn);});
    }

    __store(key, new_data, new_meta, error)   {
        /**
        *     .. js:function:: js2p.sync.sync_socket.__store(key, new_data, new_meta, error)
        *
        *         Private API method for storing data
        *
        *         :param key:        The key you wish to store data at
        *         :param new_data:   The data you wish to store in said key
        *         :param new_meta:   The metadata associated with this storage
        *         :param error:      A boolean which says whether to raise a :py:class:`KeyError` if you can't store there
        *
        *         :raises Error: If someone else has a lease at this value, and ``error`` is not ``false``
        */
        let meta = this.metadata[key];
        if ( (!meta) || (!this.__leasing) || (meta.owner == new_meta.owner) ||
                (meta.timestamp > new_meta.timestamp) || (meta.timestamp < base.getUTC() - 3600) ||
                (meta.timestamp == new_meta.timestamp && meta.owner > new_meta.owner) )    {
            if (new_data !== new Buffer(''))    {
                this.metadata[key] = new_meta;
                this.data[key] = new_data;
            }
            else    {
                delete this.data[key];
                delete this.metadata[key];
            }
        }
        else if (error !== false) {
            throw new Error("You don't have permission to change this yet");
        }
    }

    _send_handshake_response(handler) {
        /**
        *     .. js:function:: js2p.sync.sync_socket._send_handshake_response(handler)
        *
        *         Shortcut method to send a handshake response. This method is extracted from :js:func:`~js2p.mesh.mesh_socket.__handle_handshake`
        *         in order to allow cleaner inheritence from :js:class:`js2p.sync.sync_socket`
        *
        */
        super._send_handshake_response(handler)
        for (var key in this.data)  {
            let meta = this.metadata[key];
            handler.send(base.flags.whisper, [base.flags.store, key, this.data[key], meta.owner, base.to_base_58(meta.timestamp)]);
        }
    }

    __handle_store(msg, handler)  {
        /**
        *     .. js:function:: js2p.sync.sync_socket.__handle_store
        *
        *         This callback is used to deal with data storage signals. Its two primary jobs are:
        *
        *            - store data in a given key
        *            - delete data in a given key
        *
        *            :param msg:        A :js:class:`~js2p.base.message`
        *            :param handler:    A :js:class:`~js2p.mesh.mesh_connection`
        *
        *            :returns: Either ``true`` or ``undefined``
        */
        const packets = msg.packets;
        if (packets[0].toString() === base.flags.store) {
            let meta = new m.metatuple(msg.sender, msg.time);
            if (packets.length === 5)   {
                if (this.data[packets[1]])  {
                    return;
                }
                meta = new m.metatuple(packets[3], base.from_base_58(packets[4]));
            }
            this.__store(packets[1], packets[2], meta, false);
            return true;
        }
    }

    get(key, fallback)  {
        /**
        *     .. js:function:: js2p.sync.sync_socket.get(key [, fallback])
        *
        *         Retrieves the value at a given key
        *
        *         :param key:       The key you wish to look up (must be transformable into a :js:class:`Buffer` )
        *         :param fallback:  The value it should return when the key has no data
        *
        *         :returns: The value at the given key, or ``fallback``.
        *
        *         :raises TypeError:    If the key could not be transformed into a :js:class:`Buffer`
        */
        let l_key = new Buffer(key);
        return this.data[l_key] || fallback;
    }

    set(key, data) {
        /**
        *     .. js:function:: js2p.sync.sync_socket.set(key, value)
        *
        *         Sets the value at a given key
        *
        *         :param key:   The key you wish to look up (must be transformable into a :js:class:`Buffer` )
        *         :param value: The key you wish to store (must be transformable into a :js:class:`Buffer` )
        *
        *         :raises TypeError:    If a key or value could not be transformed into a :js:class:`Buffer`
        *         :raises:              See :js:func:`~js2p.sync.sync_socket.__store`
        */
        let new_meta = new m.metatuple(this.id, base.getUTC());
        let s_key = new Buffer(key);
        let s_data = new Buffer(data);
        this.__store(s_key, s_data, new_meta);
        if (!data)  {
            this.send([s_key, ''], undefined, base.flags.store);
        }
        else    {
            this.send([s_key, s_data], undefined, base.flags.store);
        }
    }

    update(update_dict) {
        /**
        *     .. js:function:: js2p.sync.sync_socket.update(update_dict)
        *
        *         For each key/value pair in the given object, calls :js:func:`~js2p.sync.sync_socket.set`
        *
        *         :param Object update_dict: An object with keys and values which can be transformed into a :js:class:`Buffer`
        *
        *         :raises: See :js:func:`~js2p.sync.sync_socket.set`
        */
        for (var key in update_dict)    {
            this.set(key, update_dict[key]);
        }
    }
}