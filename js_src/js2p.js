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

m.bootstrap = function bootstrap(net_id, constrcutor, addr, port, protocol, seeding)  {
    let conn = new m.chord.chord_socket('0.0.0.0', 44565, new m.base.protocol('bootstrapper', 'SSL'));
    if (seeding !== false)  {
        conn.join();
    }
    conn.connect('euclid.nmu.edu', 44565);
    let ret = new constructor(addr, port, protocol);
    conn.get(net_id).then((val)=>{
        for (let addr of JSON.parse(val)) {
            ret.connect(addr[0], addr[1]);
        }
        if (seeding === false) {
            conn.close();
        }
    }, (err)=>{
        console.critical(err);
    });
    return ret;
}
