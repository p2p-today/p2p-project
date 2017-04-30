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
                'p2p.today': ['blog.p2p.today', 44565]
            },
            'SSL': {
                'euclid': ['euclid.nmu.edu', 44566],
                'turing': ['turing.nmu.edu', 44566],
                'p2p.today': ['blog.p2p.today', 44566]
            },
            'ws': {
                'euclid': ['euclid.nmu.edu', 44567],
                'turing': ['turing.nmu.edu', 44567],
                'p2p.today': ['blog.p2p.today', 44567]
            }
        };
}

function _update_database() {}

m.bootstrap = function bootstrap(socket_type, protocol, addr, port, ...args)    {
    let ret = new socket_type(addr, port, protocol, ...args);
    let dict = _get_database();
    let seed_protocol = new m.base.Protocol('bootstrap', protocol.encryption);
    let seed = ret;
    if (ret.protocol.id !== seed_protocol.id || !(m.chord && socket_type === m.chord.ChordSocket))  {
        if (ret.port)   {
            seed = new m.chord.ChordSocket(addr, Math.floor(Math.random() * 32768) + 32767, seed_protocol);
        }
        else {
            seed = new m.chord.ChordSocket(null, null, seed_protocol);
        }
    }

    seed.once('connect', ()=>{
        let delta = {};
        delta[ret.id] = ret.out_addr;
        let request = seed.apply_delta(ret.protocol.id, delta);

        let on_error = (e)=>{
            console.warn(e);
            seeder.close();
        }

        request.catch(on_error);
        request.then((dct)=>{
            for (let key of new Set(Object.keys(dct)))  {
                if (ret.routing_table.size > 4) {
                    break;
                }
                else    {
                    let info = dct[key];
                    try {
                        console.log(`Attempting connection to ${util.inspect(info)}`);
                        ret.connect(...info);
                    }
                    catch(e)    {
                        console.warn(e);
                    }
                }
            }
            seed.close();
        }).catch(on_error);

        for (let id_ of seed.routing_table.keys())  {
            if (dict[ret.protocol.encryption][id_] === undefined)   {
                let node = seed.routing_table.get(id_);
                dict[ret.protocol.encryption][id_] = node.addr;
            }
        }

        _update_database(dict)
    });

    if (dict[ret.protocol.encryption] !== undefined)   {
        for (let key of Object.keys(dict[ret.protocol.encryption]))    {
            let seeder = dict[ret.protocol.encryption][key];
            try {
                seed.connect(...seeder);
            }
            catch(e)    {}
        }
    }

    return ret
}
