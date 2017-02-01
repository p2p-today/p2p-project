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
        this.__leasing = leasing;
        this.data = {};
        this.metadata = {};
        const self = this;
        this.register_handler(function handle_store(msg, conn)  {return self.__handle_store(msg, conn);});
    }

    __check_lease(key, new_data, new_meta)  {
        let meta = this.metadata[key];
        return ((!meta) || (meta.owner.toString() === new_meta.owner.toString()) ||
                (meta.timestamp < base.getUTC() - 3600) ||
                (meta.timestamp === new_meta.timestamp && meta.owner.toString() > new_meta.owner.toString()) ||
                ((meta.timestamp < new_meta.timestamp) && (!this.__leasing)));
    }

    __store(key, new_data, new_meta, error) {
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
        if (this.__check_lease(key, new_data, new_meta))    {
            if (new_data.toString() === '')    {
                delete this.data[key];
                delete this.metadata[key];
            }
            else    {
                this.metadata[key] = new_meta;
                this.data[key] = new_data;
            }
        }
        else if (error !== false) {
            throw new Error("You don't have permission to change this yet");
        }
    }

    _send_peers(handler) {
        /**
        *     .. js:function:: js2p.sync.sync_socket._send_peers(handler)
        *
        *         Shortcut method to send a handshake response. This method is extracted from :js:func:`~js2p.mesh.mesh_socket.__handle_handshake`
        *         in order to allow cleaner inheritence from :js:class:`js2p.sync.sync_socket`
        *
        */
        super._send_peers(handler)
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
        if (packets[0] === base.flags.store) {
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
        *         :param value: The key you wish to store
        *
        *         :raises TypeError:    If a key or value could not be transformed into a :js:class:`Buffer`
        *         :raises:              See :js:func:`~js2p.sync.sync_socket.__store`
        */
        let new_meta = new m.metatuple(this.id, base.getUTC());
        let s_key = new Buffer(key);
        this.__store(s_key, data, new_meta);
        this.send([s_key, data], undefined, base.flags.store);
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

    del(key)    {
        /**
        *     .. js:function:: js2p.sync.sync_socket.del(key)
        *
        *         Clears the value at a given key
        *
        *         :param key:   The key you wish to look up (must be transformable into a :js:class:`Buffer` )
        *
        *         :raises TypeError:    If a key or value could not be transformed into a :js:class:`Buffer`
        *         :raises:              See :js:func:`~js2p.sync.sync_socket.set`
        */
        this.set(key);
    }

    *keys()  {
        /**
        *     .. js:function:: js2p.sync.sync_socket.keys()
        *
        *         Returns a generator for all keys presently in the dictionary
        *
        *         Because this data is changed asynchronously, the key is
        *         only garunteed to be present at the time of generation.
        *
        *         :returns: A generator which yields :js:class:`Buffer` s
        */
        for (let key of Object.keys(this.data)) {
            if (this.get(key, null) !== null)    {
                yield key;
            }
        }
    }

    *values()    {
        /**
        *     .. js:function:: js2p.sync.sync_socket.values()
        *
        *         Returns a generator for all values presently in the
        *         dictionary
        *
        *         Because this data is changed asynchronously, the value is
        *         only garunteed to be accurate at the time of generation.
        *
        *         :returns: A generator which yields :js:class:`Buffer` s
        */
        for (let key of this.keys())  {
            let val = this.get(key);
            if (val !== undefined)   {
                yield val;
            }
        }
    }

    *items() {
        /**
        *     .. js:function:: js2p.sync.sync_socket.items()
        *
        *         Returns a generator for all associations presently in the
        *         dictionary
        *
        *         Because this data is changed asynchronously, the association
        *         is only garunteed to be present at the time of generation.
        *
        *         :returns: A generator which yields pairs of
        *                   :js:class:`Buffer` s
        */
        for (let key of this.keys())  {
            let val = this.get(key);
            if (val !== undefined)   {
                yield [key, val];
            }
        }
    }

    pop(key, fallback)  {
        /**
        *     .. js:function:: js2p.sync.sync_socket.pop(key [, fallback])
        *
        *         Returns the value at a given key. As a side effect, it
        *         it deletes that key.
        *
        *         :returns: A :js:class:`Buffer`
        */
        let val = this.get(key, fallback);
        if (val !== fallback)    {
            this.del(key);
        }
        return val;
    }

    popitem()   {
        /**
        *     .. js:function:: js2p.sync.sync_socket.popitem()
        *
        *         Returns the association at a key. As a side effect, it
        *         it deletes that key.
        *
        *         :returns: A pair of :js:class:`Buffer` s
        */
        for (let key of this.keys())  {
            return [key, this.pop(key)];
        }
    }
}
