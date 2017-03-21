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

m.default_protocol = new base.Protocol('sync', 'Plaintext');

m.metatuple = class metatuple   {
    /**
    * .. js:class:: js2p.sync.metatuple(owner, timestamp)
    *
    *     This class is used to store metadata for a particular key
    *
    *     :param string owner: The owner of this change
    *     :param Number timestamp: The time of this change
    */
    constructor(owner, timestamp)   {
        this.owner = owner;
        this.timestamp = timestamp;
    }
}

m.SyncSocket = class SyncSocket extends mesh.MeshSocket  {
    /**
    * .. js:class:: js2p.sync.SyncSocket(addr, port [, leasing [, protocol [, out_addr [, debug_level]]]])
    *
    *     This is the class for mesh network socket abstraction. It inherits from :js:class:`js2p.mesh.MeshSocket`.
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
    *     :param js2p.base.Protocol protocol:   The subnet you're looking to connect to
    *     :param array out_addr:                Your outward-facing address
    *     :param number debug_level:            The verbosity of debug prints
    *
    *     .. js:function:: js2p.sync.SyncSocket Event 'update'(conn, key, new_data, metatuple)
    *
    *         This event is triggered when a key is updated in your synchronized
    *         dictionary. ``new_meta`` will be an object containing metadata of this
    *         change, including the time of change, and who initiated the change.
    *
    *         :param js2p.sync.SyncSocket conn: A reference to this abstract socket
    *         :param Buffer key: The key which has a new value
    *         :param new_data: The new value at that key
    *         :param js2p.sync.metatuple new_meta: Metadata on the key changer
    *
    *     .. js:function:: js2p.sync.SyncSocket Event 'delete'(conn, key)
    *
    *         This event is triggered when a key is deleted from your synchronized
    *         dictionary.
    *
    *         :param js2p.sync.SyncSocket conn: A reference to this abstract socket
    *         :param Buffer key: The key which has a new value
    *
    */
    constructor(addr, port, leasing, protocol, out_addr, debug_level)   {
        if (!protocol)  {
            protocol = m.default_protocol;
        }
        let lease_descriptor = (leasing !== false) ? '1' : '0';
        let protocol_used = new base.Protocol(protocol.subnet + lease_descriptor, protocol.encryption);
        super(addr, port, protocol_used, out_addr, debug_level);
        this.__leasing = leasing;
        this.data = {};
        this.metadata = {};
        const self = this;
        this.register_handler(function handle_store(msg, conn)  {return self.__handle_store(msg, conn);});
        this.register_handler(function handle_delta(msg, conn)  {return self.__handle_delta(msg, conn);});
    }

    __check_lease(key, new_data, new_meta, delta)  {
        let meta = this.metadata[key];
        return ((!meta) || (meta.owner.toString() === new_meta.owner.toString()) ||
                (delta && !this.__leasing) ||
                (meta.timestamp < base.getUTC() - 3600) ||
                (meta.timestamp === new_meta.timestamp && meta.owner.toString() > new_meta.owner.toString()) ||
                ((meta.timestamp < new_meta.timestamp) && (!this.__leasing)));
    }

    __store(key, new_data, new_meta, error) {
        /**
        *     .. js:function:: js2p.sync.SyncSocket.__store(key, new_data, new_meta, error)
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
                this.emit('delete', this, key);
            }
            else    {
                this.metadata[key] = new_meta;
                this.data[key] = new_data;
                this.emit('update', this, key, new_data, new_meta);
            }
        }
        else if (error !== false) {
            throw new Error("You don't have permission to change this yet");
        }
    }

    _send_peers(handler) {
        /**
        *     .. js:function:: js2p.sync.SyncSocket._send_peers(handler)
        *
        *         Shortcut method to send a handshake response. This method is extracted from :js:func:`~js2p.mesh.MeshSocket.__handle_handshake`
        *         in order to allow cleaner inheritence from :js:class:`js2p.sync.SyncSocket`
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
        *     .. js:function:: js2p.sync.SyncSocket.__handle_store
        *
        *         This callback is used to deal with data storage signals. Its two primary jobs are:
        *
        *            - store data in a given key
        *            - delete data in a given key
        *
        *            :param msg:        A :js:class:`~js2p.base.Message`
        *            :param handler:    A :js:class:`~js2p.mesh.MeshConnection`
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
        *     .. js:function:: js2p.sync.SyncSocket.get(key [, fallback])
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
        *     .. js:function:: js2p.sync.SyncSocket.set(key, value)
        *
        *         Sets the value at a given key
        *
        *         :param key:   The key you wish to look up (must be transformable into a :js:class:`Buffer` )
        *         :param value: The value you wish to store
        *
        *         :raises TypeError:    If a key could not be transformed into a :js:class:`Buffer`
        *         :raises:              See :js:func:`~js2p.sync.SyncSocket.__store`
        */
        let new_meta = new m.metatuple(this.id, base.getUTC());
        let s_key = new Buffer(key);
        this.__store(s_key, data, new_meta);
        this.send([s_key, data], undefined, base.flags.store);
    }

    __delta(key, delta, new_meta, error) {
        /**
        *     .. js:function:: js2p.sync.SyncSocket.__delta(key, delta, new_meta, error)
        *
        *         Private API method for storing data
        *
        *         :param key:        The key you wish to store data at
        *         :param delta:      The delta you wish to apply at said key
        *         :param new_meta:   The metadata associated with this storage
        *         :param error:      A boolean which says whether to raise a :py:class:`KeyError` if you can't store there
        *
        *         :raises Error: If someone else has a lease at this value, and ``error`` is not ``false``
        */
        if (this.__check_lease(key, delta, new_meta, true))    {
            if (this.data[key] === undefined)   {
                this.data[key] = {};
            }
            if (this.data[key] instanceof Object)  {
                this.metadata[key] = new_meta;
                for (let _key in delta)  {
                    this.data[key][_key] = delta[_key];
                }
                this.emit('update', this, key, this.data[key], new_meta);
            }
            else if (error !== false)    {
                throw new Error("You cannot apply a delta to a non-mapping");
            }
        }
        else if (error !== false) {
            throw new Error("You don't have permission to change this yet");
        }
    }

    apply_delta(key, delta) {
        /**
        *     .. js:function:: js2p.sync.SyncSocket.apply_delta(key, delta)
        *
        *         Sets the value at a given key
        *
        *         :param key:   The key you wish to look up (must be transformable into a :js:class:`Buffer` )
        *         :param delta: The detla you wish to apply at said key
        *
        *         :raises TypeError:    If a key could not be transformed into a :js:class:`Buffer`
        *         :raises TypeError:    If the value stored at this key is not a mapping, or delta is not a mapping
        *         :raises:              See :js:func:`~js2p.sync.SyncSocket.__delta`
        */
        let new_meta = new m.metatuple(this.id, base.getUTC());
        let s_key = new Buffer(key);
        this.__delta(s_key, delta, new_meta);
        this.send([s_key, delta], undefined, base.flags.delta);
    }

    __handle_delta(msg, handler)  {
        /**
        *     .. js:function:: js2p.sync.SyncSocket.__handle_delta
        *
        *         This callback is used to deal with data delta signals. Its primary job is:
        *
        *            - apply a delta at a given key
        *
        *            :param msg:        A :js:class:`~js2p.base.Message`
        *            :param handler:    A :js:class:`~js2p.mesh.MeshConnection`
        *
        *            :returns: Either ``true`` or ``undefined``
        */
        const packets = msg.packets;
        if (packets[0] === base.flags.delta) {
            let meta = new m.metatuple(msg.sender, msg.time);
            this.__delta(packets[1], packets[2], meta, false);
            return true;
        }
    }

    update(update_dict) {
        /**
        *     .. js:function:: js2p.sync.SyncSocket.update(update_dict)
        *
        *         For each key/value pair in the given object, calls :js:func:`~js2p.sync.SyncSocket.set`
        *
        *         :param Object update_dict: An object with keys and values which can be transformed into a :js:class:`Buffer`
        *
        *         :raises: See :js:func:`~js2p.sync.SyncSocket.set`
        */
        for (var key in update_dict)    {
            this.set(key, update_dict[key]);
        }
    }

    del(key)    {
        /**
        *     .. js:function:: js2p.sync.SyncSocket.del(key)
        *
        *         Clears the value at a given key
        *
        *         :param key:   The key you wish to look up (must be transformable into a :js:class:`Buffer` )
        *
        *         :raises TypeError:    If a key or value could not be transformed into a :js:class:`Buffer`
        *         :raises:              See :js:func:`~js2p.sync.SyncSocket.set`
        */
        this.set(key);
    }

    *keys()  {
        /**
        *     .. js:function:: js2p.sync.SyncSocket.keys()
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
        *     .. js:function:: js2p.sync.SyncSocket.values()
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
        *     .. js:function:: js2p.sync.SyncSocket.items()
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
        *     .. js:function:: js2p.sync.SyncSocket.pop(key [, fallback])
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
        *     .. js:function:: js2p.sync.SyncSocket.popitem()
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
