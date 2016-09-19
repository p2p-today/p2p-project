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

m.mesh_connection = class mesh_connection extends base.base_connection  {
    constructor(sock, server, outgoing) {
        super(sock, server, outgoing);
    }

    send(msg_type, packs, id, time)  {
        var msg = super.send(msg_type, packs, id, time);
        //add msg to waterfall
    }

    found_terminator()  {
        var msg = super.found_terminator();
        console.log(msg.packets);
        if (this.handle_waterfall(msg, msg.packets))   {
            return true;
        }
        else if (this.handle_renegotiate(msg.packets))  {
            return true;
        }
        this.server.handle_msg(new base.message(msg, this.server), this);
    }

    handle_waterfall(msg, packets)  {
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
}

m.mesh_socket = class mesh_socket extends base.base_socket  {
    constructor(addr, port, protocol, out_addr, debug_level)   {
        super(addr, port, protocol || m.default_protocol, out_addr, debug_level);
        const self = this;
        this.waterfalls = [];
        this.requests = [];
        this.queue = [];
        this.register_handler(function(msg, conn)   {return self.__handle_handshake(msg, conn);});
        this.register_handler(function(msg, conn)   {return self.__handle_peers(msg, conn);});
        this.register_handler(function(msg, conn)   {return self.__handle_response(msg, conn);});
        this.register_handler(function(msg, conn)   {return self.__handle_request(msg, conn);});

        this.incoming.on('connection', function(sock)   {
            const conn = new m.mesh_connection(sock, self, false);
            conn.send(base.flags.whisper, [base.flags.handshake, self.id, self.id, JSON.stringify(self.out_addr), base.json_compressions]);
            self.awaiting_ids = self.awaiting_ids.concat(conn);
        });
    }

    get outgoing()  {
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
            console.log(`changed compression methods to: ${packets[4]}`);
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

    }

    __handle_request(msg, conn) {

    }

    send(packets, flag, type)  {
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
        if (this.waterfalls.indexOf([msg.id, msg.time]) <= -1)  {
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