/**
* Ford Module
* ===========
*/

"use strict";

const BigInt = require('big-integer');
const base = require('./base.js');
const flags = base.flags;
const mesh = require('./mesh.js');
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
    root.ford = {};
    m = root;
}

m.max_outgoing = 4;

m.default_protocol = new base.Protocol('ford', "Plaintext");
/**
* .. js:data:: js2p.ford.default_protocol
*
*     A :js:class:`~js2p.base.Protocol` object which is used by default in the ford module
*/

m.FordConnection = class FordConnection extends mesh.MeshConnection  {
    /**
    * .. js:class:: js2p.ford.FordConnection(sock, server, outgoing)
    *
    *     This is the class for ford connection abstractraction. It inherits from :js:class:`js2p.mesh.MeshConnection`
    *
    *     :param sock:                          This is the raw socket object
    *     :param js2p.ford.FordSocket server:  This is a link to the :js:class:`~js2p.ford.FordSocket` parent
    *     :param outgoing:                      This bool describes whether ``server`` initiated the connection
    */
    constructor(sock, server, outgoing) {
        super(sock, server, outgoing);
    }
}

m.FordSocket = class FordSocket extends mesh.MeshSocket  {
    /**
    * .. js:class:: js2p.ford.FordSocket(addr, port [, protocol [, out_addr [, debug_level]]])
    *
    *     This is the class for ford network socket abstraction. It inherits from :js:class:`js2p.mesh.MeshSocket`
    *
    *     :param string addr:                   The address you'd like to bind to
    *     :param number port:                   The port you'd like to bind to
    *     :param js2p.base.Protocol protocol:   The subnet you're looking to connect to
    *     :param array out_addr:                Your outward-facing address
    *     :param number debug_level:            The verbosity of debug prints
    *
    *     .. js:attribute:: js2p.ford.FordSocket.routes
    *
    *         A :js:class:`Map` which contains the path to all other nodes keyed by their IDs
    *
    */
    constructor(addr, port, protocol, out_addr, debug_level)   {
        super(addr, port, protocol || m.default_protocol, out_addr, debug_level);
        var self = this;
        this.conn_type = m.FordConnection;
        this.routes = {};
        this.routes[this.id] = [];
        this.register_handler(function handle_new_paths(msg, conn)  {return self.__handle_new_paths(msg, conn);});
        this.register_handler(function handle_del_paths(msg, conn)  {return self.__handle_del_paths(msg, conn);});
        this.register_handler(function handle_forward(msg, conn)    {return self.__handle_forward(msg, conn);});
    }

    __on_TCP_Connection(sock)  {
        let conn = super.__on_TCP_Connection(sock);
        this._send_paths(conn);
        return conn;
    }

    __on_WS_Connection(sock)  {
        let conn = super.__on_WS_Connection(sock);
        this._send_paths(conn);
        return conn;
    }

    disconnect(handler) {
        let _id = handler.id;
        super.disconnect(handler)
        let path = this.routes[_id];
        if (path !== undefined) {
            delete this.routes[_id];
            for (let key of this.routing_table.keys())  {
                this.routing_table.get(key).send(flags.whisper, [flags.revoke_paths, {_id: path}])
            }
        }
    }

    __handle_new_paths(msg, handler)    {
        let packets = msg.packets;
        if (packets[0] === flags.new_paths) {
            let respond = false;
            for (let dest in packets[1])    {
                let route = packets[1][dest];
                if (this.routes[dest] === undefined || route.length < this.routes[dest].length) {
                    this.routes[dest] = route;
                    respond = true;
                }
            }
            if (respond)    {
                for (let key of this.routing_table.keys())   {
                    this._send_paths(this.routing_table.get(key));
                }
            }
            return true;
        }
    }

    __handle_del_paths(msg, handler)    {
        let packets = msg.packets;
        if (packets[0] === flags.revoke_paths)  {
            let respond = false;
            for (let dest in packets[1])    {
                let route = packets[1][dest];
                if (route !== undefined && route === this.routes[dest]) {
                    delete this.routes[dest];
                    respond = true;
                }
            }
            if (respond)    {
                for (let key of this.routing_table.keys())  {
                    this._send_paths(this.routing_table.get(key));
                }
            }
            return true;
        }
    }

    __handle_forward(msg, handler)  {
        let packets = msg.packets;
        if (packets[0] === flags.forward)   {
            let dest = packets[1];
            if (this.routes[dest])  {
                let path = this.routes[dest];
                let imsg = msg.msg;
                if (path[0] === dest)   {
                    imsg.payload = packets.slice(2);
                }
                this.routing_table.get(path[0]).send_InternalMessage(imsg);
            }
            return true;
        }
    }

    _send_paths(handler)    {
        let to_send = {};
        for (let dest in this.routes)   {
            let path = this.routes[dest];
            to_send[dest] = [this.id, ...path];
        }
        console.log(`sending paths: ${util.inspect(to_send)}`);
        handler.send(flags.whisper, [flags.new_paths, to_send]);
    }

    sendTo(dest, packets, flag, type)   {
        let path = this.routes[dest];
        let send_type = type || flags.whisper;
        let main_flag = flag || flags.whisper;
        if (path[0] !== dest)   {
            this.routing_table.get(path[0]).send(main_flag, [flags.forward, dest, send_type, ...packets]);
        }
        else    {
            this.routing_table.get(path[0]).send(main_flag, [send_type, ...packets]);
        }
    }
};
