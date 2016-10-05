/**
* Mesh Module
* ===========
*/

"use strict";

const base = require('./base.js');

var m;

if( typeof exports !== 'undefined' ) {
    if( typeof module !== 'undefined' && module.exports ) {
        m = exports = module.exports;
    }
    m = exports;
}
else {
    root.p2p = {};
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
        *         :param msg_type:      Message type, corresponds to the header in a :js:class:`~js2p.base.pathfinding_message` object
        *         :param packs:         A list of Buffer-like objects, which correspond to the packets to send to you
        *         :param id:            The ID this message should appear to be sent from (default: your ID)
        *         :param number time:   The time this message should appear to be sent from (default: now in UTC)
        *
        *         :returns: ``undefined``
        */
        // console.log(msg_type);
        // console.log(packs);
        var msg = super.send(msg_type, packs, id, time);
        //add msg to waterfall
    }

    found_terminator()  {
        /**
        *     .. js:function:: js2p.mesh.mesh_connection.found_terminator()
        *
        *         This method is called when the expected amount of data is received
        *
        *         :returns: ``undefined``
        */
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

    handle_waterfall(msg, packets)  {
        /**
        *     .. js:function:: js2p.mesh.mesh_connection.handle_waterfall(msg, packets)
        *
        *         This method determines whether this message has been previously received or not.
        *         If it has been previously received, this method returns ``true``.
        *         If it is older than a preset limit, this method returns ``true``.
        *         Otherwise this method returns ``undefined``, and forwards the message appropriately.
        *
        *         :param js2p.base.pathfinding_message msg: The message in question
        *         :param packets:                           The message's packets
        *
        *         :returns: ``true`` or ``undefined``
        */
        if (packets[0] == base.flags.waterfall || packets[0] == base.flags.broadcast) {
            if (base.from_base_58(packets[3]) < base.getUTC() - 60) {
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
        this.sock.end();
        this.sock.destroy();
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
    *     .. js:attribute:: js2p.mesh.mesh_socket.routing_table
    *
    *         An object which contains :js:class:`~js2p.mesh.mesh_connection` s keyed by their IDs
    *
    *     .. js:attribute:: js2p.mesh.mesh_socket.awaiting_ids
    *
    *         An array which contains :js:class:`~js2p.mesh.mesh_connection` s that are awaiting handshake information
    */
    constructor(addr, port, protocol, out_addr, debug_level)   {
        super(addr, port, protocol || m.default_protocol, out_addr, debug_level);
        const self = this;
        this.waterfalls = [];
        this.requests = {};
        this.queue = [];
        this.register_handler(function handle_handshake(msg, conn)  {return self.__handle_handshake(msg, conn);});
        this.register_handler(function handle_peers(msg, conn)      {return self.__handle_peers(msg, conn);});
        this.register_handler(function handle_response(msg, conn)   {return self.__handle_response(msg, conn);});
        this.register_handler(function handle_request(msg, conn)    {return self.__handle_request(msg, conn);});

        this.incoming.on('connection', function onConnection(sock)   {
            const conn = new m.mesh_connection(sock, self, false);
            conn.send(base.flags.whisper, [base.flags.handshake, self.id, self.protocol.id, JSON.stringify(self.out_addr), base.json_compressions]);
            self.awaiting_ids = self.awaiting_ids.concat(conn);
        });
    }

    get outgoing()  {
        /**
        *     .. js:attribute:: js2p.mesh.mesh_socket.outgoing
        *
        *         This is an array of all outgoing connections. The length of this array is used to determine
        *         whether the "socket" should automatically initiate connections
        */
        var outs = [];
        const self = this;
        Object.keys(this.routing_table).forEach(function(key)   {
            if (self.routing_table[key].outgoing)   {
                outs.push(self.routing_table[key]);
            }
        });
        return outs;
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

    connect(addr, port, id) {
        // self.__print__("Attempting connection to %s:%s with id %s" % (addr, port, repr(id)), level=1)
        // if socket.getaddrinfo(addr, port)[0] == socket.getaddrinfo(*self.out_addr)[0] or \
        //                                                     id in self.routing_table:
        //     self.__print__("Connection already established", level=1)
        //     return false
        var shouldBreak = (id == this.id || [addr, port] == this.out_addr || [addr, port] == this.addr);
        const self = this;
        Object.keys(this.routing_table).some(function(key)   {
            if (key == id || self.routing_table[key].addr == [addr, port])   {
                shouldBreak = true;
            }
            if (shouldBreak)    {
                return true;
            }
        });
        if (shouldBreak)    {
            return false;
        }
        var conn = new net.Socket();
        // conn.settimeout(1)
        conn.connect(port, addr);
        var handler = new m.mesh_connection(conn, this, true);
        handler.id = id;
        handler.send(base.flags.whisper, [base.flags.handshake, this.id, this.protocol.id, JSON.stringify(this.out_addr), base.json_compressions]);
        if (id) {
            this.routing_table[id] = handler;
        }
        else    {
            this.awaiting_ids = this.awaiting_ids.concat(handler);
        }
    }

    disconnect(handler) {
        handler.sock.end();
        handler.sock.destroy(); //These implicitly remove from routing table
    }

    handle_msg(msg, conn)    {
        if (!super.handle_msg(msg, conn))   {
            const packs = msg.packets;
            if (packs[0] == base.flags.whisper || packs[0] == base.flags.broadcast) {
                this.queue = this.queue.concat(msg);
            }
            // else    {
            //     this.__print__("Ignoring message with invalid subflag", level=4);
            // }
        }
    }

    __get_peer_list()   {
        var ret = [];
        const self = this;
        Object.keys(this.routing_table).forEach(function(key)   {
            ret = ret.concat([[self.routing_table[key].addr, key]]);
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
        const packets = msg.packets;
        if (packets[0].toString() == base.flags.handshake)  {
            if (packets[2] != msg.protocol.id) {
                this.disconnect(conn);
                return true;
            }
            // else if (handler is not this.routing_table.get(packets[1], handler))    {
            //     this.__resolve_connection_conflict(handler, packets[1]);
            // }
            conn.id = packets[1];
            conn.addr = JSON.parse(packets[3]);
            //console.log(`changed compression methods to: ${packets[4]}`);
            conn.compression = JSON.parse(packets[4]);
            // self.__print__("Compression methods changed to %s" % repr(handler.compression), level=4)
            if (this.awaiting_ids.indexOf(conn) > -1)   {  // handler in this.awaiting_ids
                this.awaiting_ids.splice(this.awaiting_ids.indexOf(conn), 1);
            }
            this.routing_table[packets[1]] = conn;
            conn.send(base.flags.whisper, [base.flags.peers, JSON.stringify(this.__get_peer_list())]);
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
        const packets = msg.packets;
        if (packets[0].toString() == base.flags.peers)  {
            var new_peers = JSON.parse(packets[1]);
            const self = this;
            new_peers.forEach(function(peer_array)  {
                if (self.outgoing.length < m.max_outgoing)  {
                    // try:
                        var addr = peer_array[0];
                        var id = peer_array[1];
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
        const packets = msg.packets;
        if (packets[0].toString() == base.flags.response)  {
            // self.__print__("Response received for request id %s" % packets[1], level=1)
            if (this.requests[packets[1]])  {
                var addr = JSON.parse(packets[2]);
                if (addr)   {
                    var msg = this.requests[packets[1]];
                    // console.log(msg);
                    this.connect(addr[0][0], addr[0][1], addr[1]);
                    this.routing_table[addr[1]].send(msg[1], [msg[2]].concat(msg[0]));
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
        const packets = msg.packets;
        //console.log(packets[0].toString());
        //console.log(packets[1].toString());
        if (packets[0].toString() == base.flags.request)  {
            if (packets[1].toString() == '*')  {
                conn.send(base.flags.whisper, [base.flags.peers, JSON.stringify(this.__get_peer_list())]);
            }
            else if (this.routing_table[packets[2]])    {
                conn.send(base.flags.broadcast, [base.flags.response, packets[1], JSON.stringify([this.routing_table[packets[2]].addr, packets[2]])]);
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
        const send_type = type || base.flags.broadcast;
        const main_flag = flag || base.flags.broadcast;
        const self = this;
        Object.keys(this.routing_table).forEach(function(key)   {
            self.routing_table[key].send(main_flag, [send_type].concat(packets));
        });
    }

    __clean_waterfalls()    {
        this.waterfalls = Array.from(new Set(this.waterfalls));
        var new_waterfalls = [];
        const filter_time = base.getUTC() - 60;
        for (var i in this.waterfalls)  {
            if (this.waterfalls[i][1] > filter_time) {
                new_waterfalls.push(this.waterfalls[i]);
            }
        }
        this.waterfalls = new_waterfalls;
    }

    waterfall(msg)  {
        var contained = false;
        this.waterfalls.some(function(entry)    {
            if (entry[0] === msg.id && entry[1].equals(msg.time))   {
                contained = true;
                return true;
            }
        });
        if (!contained)  {
            this.waterfalls.unshift([msg.id, msg.time]);
            const self = this;
            Object.keys(this.routing_table).forEach(function(key)   {
                const handler = self.routing_table[key];
                if (handler.id.toString() !== msg.sender.toString())   {
                    handler.send(base.flags.waterfall, msg.packets, msg.sender, msg.time);
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
