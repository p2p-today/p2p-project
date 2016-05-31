function p2p() {
    "use strict";
    var m = this;

    var BigInt = require('./BigInteger/BigInteger.js');
    var struct = require('./pack/bufferpack.js');
    var SHA = require('./SHA/src/sha.js');
    var zlib = require('./zlib/bin/node-zlib.js');

    m.version = "0.1.C";
    m.compression = ['gzip'];

    // User salt generation pulled from: http://stackoverflow.com/a/2117523
    m.user_salt = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random()*16|0, v = c == 'x' ? r : (r&0x3|0x8);
        return v.toString(16);
    });

    m.base_58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';

    m.to_base_58 = function(i) {
        //Takes an integer and returns its corresponding base_58 string
        var string = "";
        if (!BigInt.isInstance(i)) {
            i = BigInt(i);
        }
        while (i.notEquals(0)) {
            string = m.base_58[i.mod(58)] + string;
            i = i.divide(58);
        }
        return string;
    };


    m.from_base_58 = function(string) {
        //Takes a base_58 string and returns its corresponding integer
        var decimal = BigInt(0);
        //for char in string {
        for (i = 0; i < string.length; i++) {
            decimal = decimal.times(58).plus(m.base_58.indexOf(string[i]));
        }
        return decimal;
    };


    m.getUTC = function() {
        return Math.floor(Date.now() / 1000);
    };


    m.SHA384 = function(text) {
        var hash = new SHA("SHA-384", "TEXT");
        hash.update(text);
        return hash.getHash("HEX");
    };


    m.SHA256 = function(text) {
        var hash = new SHA("SHA-256", "TEXT");
        hash.update(text);
        return hash.getHash("HEX");
    };


    m.compress = function(text, method) {
        if (method == "gzip") {
            return zlib.deflateSync(Buffer(text));
        }
        else {
            throw "Unknown compression method";
        }
    };


    m.decompress = function(text, method) {
        if (method == "gzip") {
            return zlib.inflateSync(Buffer(text));
        }
        else {
            throw "Unknown compression method";
        }
    };


    m.protocol = class protocol {
        constructor(sep, subnet, encryption) {
            this.sep = sep;
            this.subnet = subnet;
            this.encryption = encryption;
        }

        id() {
            var protocol_hash = m.SHA256([this.sep, this.subnet, this.encryption, m.version].join(''));
            return m.to_base_58(BigInt(protocol_hash, 16));
        }
    };

    m.default_protocol = m.protocol(Buffer([28, 29, 30, 31]), '', 'Plaintext');


    m.construct_message = function(prot, comp_types, msg_type, id, packets, time) {
        var time = typeof time !== 'undefined' ?  time : m.to_base_58(m.getUTC());

        var msg_hash = m.SHA384(packets.join(prot.sep) + time);
        var msg_id = m.to_base_58(BigInt(msg_hash, 16));

        var packets = [msg_type, id, msg_id, time].concat(packets);
        var msg = new Buffer(packets.join(prot.sep));

        //compression_used = ""
        //for method in compression:
        //    if method in comp_types:
        //        compression_used = method
        //        msg = compress(msg, method)
        //        break

        var size = struct.pack("!L", [msg.length]);
        return [size, msg];
    }
}

if( typeof exports !== 'undefined' ) {
    if( typeof module !== 'undefined' && module.exports ) {
        exports = module.exports = new p2p()
    }
    exports.p2p = new p2p()
} 
else {
    root.p2p = new p2p()
}