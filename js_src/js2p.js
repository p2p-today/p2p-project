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

m.bootstrap = function bootstrap(net_id, constrcutor, addr, port, protocol, seeding)  {
    throw new Error("Not yet implemented (see #130)");
}
