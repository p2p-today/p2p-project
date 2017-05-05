/**
* Chord Module
* ============
*/

"use strict";

const base = require('./base.js');
const mesh = require('./mesh.js');
const Buffer = require('buffer').Buffer;
const equal = require('equal');
const SHA = require('jssha');
const BigInt = require('big-integer');
const util = require('util');

var m;

if( typeof exports !== 'undefined' ) {
    if( typeof module !== 'undefined' && module.exports ) {
        m = exports = module.exports;
    }
    m = exports;
}
else {
    root.chord = {};
    m = root;
}

m.default_protocol = new base.Protocol('chord', 'Plaintext');

m.limit = BigInt('g0000000000000000000000000000000000000000000000000000000000000000000000000000', 32);  // 2 ** 384

m.max_outgoing = mesh.max_outgoing;

m.distance = function distance(a, b, limit) {
    let raw = BigInt(b).minus(a);
    if (limit !== undefined)    {
        if (raw.lesser(0))  {
            return raw.mod(limit).plus(limit).mod(limit);
        }
        return raw.mod(limit);
    }
    else    {
        if (raw.lesser(0))  {
            return raw.mod(m.limit).plus(m.limit).mod(m.limit);
        }
        return raw.mod(m.limit);
    }
};

m.get_hashes = function get_hashes(key) {
    /**
    * .. js:function:: js2p.chord.get_hashes(key)
    *
    *     Returns the (adjusted) hashes for a given key. This is in the order of:
    *
    *     - SHA1 (shifted 224 bits left)
    *     - SHA224 (shifted 160 bits left)
    *     - SHA256 (shifted 128 bits left)
    *     - SHA384 (unadjusted)
    *     - SHA512 (unadjusted)
    *
    *     The adjustment is made to allow better load balancing between nodes, which
    *     assign responisbility for a value based on their SHA384-assigned ID.
    */
    let ret = [];
    // get SHA1
    let hash = new SHA("SHA-1", "ARRAYBUFFER");
    hash.update(key);
    ret.push(BigInt(hash.getHash("HEX"), 16).shiftLeft(224));
    // get SHA224
    hash = new SHA("SHA-224", "ARRAYBUFFER");
    hash.update(key);
    ret.push(BigInt(hash.getHash("HEX"), 16).shiftLeft(160));
    // get SHA256
    ret.push(BigInt(base.SHA256(key), 16).shiftLeft(128));
    // get SHA384
    ret.push(BigInt(base.SHA384(key), 16));
    // get SHA512
    hash = new SHA("SHA-512", "ARRAYBUFFER");
    hash.update(key);
    ret.push(BigInt(hash.getHash("HEX"), 16));
    return ret;
};

class awaiting_value    {
    constructor(value)  {
        this.value = value;
        this.callback = undefined;
        this.__is_awaiting_value = true;
    }

    callback_method(method, key)    {
        this.callback.send(
            base.flags.whisper,
            [base.flags.retrieved, method, key, this.value]
        );
    }
}

function most_common(tmp)   {
    let lst = [];
    for (let item of tmp)   {
        if (item === null || item === undefined)    {}
        else if (item.__is_awaiting_value)  {
            lst.push(item.value);
        }
        else    {
            lst.push(item);
        }
    }

    if (!lst.length)    {
        return [undefined, 0];
    }

    const comparator = (o)=>{
        return (v)=>{
            return equal(v, o);
        }
    }

    let ret = lst.sort((a,b)=>{
        return lst.filter(comparator(a)).length
             - lst.filter(comparator(b)).length;
    }).pop();
    return [ret, lst.filter(comparator(ret)).length + 1];
}


m.ChordConnection = class ChordConnection extends mesh.MeshConnection    {
    /**
    * .. js:class:: js2p.chord.ChordConnection(sock, server, outgoing)
    *
    *     This is the class for chord connection abstractraction. It inherits from :js:class:`js2p.mesh.MeshConnection`
    *
    *     :param sock:                              This is the raw socket object
    *     :param js2p.chord.ChordSocket server:    This is a link to the :js:class:`~js2p.chord.ChordSocket` parent
    *     :param outgoing:                          This bool describes whether ``server`` initiated the connection
    */
    constructor(sock, server, outgoing) {
        super(sock, server, outgoing);
        this.__id_10 = -1;
        this.leeching = true;
    }

    get id_10() {
        if (this.id === null)   {
            return null;
        }
        else if (!BigInt.isInstance(this.__id_10))   {
            this.__id_10 = base.from_base_58(this.id);
        }
        return this.__id_10;
    }
};

m.ChordSocket = class ChordSocket extends mesh.MeshSocket    {
    /**
    * .. js:class:: js2p.chord.ChordSocket(addr, port [, protocol [, out_addr [, debug_level]]])
    *
    *     This is the class for chord network socket abstraction. It inherits from :js:class:`js2p.mesh.MeshSocket`
    *
    *     :param string addr:                   The address you'd like to bind to
    *     :param number port:                   The port you'd like to bind to
    *     :param js2p.base.Protocol protocol:   The subnet you're looking to connect to
    *     :param array out_addr:                Your outward-facing address
    *     :param number debug_level:            The verbosity of debug prints
    *
    *     .. js:function:: js2p.chord.ChordSocket Event 'add'(conn, key)
    *
    *         This event is triggered when a key is added to the distributed
    *         dictionary. Because value information is not transmitted in this
    *         message, you must specifically request it.
    *
    *         :param js2p.chord.ChordSocket conn: A reference to this abstract socket
    *         :param Buffer key: The key which has a new value
    *
    *     .. js:function:: js2p.chord.ChordSocket Event 'delete'(conn, key)
    *
    *         This event is triggered when a key is deleted from your distributed
    *         dictionary.
    *
    *         :param js2p.chord.ChordSocket conn: A reference to this abstract socket
    *         :param Buffer key: The key which has a new value
    *
    *     .. js:attribute:: js2p.chord.ChordSocket.id_10
    *
    *         This socket's ID as a :js:class:`big-integer`
    *
    */
    constructor(addr, port, protocol, out_addr, debug_level)   {
        super(addr, port, protocol || m.default_protocol, out_addr, debug_level);
        const self = this;
        this.conn_type = m.ChordConnection;
        this.leeching = true;
        this.id_10 = base.from_base_58(this.id);
        this.connect_override = true;
        this.data = {
            'sha1': {},
            'sha224': {},
            'sha256': {},
            'sha384': {},
            'sha512': {}
        };
        this.__keys = new Set();
        this.register_handler(function __handle_meta(msg, conn)  {return self.__handle_meta(msg, conn);});
        this.register_handler(function __handle_key(msg, conn)  {return self.__handle_key(msg, conn);});
        this.register_handler(function __handle_retrieved(msg, conn)  {return self.__handle_retrieved(msg, conn);});
        this.register_handler(function __handle_retrieve(msg, conn)  {return self.__handle_retrieve(msg, conn);});
        this.register_handler(function __handle_store(msg, conn)  {return self.__handle_store(msg, conn);});
        this.register_handler(function __handle_delta(msg, conn)  {return self.__handle_delta(msg, conn);});
    }

    __on_TCP_Connection(sock)  {
        let conn = super.__on_TCP_Connection(sock);
        this._send_meta(conn);
        return conn;
    }

    __on_WS_Connection(sock)  {
        let conn = super.__on_WS_Connection(sock);
        this._send_meta(conn);
        return conn;
    }

    get data_storing()  {
        const self = this;
        function* _data_storing()   {
            for (let key of self.routing_table.keys()) {
                let node = self.routing_table.get(key);
                if (!node.leeching) {
                    yield node;
                }
            }
        }
        return _data_storing();
    }

    __handle_peers(msg, conn)   {
        /**
        *     .. js:function:: js2p.chord.ChordSocket.__handle_peers(msg, conn)
        *
        *         This callback is used to deal with peer signals. Its primary jobs is to connect to the given peers, if this does not exceed :js:data:`js2p.chord.max_outgoing`
        *
        *         :param js2p.base.Message msg:
        *         :param js2p.mesh.MeshConnection conn:
        *
        *         :returns: Either ``true`` or ``undefined``
        */
        var packets = msg.packets;
        if (packets[0] === base.flags.peers)  {
            var new_peers = packets[1];
            var self = this;

            function is_prev(id)    {
                return m.distance(base.from_base_58(id), self.id_10).lesserOrEquals(distance(self.prev.id_10, self.id_10));
            }

            function is_next(id)    {
                return m.distance(self.id_10, base.from_base_58(id)).lesserOrEquals(distance(self.id_10, self.next.id_10));
            }

            new_peers.forEach(function(peer_array)  {
                var addr = peer_array[0];
                var id = peer_array[1];
                if (self.outgoing.length < m.max_outgoing || is_prev(id) || is_next(id))    {
                    if (addr[0] && addr[1])
                        self.__connect(addr[0], addr[1], id);
                }
            });
            return true;
        }
    }


    __handle_delta(msg, handler)  {
        /**
        *     .. js:function:: js2p.chord.ChordSocket.__handle_delta(msg, conn)
        *
        *         This callback is used to deal with delta storage signals. Its
        *         primary job is:
        *
        *             - update the mapping in a given key
        *
        *         :param msg:       A :js:class:`~js2p.base.Message`
        *         :param handler:   A :js:class:`~js2p.chord.ChordConnection`
        *
        *         :returns: Either ``True`` or ``None``
        */
        let packets = msg.packets;
        if (packets[0] === base.flags.delta)  {
            let method = packets[1];
            let key = base.from_base_58(packets[2]);
            this.__delta(method, key, packets[3]);
            return true;
        }
    }

    __connect(addr, port, id)   {
        try {
            let handler = this.connect(addr, port, id)
            if (handler && !this.leeching)  {
                this._send_handshake(handler)
                this._send_meta(handler)
            }
        }
        catch(e) {}
    }

    join()  {
        this.leeching = false;
        for (let handler of this.awaiting_ids)  {
            this._send_handshake(handler);
            this._send_peers(handler);
            this._send_meta(handler);
        }
        for (let key of this.routing_table.keys())    {
            let handler = this.routing_table.get(key);
            if (handler)    {
                this._send_handshake(handler);
                this._send_peers(handler);
                this._send_meta(handler);
            }
        }
    }

    unjoin()    {
        this.leeching = true;
        for (let handler in this.awaiting_ids)  {
            this._send_handshake(handler);
            this._send_peers(handler);
            this._send_meta(handler);
        }
        for (let key of this.routing_table.keys())    {
            let handler = this.routing_table.get(key);
            if (handler)    {
                this._send_handshake(handler);
                this._send_peers(handler);
                this._send_meta(handler);
            }
        }
    }

    _send_meta(handler) {
        handler.send(base.flags.whisper, [base.flags.handshake, this.leeching ? '1' : '0']);
        for (let key in this.__keys)    {
            handler.send(base.flags.whisper, [base.flags.notify, key]);
        }
    }

    disconnect_least_efficient()    {
        function smallest_gap(lst)  {
            let coll = lst.sort((a, b)=>{
                return a.id_10 - b.id_10;
            });
            let coll_len = coll.length;
            let circular_triplets = [];
            for (let i = 0; i < coll_len; i++)  {
                let beg = coll[i];
                let mid = coll[(i + 1) % coll_len];
                let end = coll[(i + 2) % coll_len];
                circular_triplets.push([beg, mid, end]);
            }
            let narrowest = null;
            let gap = m.limit;
            for (let tuple of circular_triplets)    {
                let beg = tuple[0];
                let mid = tuple[1];
                let end = tuple[2];
                if (m.distance(beg.id_10, end.id_10).lesser(gap) && mid.outgoing)    {
                    gap = m.distance(beg.id_10, end.id_10);
                    narrowest = mid;
                }
            }
            return narrowest;
        }

        to_kill = smallest_gap(this.data_storing);
        if (to_kill)    {
            this.disconnect(to_kill);
            return true;
        }
        return false;
    }

    __handle_meta(msg, conn)   {
        const packets = msg.packets;
        if (packets[0] === base.flags.handshake && packets.length === 2) {
            if (!conn.id)   {
                conn.id = msg.sender;
                this.move_to_routing_table(conn.id, conn);
            }
            let new_meta = (packets[1].toString() === '1');
            if (new_meta !== conn.leeching)  {
                this._send_meta(conn);
                conn.leeching = new_meta;
                if (!conn.leeching && [...this.data_storing].length === 1) {
                    this.emit('connect', this);
                }
                if (!this.leeching && !conn.leeching)   {
                    this._send_peers(conn);
                    let update = this.dump_data(conn.id_10, this.id_10);
                    for (let method in update)  {
                        let table = update[method];
                        for (let key in table)  {
                            let value = table[key];
                            // this.__print__(method, key, value, level=5);
                            this.__store(method, key, value);
                        }
                    }
                }
                if (this.outgoing.length > m.max_outgoing)    {
                    this.disconnect_least_efficient();
                }
            }
            return true;
        }
    }

    __handle_key(msg, conn)   {
        let packets = msg.packets;
        if (packets[0] === base.flags.notify) {
            if (packets.length === 3)   {
                if (this.__keys.has(packets[1]))    {
                    this.__keys.remove(packets[1]);
                    this.emit('delete', this, packets[1]);
                }
            }
            else    {
                this.__keys.add(packets[1]);
                this.emit('add', this, packets[1]);
            }
            return true;
        }
    }

    __handle_retrieved(msg, conn)   {
        const packets = msg.packets;
        if (packets[0] === base.flags.retrieved) {
            // self.__print__("Response received for request id %s" % packets[1],
            //                level=1)
            if (this.requests[[packets[1].toString(), packets[2]]]) {
                let value = this.requests[[packets[1].toString(), packets[2]]];
                value.value = packets[3];
                if (value.callback) {
                    value.callback_method(packets[1], packets[2]);
                }
            }
            return true;
        }
    }

    __handle_retrieve(msg, conn)   {
        const packets = msg.packets;
        if (packets[0] === base.flags.retrieve)  {
            let val = this.__lookup(packets[1].toString(), base.from_base_58(packets[2]), conn);
            try {
                conn.send(base.flags.whisper, [base.flags.retrieved, packets[1], packets[2], val.value]);
            }
            catch (e)   {
                console.warn(e);
            }
            return true;
        }
    }

    __handle_store(msg, conn)   {
        let packets = msg.packets;
        if (packets[0] === base.flags.store)  {
            let method = packets[1].toString();
            let key = base.from_base_58(packets[2]);
            this.__store(method, key, packets[3]);
            return true;
        }
    }

    find(key)   {
        let ret = null;
        let gap = m.limit;
        if (!this.leeching) {
            ret = this;
            gap = m.distance(this.id_10, key);
        }
        for (let handler of this.data_storing)  {
            let dist = m.distance(handler.id_10, key);
            if (dist.lesser(gap))   {
                ret = handler;
                gap = dist;
            }
        }
        return ret;
    }

    find_prev(key)  {
        let ret = null;
        let gap = m.limit;
        if (!this.leeching) {
            ret = this;
            gap = m.distance(key, this.id_10);
        }
        for (let handler of this.data_storing)  {
            let dist = m.distance(key, handler.id_10);
            if (dist.lesser(gap))   {
                ret = handler;
                gap = dist;
            }
        }
        return ret;
    }

    get next()  {
        return this.find(this.id_10.minus(1));
    }

    get prev()  {
        return this.find_prev(this.id_10.plus(1));
    }

    dump_data(start, end)   {
        let ret = {
            'sha1': {},
            'sha224': {},
            'sha256': {},
            'sha384': {},
            'sha512': {}
        };
        for (let method of Object.keys(this.data))  {
            let table = this.data[method];
            for (let key of Object.keys(table)) {
                if (m.distance(start, key).lesser(m.distance(end, key)))    {
                    ret[method][key] = table[key];
                }
            }
        }
        return ret;
    }

    __lookup(method, key, handler)  {
        let node = this;
        if (this.routing_table.size) {
            node = this.find(key);
        }
        else if (this.awaiting_ids.length)  {
            node = this.awaiting_ids[Math.floor(Math.random()*this.awaiting_ids.length)];
        }
        if (Object.is(node, this))  {
            return new awaiting_value(this.data[method][key]);
        }
        else    {
            node.send(base.flags.whisper, [base.flags.retrieve, method, base.to_base_58(key)]);
            let ret = new awaiting_value();
            if (handler)    {
                ret.callback = handler;
            }
            this.requests[[method, base.to_base_58(key)]] = ret;
            return ret;
        }
    }

    get_no_fallback(key, timeout) {
        key = new Buffer(key);
        return new Promise((fulfill, reject) => {

            let keys = m.get_hashes(key);
            let vals = [
                this.__lookup('sha1', keys[0]),
                this.__lookup('sha224', keys[1]),
                this.__lookup('sha256', keys[2]),
                this.__lookup('sha384', keys[3]),
                this.__lookup('sha512', keys[4])
            ];
            let ctuple = most_common(vals);
            let common = ctuple[0];
            let count = ctuple[1];
            let iters = 0
            let limit = Math.floor(timeout / 0.1) || 100;

            let cleanup = ()=>{
                delete this.requests[`sha1,${base.to_base_58(keys[0])}`];
                delete this.requests[`sha224,${base.to_base_58(keys[1])}`];
                delete this.requests[`sha256,${base.to_base_58(keys[2])}`];
                delete this.requests[`sha384,${base.to_base_58(keys[3])}`];
                delete this.requests[`sha512,${base.to_base_58(keys[4])}`];
            }

            function check()    {
                if ((common === undefined || count <= 2) && iters < limit)   {
                    setTimeout(check, 100);
                    iters += 1
                    ctuple = most_common(vals);
                    common = ctuple[0];
                    count = ctuple[1];
                }
                else if (common !== undefined && common !== null && count > 2) {
                    cleanup();
                    fulfill(common);
                }
                else if (iters === limit)   {
                    cleanup();
                    reject(new Error(`Time out: ${util.inspect(vals)}`));
                }
                else    {
                    cleanup();
                    reject(new Error(`This key does not have an agreed-upon value. values=${util.inspect(vals)}, count=${count}, majority=3, most common=${util.inspect(common)}`));
                }
            }
            check();
        });
    }

    get(key, fallback, timeout) {
        /**
        *     .. js:function:: js2p.chord.ChordSocket.get(key [, fallback [, timeout]])
        *
        *         Retrieves the value at a given key
        *
        *         :param key:       The key you wish to look up (must be transformable into a :js:class:`Buffer` )
        *         :param fallback:  The value it should return when the key has no data
        *         :param timeout:   The maximum time (in seconds) to wait before returning ``fallback``
        *
        *         :returns: A :js:class:`Promise` for the value at the given key, or ``fallback``.
        *
        *         :raises TypeError:    If the key could not be transformed into a :js:class:`Buffer`
        */
        try {
            return this.get_no_fallback(key, timeout);
        }
        catch (e)   {
            return Promise.resolve(fallback);
        }
    }

    __store(method, key, value) {
        let node = this.find(key);
        if (this.leeching && Object.is(node, this)) {
            node = this.awaiting_ids[Math.floor(Math.random()*this.awaiting_ids.length)];
        }
        if (Object.is(node, this))  {
            if (value === null)    {
                delete this.data[method][key];
            }
            else    {
                this.data[method][key] = value;
            }
        }
        else    {
            node.send(base.flags.whisper, [base.flags.store, method, base.to_base_58(key), value]);
        }
    }

    __delta(method, key, delta) {
        let node = this.find(key);
        if (this.leeching && Object.is(node, this) && this.awaiting_ids.length) {
            node = this.awaiting_ids[Math.floor(Math.random()*this.awaiting_ids.length)];
        }
        if (Object.is(node, this))  {
            if (this.data[method][key] === undefined)   {
                this.data[method][key] = {};
            }
            if (this.data[method][key] instanceof Object)  {
                for (let _key in delta)  {
                    this.data[method][key][_key] = delta[_key];
                }
            }
        }
        else    {
            node.send(base.flags.whisper, [base.flags.delta, method, base.to_base_58(key), delta]);
        }
    }

    apply_delta(key, delta) {
        /*Updates a stored mapping with the given delta. This allows for more
        graceful handling of conflicting changes

        Args:
            key:    The key you wish to apply a delta to. Must be a
                        :py:class:`str` or :py:class:`bytes`-like object
            delta:  A mapping which contains the keys you wish to update, and
                        the values you wish to store

        Returns:
            A :py:class:`~async_promises.Promise` which yields the resulting
            data, or rejects with a :py:class:`TypeError` if the updated key
            does not store a mapping already.

        Raises:
            TypeError: If the updated key does not store a mapping already.
        */

        const self = this;

        return new Promise((resolve, reject)=>{
            if (!(delta instanceof Object)) {
                reject(new Error("Cannot apply delta if you feed a non-mapping"));
            }

            function on_success(value)    {
                let _key = new Buffer(key);
                let keys = m.get_hashes(_key);
                let hashes = ['sha1', 'sha224', 'sha256', 'sha384', 'sha512'];
                for (let i in keys) {
                    self.__delta(hashes[i], keys[i], delta);
                }
                for (let k of Object.keys(delta))    {
                    value[k] = delta[k];
                }
                resolve(value)
            }

            self.get(key, {}).then(
                (value)=>{
                    if (value instanceof Object)    {
                        on_success(value);
                    }
                    else    {
                        reject(new Error("This key already has a non-mapping value"));
                    }
                },
                ()=>{on_success({})}
            );
        });
    }

    set(key, value) {
        /**
        *     .. js:function:: js2p.chord.ChordSocket.set(key, value)
        *
        *         Sets the value at a given key
        *
        *         :param key:   The key you wish to look up (must be transformable into a :js:class:`Buffer` )
        *         :param value: The value you wish to store
        *
        *         :raises TypeError:    If a key could not be transformed into a :js:class:`Buffer`
        *         :raises:              See :js:func:`~js2p.chord.ChordSocket.__store`
        */
        key = new Buffer(key);
        let keys = m.get_hashes(key);
        this.__store('sha1', keys[0], value);
        this.__store('sha224', keys[1], value);
        this.__store('sha256', keys[2], value);
        this.__store('sha384', keys[3], value);
        this.__store('sha512', keys[4], value);
        if (!this.__keys.has(key) && value !== null)    {
            this.__keys.add(key);
            this.send([key], undefined, base.flags.notify);
        }
        else if (this.__keys.has(key) && value === null)    {
            this.__keys.add(key);
            this.send([key, 'del'], undefined, base.flags.notify);
        }
    }

    update(update_dict) {
        /**
        *     .. js:function:: js2p.chord.ChordSocket.update(update_dict)
        *
        *         For each key/value pair in the given object, calls :js:func:`~js2p.chord.ChordSocket.set`
        *
        *         :param Object update_dict: An object with keys and values which can be transformed into a :js:class:`Buffer`
        *
        *         :raises: See :js:func:`~js2p.chord.ChordSocket.set`
        */
        for (let key in update_dict)    {
            this.set(key, update_dict[key]);
        }
    }

    del(key)    {
        /**
        *     .. js:function:: js2p.chord.ChordSocket.del(key)
        *
        *         Clears the value at a given key
        *
        *         :param key:   The key you wish to look up (must be transformable into a :js:class:`Buffer` )
        *
        *         :raises TypeError:    If a key or value could not be transformed into a :js:class:`Buffer`
        *         :raises:              See :js:func:`~js2p.chord.ChordSocket.set`
        */
        this.set(key, null);
    }

    *keys()  {
        /**
        *     .. js:function:: js2p.chord.ChordSocket.keys()
        *
        *         Returns a generator for all keys presently in the dictionary
        *
        *         Because this data is changed asynchronously, the key is
        *         only garunteed to be present at the time of generation.
        *
        *         :returns: A generator which yields :js:class:`Buffer` s
        */
        for (let key of this.__keys) {
            if (this.__keys.has(key))   {
                yield key;
            }
        }
    }

    *values()    {
        /**
        *     .. js:function:: js2p.chord.ChordSocket.values()
        *
        *         Returns a generator for all values presently in the
        *         dictionary
        *
        *         Because this data is changed asynchronously, the value is
        *         only garunteed to be accurate at the time of generation.
        *
        *         :returns: A generator which yields :js:class:`Promise` s.
        *                   These :js:class:`Promise` s will yield a
        *                   :js:class:`Buffer` , on success.
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
        *     .. js:function:: js2p.chord.ChordSocket.items()
        *
        *         Returns a generator for all associations presently in the
        *         dictionary
        *
        *         Because this data is changed asynchronously, the association
        *         is only garunteed to be present at the time of generation.
        *
        *         :returns: A generator which yields pairs of
        *                   :js:class:`Buffer` s and :js:class:`Promise` s. The
        *                   :js:class:`Promise` s will yield a
        *                   :js:class:`Buffer` , on success.
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
        *     .. js:function:: js2p.chord.ChordSocket.pop(key [, fallback])
        *
        *         Returns the value at a given key. As a side effect, it
        *         it deletes that association.
        *
        *         :returns: A :js:class:`Promise` , similar to the
        *                   :js:func:`js2p.chord.ChordSocket.get` method.
        */
        let val = this.get(key, fallback);
        if (val !== fallback)    {
            this.del(key);
        }
        return val;
    }

    popitem()   {
        /**
        *     .. js:function:: js2p.chord.ChordSocket.popitem()
        *
        *         Returns the association at a key. As a side effect, it
        *         it deletes that association.
        *
        *         :returns: A pair of :js:class:`Buffer` and
        *                   :js:class:`Promise` , similar to an item in
        *                   :js:func:`js2p.chord.ChordSocket.items`
        */
        for (let key of this.keys())  {
            return [key, this.pop(key)];
        }
    }

    copy()  {
        /**
        *     .. js:function:: js2p.chord.ChordSocket.copy()
        *
        *         Returns the :js:class:`Promise` of an :js:class:`Object` ,
        *         with the same associations as this DHT.
        *
        *         .. note::
        *
        *             This is potentially a very slow operation. It is probably
        *             significantly faster, and likely to be more accurate, if
        *             you iterate over :js:func:`js2p.chord.ChordSocket.items`
        *
        *         :returns: The :js:class:`Promise` of an :js:class:`Object` ,
        *                   with the same associations as this DHT.
        */
        return new Promise((resolve, reject)=>{
            let ret = {};
            let count = this.__keys.length;
            for (let item of this.items())  {
                let key = item[0];
                item[1].then((value)=>{
                    ret[key] = value;
                    --count;
                },
                (err)=>{
                    --count;
                });
            }
            function check() {
                if (!count) {
                    resolve(ret);
                }
                else    {
                    setTimeout(check, 100);
                }
            }
            check();
        });
    }
}
