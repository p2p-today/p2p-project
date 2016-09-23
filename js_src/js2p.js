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
m.mesh = require('./mesh.js');
m.version = m.base.version;
m.version_info = m.base.version_info;

m.bootstrap = function bootstrap()  {
    throw "Not Implemented";
}
