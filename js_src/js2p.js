"use strict";

var m;

if( typeof exports !== 'undefined' ) {
    if( typeof module !== 'undefined' && module.exports ) {
        m = exports = module.exports;
    }
    m = exports;
}
else {
    root.js2p = {};
    m = root;
}

m.base = require('./base.js');
try {
    m.mesh = require('./mesh.js');
}
catch (e) {
    console.warn('js2p.mesh module not loaded');
}
try {
    m.ford = require('./ford.js');
}
catch (e) {
    console.warn('js2p.ford module not loaded (Did js2p.mesh not load?)');
}
try {
    m.sync = require('./sync.js');
}
catch (e) {
    console.warn('js2p.sync module not loaded (Did js2p.mesh not load?)');
}
try {
    m.chord = require('./chord.js');
}
catch (e) {
    console.warn('js2p.chord module not loaded (Did js2p.mesh not load?)');
}
m.version = m.base.version;
m.version_info = m.base.version_info;

function _get_database()    {
    return {
            'Plaintext': {
                'euclid': ['euclid.nmu.edu', 44565],
                'turing': ['turing.nmu.edu', 44565],
                'p2p.today': ['blog.p2p.today', 44565],
            'SSL': {
                'euclid': ['euclid.nmu.edu', 44566],
                'turing': ['turing.nmu.edu', 44566],
                'p2p.today': ['blog.p2p.today', 44566]},
            'ws': {
                'euclid': ['euclid.nmu.edu', 44567],
                'turing': ['turing.nmu.edu', 44567],
                'p2p.today': ['blog.p2p.today', 44567]}
            }};
}

function _update_database() {}

m.bootstrap = function bootstrap(socket_type, protocol, addr, port, ...args)    {
    let ret = new socket_type(addr, port, protocol, ...args);
    let dict = _get_database();
    let seed_protocol = new m.base.Protocol('bootstrap', protocol.encryption);
    let seed = ret;
    if (protocol.id !== seed_protocol.id || !(m.chord && socket_type === m.chord.ChordSocket))  {
        seed = new m.chord.ChordSocket(addr, Math.floor(Math.random() * 32768) + 32767, seed_protocol);
    }

    if (dict[protocol.encryption] !== undefined)   {
        for (let key of Object.keys(dict[protocol.encryption]))    {
            let seeder = dict[protocol.encryption][key];
            try {
                seed.connect(...seeder);
            }
            catch(e)    {}
        }
    }

    seed.once('connect', function on_connect(_) {
        let request = seed.get(protocol.id);
        let id_ = ret.id;
        request.then(function on_receipt(dct)   {
            for (let key of new Set(Object.keys(dct)))  {
                if (ret.routing_table.size > 4) {
                    break;
                }
                else    {
                    let info = dct[key];
                    try {
                        ret.connect(...info);
                    }
                    catch(e)    {}
                }
            }
            seed.apply_delta(proto.id, {id_: ret.out_addr}).catch(console.warn);
        }).catch((err)=>{
            seed.apply_delta(proto.id, {id_: ret.out_addr}).catch(console.warn);
        });

        for (let id_ of seed.routing_table.keys())  {
            if (dict[proto.encryption][id_] === undefined)   {
                let node = seed.routing_table.get(id_);
                dict[proto.encryption][id_] = node.addr;
            }
        }

        _update_database(dict)
    });

    return ret
}
