/**
* Mesh Module
* ===========
*/

"use strict";

const BigInt = require('big-integer');
const base = require('./base.js');
const net = require('net');
const util = require('util');

var m;

if( typeof exports !== 'undefined' ) {
    if( typeof module !== 'undefined' && module.exports ) {
        m = exports = module.exports;
    }
    m = exports;
}
else {
    root.mesh = {};
    m = root;
}

m.max_outgoing = 4;

m.default_protocol = new base.protocol('mesh', "Plaintext");
/**
* .. js:data:: js2p.mesh.default_protocol
*
*     A :js:class:`~js2p.base.protocol` object which is used by default in the mesh module
*/

m.mesh_connection = class mesh_connection extends base.base_connection  {
    /**
    * .. js:class:: js2p.mesh.mesh_connection(sock, server, outgoing)
    *
    *     This is the class for mesh connection abstractraction. It inherits from :js:class:`js2p.base.base_connection`
    *
    *     :param sock:                          This is the raw socket object
    *     :param js2p.mesh.mesh_socket server:  This is a link to the :js:class:`~js2p.mesh.mesh_socket` parent
    *     :param outgoing:                      This bool describes whether ``server`` initiated the connection
    */
    constructor(sock, server, outgoing) {
        super(sock, server, outgoing);
    }

    send(msg_type, packs, id, time)  {
        /**
        *     .. js:function:: js2p.mesh.mesh_connection.send(msg_type, packs, id, time)
        *
        *         Sends a message through its connection.
        *
        *         :param msg_type:      Message type, corresponds to the header in a :js:class:`~js2p.base.InternalMessage` object
        *         :param packs:         A list of Buffer-like objects, which correspond to the packets to send to you
        *         :param id:            The ID this message should appear to be sent from (default: your ID)
        *         :param number time:   The time this message should appear to be sent from (default: now in UTC)
        *
        *         :returns: ``undefined``
        */
        // console.log(msg_type);
        // console.log(packs);
        try {
            var msg = super.send(msg_type, packs, id, time);
            //add msg to waterfall
            const mid = msg.id;
            if (!this.server._in_waterfalls(mid, msg.time))    {
                this.server.waterfalls.unshift([mid, msg.time]);
            }
        }
        catch(err)  {
            console.log(`There was an unhandled exception with peer id ${this.id}. This peer is being disconnected, and the relevant exception is added to the debug queue. If you'd like to report this, please post a copy of your mesh_socket.status to http://git.p2p.today/issues`);
            this.server.exceptions.push(err);
            if (this.sock.emit) {
                this.sock.emit('error');
            }
            else    {
                // This means it must be browser websockets
                this.onError(err);
            }
        }
    }

    found_terminator()  {
        /**
        *     .. js:function:: js2p.mesh.mesh_connection.found_terminator()
        *
        *         This method is called when the expected amount of data is received
        *
        *         :returns: ``undefined``
        */
        try {
            var msg = super.found_terminator();
            //console.log(msg.packets);
            if (this.handle_waterfall(msg, msg.packets))   {
                return true;
            }
            else if (this.handle_renegotiate(msg.packets))  {
                return true;
            }
            this.server.handle_msg(new base.message(msg, this.server), this);
        }
        catch(err)  {
            console.log(`There was an unhandled exception with peer id ${this.id}. This peer is being disconnected, and the relevant exception is added to the debug queue. If you'd like to report this, please post a copy of your mesh_socket.status to http://git.p2p.today/issues`);
            this.server.exceptions.push(err);
            if (this.sock.emit) {
                this.sock.emit('error');
            }
            else    {
                // This means it must be browser websockets
                this.onError(err);
            }
        }
    }

    handle_waterfall(msg, packets)  {
        /**
        *     .. js:function:: js2p.mesh.mesh_connection.handle_waterfall(msg, packets)
        *
        *         This method determines whether this message has been previously received or not.
        *         If it has been previously received, this method returns ``true``.
        *         If it is older than a preset limit, this method returns ``true``.
        *         Otherwise this method returns ``undefined``, and forwards the message appropriately.
        *
        *         :param js2p.base.InternalMessage msg: The message in question
        *         :param packets:                           The message's packets
        *
        *         :returns: ``true`` or ``undefined``
        */
        if (packets[0] === base.flags.broadcast) {
            if (msg.time < base.getUTC() - 60) {
                // this.__print__("Waterfall expired", level=2);
                return true;
            }
            else if (!this.server.waterfall(new base.message(msg, this.server)))  {
                // this.__print__("Waterfall already captured", level=2);
                return true;
            }
            // this.__print__("New waterfall received. Proceeding as normal", level=2)
        }
    }

    onClose()   {
        /**
        *     .. js:function:: js2p.mesh.mesh_connection.onClose()
        *
        *         This function is run when a connection is closed
        */
        if (this.server.routing_table[this.id]) {
            delete this.server.routing_table[this.id];
        }
    }

    onEnd()   {
        /**
        *     .. js:function:: js2p.mesh.mesh_connection.onEnd()
        *
        *         This function is run when a connection is ended
        */
        this.onError();
    }
}

m.mesh_socket = class mesh_socket extends base.base_socket  {
    /**
    * .. js:class:: js2p.mesh.mesh_socket(addr, port [, protocol [, out_addr [, debug_level]]])
    *
    *     This is the class for mesh network socket abstraction. It inherits from :js:class:`js2p.base.base_socket`
    *
    *     :param string addr:                   The address you'd like to bind to
    *     :param number port:                   The port you'd like to bind to
    *     :param js2p.base.protocol protocol:   The subnet you're looking to connect to
    *     :param array out_addr:                Your outward-facing address
    *     :param number debug_level:            The verbosity of debug prints
    *
    *     .. js:function:: Event 'connect'(conn)
    *
    *         This event is called whenever you have a *new* connection to the
    *         service network. In other words, whenever the length of your routing
    *         table is increased from one to zero.
    *
    *         If you call ``on('connect')``, that will be executed on every
    *         connection to the network. So if you are suddenly disconnected, and
    *         manage to recover, that function will execute again.
    *
    *         To avoid this, call ``once('connect')``. That will usually be more correct.
    *
    *         :param js2p.mesh.mesh_socket conn: A reference to this abstract socket
    *
    *     .. js:function:: Event 'message'(conn)
    *
    *         This event is called whenever you receive a new message. A reference
    *         to the message is *not* passed to you. This is to prevent potential
    *         memory leaks.
    *
    *         If you want to register a "privileged" handler which *does* get a
    *         reference to the message, see
    *         :js:func:`~js2p.base.base_socket.register_handler`
    *
    *         :param js2p.mesh.mesh_socket conn: A reference to this abstract socket
    *
    *     .. js:attribute:: js2p.mesh.mesh_socket.routing_table
    *
    *         An object which contains :js:class:`~js2p.mesh.mesh_connection` s keyed by their IDs
    *
    *     .. js:attribute:: js2p.mesh.mesh_socket.awaiting_ids
    *
    *         An array which contains :js:class:`~js2p.mesh.mesh_connection` s that are awaiting handshake information
    *
    */
    constructor(addr, port, protocol, out_addr, debug_level)   {
        super(addr, port, protocol || m.default_protocol, out_addr, debug_level);
        var self = this;
        this.conn_type = m.mesh_connection;
        this.waterfalls = [];
        this.requests = {};
        this.queue = [];
        this.register_handler(function handle_handshake(msg, conn)  {return self.__handle_handshake(msg, conn);});
        this.register_handler(function handle_peers(msg, conn)      {return self.__handle_peers(msg, conn);});
        this.register_handler(function handle_response(msg, conn)   {return self.__handle_response(msg, conn);});
        this.register_handler(function handle_request(msg, conn)    {return self.__handle_request(msg, conn);});

        if (this.incoming)  {
            if (self.protocol.encryption === 'SSL') {
                this.incoming.on('secureConnection', (sock)=>{
                    self.__on_TCP_Connection(sock);
                });
            }
            else    {
                this.incoming.on('connection', (sock)=>{
                    if (self.protocol.encryption === 'Plaintext')   {
                        self.__on_TCP_Connection(sock);
                    }
                    else    {
                        self.__on_WS_Connection(sock);
                    }
                });
            }
        }
    }

    __on_TCP_Connection(sock)  {
        var conn = new this.conn_type(sock, this, false);
        this._send_handshake(conn);
        this.awaiting_ids.push(conn);
        return conn;
    }

    __on_WS_Connection(sock)  {
        let conn = new this.conn_type(sock, this, false);
        this.awaiting_ids.push(conn);
        const self = this;
        sock.on("connect", ()=>{
            self._send_handshake(conn);
        });
        return conn;
    }

    recv(num)   {
        /**
        *     .. js:function:: js2p.mesh.mesh_socket.recv([num])
        *
        *         This function has two behaviors depending on whether num is truthy.
        *
        *         If num is truthy, it will return a list of :js:class:`~js2p.base.message` objects up to length len.
        *
        *         If num is not truthy, it will return either a single :js:class:`~js2p.base.message` object, or ``undefined``
        *
        *         :param number num: The maximum number of :js:class:`~js2p.base.message` s you would like to pull
        *
        *         :returns: A list of :js:class:`~js2p.base.message` s, an empty list, a single :js:class:`~js2p.base.message` , or ``undefined``
        */
        var ret;
        if (num)    {
            ret = this.queue.slice(0, num);
            this.queue = this.queue.slice(num);
        }
        else    {
            ret = this.queue[0];
            this.queue = this.queue.slice(1);
        }
        return ret;
    }

    _send_peers(handler)   {
        /**
        *     .. js:function:: js2p.mesh.mesh_socket._send_peers(handler)
        *
        *         Shortcut method to send a peerlist message. This method is extracted from
        *         :js:func:`~js2p.mesh.mesh_socket.__handle_handshake` in order to allow cleaner
        *         inheritence from :js:class:`js2p.sync.sync_socket`
        */
        handler.send(base.flags.whisper, [base.flags.peers, this.__get_peer_list()]);
    }

    _send_handshake(handler)   {
        /**
        *     .. js:function:: js2p.mesh.mesh_socket._send_handshake(handler)
        *
        *         Shortcut method to send a handshake response. This method is extracted from
        *         :js:func:`~js2p.mesh.mesh_socket.__handle_handshake` in order to allow cleaner
        *         inheritence from :js:class:`js2p.sync.sync_socket`
        */
        let tmp_compress = handler.compression;
        handler.compression = [];
        handler.send(base.flags.whisper, [base.flags.handshake, this.id, this.protocol.id, this.out_addr, base.compression]);
        handler.compression = tmp_compress;
    }

    connect(addr, port, id) {
        /**
        *     .. js:function:: js2p.mesh.mesh_socket.connect(addr, port [, id])
        *
        *         This function connects you to a specific node in the overall network.
        *         Connecting to one node *should* connect you to the rest of the network,
        *         however if you connect to the wrong subnet, the handshake failure involved
        *         is silent. You can check this by looking at the truthiness of this objects
        *         routing table. Example:
        *
        *         .. code-block:: javascript
        *
        *             > var conn = new mesh.mesh_socket('localhost', 4444);
        *             > conn.connect('localhost', 5555);
        *             > //do some other setup for your program
        *             > if (!conn.routing_table)    {
        *             ... conn.connect('localhost', 6666); // any fallback address
        *             ... }
        *
        *         :param string addr: A string address
        *         :param number port: A positive, integral port
        *         :param id:          A string-like object which represents the expected ID of this node
        *
        *         .. note::
        *
        *             While in the Python version there are more thorough checks on this, the Javascript
        *             implementation *can* connect to itself. There are checks to keep this from happening
        *             automatically, but it's still trivial to override this via human intervention. Please
        *             do not try to connect to yourself.
        */
        // self.__print__("Attempting connection to %s:%s with id %s" % (addr, port, repr(id)), level=1)
        // if socket.getaddrinfo(addr, port)[0] == socket.getaddrinfo(*self.out_addr)[0] or \
        //                                                     id in self.routing_table:
        //     self.__print__("Connection already established", level=1)
        //     return false
        var shouldBreak = ((id && id.toString() === this.id.toString()) ||
                (addr === this.out_addr[0] && port === this.out_addr[1]) ||
                (addr === this.addr[0] && port === this.addr[1]));
        var self = this;
        Object.keys(this.routing_table).some(function(key)   {
            if (key === id || self.routing_table[key].addr[0] === addr ||
                self.routing_table[key].addr[1] === port)   {
                shouldBreak = true;
            }
            if (shouldBreak)    {
                return true;
            }
        });
        if (shouldBreak)    {
            return false;
        }
        var conn = base.get_socket(addr, port, this.protocol);
        var handler = new this.conn_type(conn, this, true);
        handler.id = id;
        if (this.protocol.encryption === 'ws' || this.protocol.encryption === 'wss')    {
            if (conn.on)    {
                conn.on('connect', ()=>{
                    self._send_handshake(handler);
                })
            }
            else    {
                var onopen = ()=>{
                    this._send_handshake(handler);
                }
                if (conn.readyState === 1)  {
                    onopen();
                }
                conn.onopen = onopen;
            }
        }
        else if (this.protocol.encryption === 'SSL')    {
            const self = this;
            conn.on('secureConnect', ()=>{
                self._send_handshake(handler);
            })
        }
        else    {
            this._send_handshake(handler);
        }
        if (id) {
            this.routing_table[id] = handler;
        }
        else    {
            this.awaiting_ids.push(handler);
        }
    }

    disconnect(handler) {
        /**
        *     .. js:function:: js2p.mesh.mesh_socket.disconnect(handler)
        *
        *         Closes a given connection, and removes it from your routing tables
        *
        *         :param js2p.mesh.mesh_connection handler: The connection you wish to close
        */
        if (handler.sock.end)   {
            handler.sock.end();
            handler.sock.destroy(); //These implicitly remove from routing table
        }
        else    {
            handler.sock.close();
        }
    }

    handle_msg(msg, conn)    {
        if (!super.handle_msg(msg, conn))   {
            var packs = msg.packets;
            if (packs[0] === base.flags.whisper || packs[0] === base.flags.broadcast) {
                this.queue.push(msg);
                this.emit('message', this);
            }
            // else    {
            //     this.__print__("Ignoring message with invalid subflag", level=4);
            // }
        }
    }

    __get_peer_list()   {
        /**
        *     .. js:function:: js2p.mesh.mesh_socket.__get_peer_list()
        *
        *         This function is used to generate a list-formatted group of your peers. It goes in format ``[ [[addr, port], ID], ...]``
        *
        *         :returns: An array in the above format
        */
        var ret = [];
        var self = this;
        Object.keys(this.routing_table).forEach(function(key)   {
            if (self.routing_table[key].addr)   {
                ret.push([[self.routing_table[key].addr, key]]);
            }
        });
        return ret;
    }

    __handle_handshake(msg, conn)    {
        /**
        *     .. js:function:: js2p.mesh.mesh_socket.__handle_handshake(msg, conn)
        *
        *         This callback is used to deal with handshake signals. Its three primary jobs are:
        *
        *         - reject connections seeking a different network
        *         - set connection state
        *         - deal with connection conflicts
        *
        *         :param js2p.base.message msg:
        *         :param js2p.mesh.mesh_connection conn:
        *
        *         :returns: Either ``true`` or ``undefined``
        */
        var packets = msg.packets;
        if (packets[0] === base.flags.handshake && packets.length === 5) {
            if (packets[2].toString() !== msg.protocol.id) {
                this.disconnect(conn);
                return true;
            }
            // else if (handler is not this.routing_table.get(packets[1], handler))    {
            //     this.__resolve_connection_conflict(handler, packets[1]);
            // }
            conn.id = packets[1];
            if (!conn.addr && Object.keys(this.awaiting_ids).length === 0)  {
                this.emit('connect', this);
            }
            conn.addr = packets[3];
            //console.log(`changed compression methods to: ${packets[4]}`);
            conn.compression = packets[4];
            // self.__print__("Compression methods changed to %s" % repr(handler.compression), level=4)
            if (this.awaiting_ids.indexOf(conn) > -1)   {  // handler in this.awaiting_ids
                this.awaiting_ids.splice(this.awaiting_ids.indexOf(conn), 1);
                this._send_handshake(conn);
            }
            this.routing_table[packets[1]] = conn;
            this._send_peers(conn);
            return true;
        }
    }

    __handle_peers(msg, conn)   {
        /**
        *     .. js:function:: js2p.mesh.mesh_socket.__handle_peers(msg, conn)
        *
        *         This callback is used to deal with peer signals. Its primary jobs is to connect to the given peers, if this does not exceed :js:data:`js2p.mesh.max_outgoing`
        *
        *         :param js2p.base.message msg:
        *         :param js2p.mesh.mesh_connection conn:
        *
        *         :returns: Either ``true`` or ``undefined``
        */
        var packets = msg.packets;
        if (packets[0] === base.flags.peers)  {
            var new_peers = packets[1];
            var self = this;
            new_peers.forEach(function(peer_array)  {
                if (self.outgoing.length < m.max_outgoing)  {
                    // try:
                        var addr = peer_array[0];
                        var id = peer_array[1];
                        if (addr[0] && addr[1])
                            self.connect(addr[0], addr[1], id);
                }
                    // except:  # pragma: no cover
                        // self.__print__("Could not connect to %s:%s because\n%s" % (addr[0], addr[1], traceback.format_exc()), level=1)
                        // continue
            });
            return true;
        }
    }

    __handle_response(msg, conn)    {
        /**
        *     .. js:function:: js2p.mesh.mesh_socket.__handle_response(msg, conn)
        *
        *         This callback is used to deal with response signals. Its two primary jobs are:
        *
        *         - if it was your request, send the deferred message
        *         - if it was someone else's request, relay the information
        *
        *         :param js2p.base.message msg:
        *         :param js2p.mesh.mesh_connection conn:
        *
        *         :returns: Either ``true`` or ``undefined``
        */
        var packets = msg.packets;
        if (packets[0] === base.flags.response)  {
            // self.__print__("Response received for request id %s" % packets[1], level=1)
            if (this.requests[packets[1]])  {
                var addr = packets[2];
                if (addr)   {
                    var info = this.requests[packets[1]];
                    // console.log(msg);
                    this.connect(addr[0][0], addr[0][1], addr[1]);
                    this.routing_table[addr[1]].send(info[1], [...info[2], ...info[0]]);
                    delete this.requests[packets[1]];
                }
            }
            return true;
        }
    }

    __handle_request(msg, conn) {
        /**
        *     .. js:function:: js2p.mesh.mesh_socket.__handle_request(msg, conn)
        *
        *         This callback is used to deal with request signals. Its three primary jobs are:
        *
        *         - respond with a peers signal if packets[1] is ``'*'``
        *         - if you know the ID requested, respond to it
        *         - if you don't, make a request with your peers
        *
        *         :param js2p.base.message msg:
        *         :param js2p.mesh.mesh_connection conn:
        *
        *         :returns: Either ``true`` or ``undefined``
        */
        var packets = msg.packets;
        //console.log(packets[0].toString());
        //console.log(packets[1].toString());
        if (packets[0] === base.flags.request)  {
            if (packets[1].toString() === '*')  {
                this._send_peers(conn);
            }
            else if (this.routing_table[packets[2]])    {
                conn.send(base.flags.broadcast, [base.flags.response, packets[1], [this.routing_table[packets[2]].addr, packets[2]]]);
            }
            return true;
        }
    }

    send(packets, flag, type)  {
        /**
        *     .. js:function:: js2p.mesh.mesh_socket.send(packets [, flag [, type]])
        *
        *         This sends a message to all of your peers. If you use default values it will send it to everyone on the network
        *
        *         :param packets:   A list of strings or Buffer-like objects you want your peers to receive
        *         :param flag:      A string or Buffer-like object which defines your flag. In other words, this defines packet 0.
        *         :param type:      A string or Buffer-like object which defines your message type. Changing this from default can have adverse effects.
        *
        *         .. warning::
        *
        *             If you change the type attribute from default values, bad things could happen. It **MUST** be a value from :js:data:`js2p.base.flags` ,
        *             and more specifically, it **MUST** be either ``broadcast`` or ``whisper``. The only other valid flags are ``waterfall`` and ``renegotiate``,
        *             but these are **RESERVED** and must **NOT** be used.
        */
        var send_type = type || base.flags.broadcast;
        var main_flag = flag || base.flags.broadcast;
        var self = this;
        Object.keys(this.routing_table).forEach(function(key)   {
            self.routing_table[key].send(main_flag, [send_type, ...packets]);
        });
    }

    _in_waterfalls(id, time)    {
        let contained = false;
        this.waterfalls.some(function(entry)    {
            if (!BigInt.isInstance(entry[1])) {
                entry[1] = new BigInt(entry[1]);
            }
            if (entry[0] === id && entry[1].equals(time))   {
                contained = true;
                return true;
            }
        });
        return contained;
    }

    __clean_waterfalls()    {
        /**
        *     .. js:function:: js2p.mesh.mesh_socket.__clean_waterfalls()
        *
        *         This function cleans the list of recently relayed messages based on
        *         the following heurisitics:
        *
        *         - Delete all duplicates
        *         - Delete all older than 60 seconds
        */
        this.waterfalls = Array.from(new Set(this.waterfalls));
        var new_waterfalls = [];
        var filter_time = base.getUTC() - 60;
        for (var i in this.waterfalls)  {
            if (this.waterfalls[i][1] > filter_time) {
                new_waterfalls.push(this.waterfalls[i]);
            }
        }
        this.waterfalls = new_waterfalls;
    }

    waterfall(msg)  {
        /**
        *     .. js:function:: js2p.mesh.mesh_socket.waterfall(msg)
        *
        *         This function handles message relays. Its return value is based on
        *         whether it took an action or not.
        *
        *         :param js2p.base.message msg: The message in question
        *
        *         :returns: ``true`` if the message was then forwarded. ``false`` if not.
        */
        const id = msg.id;
        if (!this._in_waterfalls(id, msg.time)) {
            this.waterfalls.unshift([id, msg.time]);
            var self = this;
            Object.keys(this.routing_table).forEach(function(key)   {
                var handler = self.routing_table[key];
                if (handler.id.toString() !== msg.sender.toString())   {
                    handler.send_InternalMessage(msg.msg);
                }
            });
            this.__clean_waterfalls()
            return true
        }
        else    {
            // this.__print__("Not rebroadcasting", level=3)
            return false
        }
    }
};
