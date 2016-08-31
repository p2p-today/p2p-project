var BigInt = require('./BigInteger/BigInteger.js');
var struct = require('./pack/bufferpack.js');
var SHA = require('./SHA/src/sha.js');
var zlib = require('./zlib/bin/node-zlib.js');
const assert = require('assert');

function p2p() {
    "use strict";
    var m = this;

    if (!Array.prototype.last) {
        Array.prototype.last = function() {
            return this[this.length - 1];
        };
    }

    m.protocol_version = "0.4";
    m.node_policy_version = "319";

    m.version = [m.protocol_version, m.node_policy_version].join('.');

    m.flags = {
        //main flags
        broadcast:   '\x00',
        waterfall:   '\x01',
        whisper:     '\x02',
        renegotiate: '\x03',
        ping:        '\x04',
        pong:        '\x05',

        //sub-flags
        //broadcast: '\x00',
        compression: '\x01',
        //whisper:   '\x02',
        handshake:   '\x03',
        //ping:      '\x04',
        //pong:      '\x05',
        notify:      '\x06',
        peers:       '\x07',
        request:     '\x08',
        resend:      '\x09',
        response:    '\x0A',
        store:       '\x0B',
        retrieve:    '\x0C',

        //compression methods
        bz2:      '\x10',
        gzip:     '\x11',
        lzma:     '\x12',
        zlib:     '\x13',
        bwtc:     '\x14',
        context1: '\x15',
        defsum:   '\x16',
        dmc:      '\x17',
        fenwick:  '\x18',
        huffman:  '\x19',
        lzjb:     '\x1A',
        lzjbr:    '\x1B',
        lzp3:     '\x1C',
        mtf:      '\x1D',
        ppmd:     '\x1E',
        simple:   '\x1F'
    };

    m.compression = [m.flags.zlib, m.flags.gzip];

    // User salt generation pulled from: http://stackoverflow.com/a/2117523
    m.user_salt = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random()*16|0, v = c === 'x' ? r : (r&0x3|0x8);
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
        try {
            string = string.toString()
        }
        finally {
            var decimal = BigInt(0);
            //for char in string {
            for (var i = 0; i < string.length; i++) {
                decimal = decimal.times(58).plus(m.base_58.indexOf(string[i]));
            }
            return decimal;
        }
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
        if (method === m.flags.zlib) {
            return zlib.deflateSync(Buffer(text));
        }
        else if (method === m.flags.gzip) {
            return zlib.gzipSync(Buffer(text));
        }
        else {
            throw "Unknown compression method";
        }
    };


    m.decompress = function(text, method) {
        if (method === m.flags.zlib) {
            return zlib.inflateSync(Buffer(text));
        }
        else if (method === m.flags.gzip) {
            return zlib.gunzipSync(Buffer(text));
        }
        else {
            throw "Unknown compression method";
        }
    };


    m.protocol = class protocol {
        constructor(subnet, encryption) {
            this.subnet = subnet;
            this.encryption = encryption;
        }

        id() {
            var protocol_hash = m.SHA256([this.subnet, this.encryption, m.protocol_version].join(''));
            return m.to_base_58(BigInt(protocol_hash, 16));
        }
    };

    m.default_protocol = new m.protocol('', 'Plaintext');

    m.pathfinding_message = class pathfinding_message {
        constructor(msg_type, sender, payload, compression) {
            this.msg_type = Buffer(msg_type)
            this.sender = Buffer(sender)
            this.payload = payload
            for (var i = 0; i < this.payload.length; i++)   {
                this.payload[i] = Buffer(this.payload[i])
            }
            this.time = m.getUTC()
            if (compression) {
                this.compression = compression
            }
            else {
                this.compression = []
            }
            this.compression_fail = false
        }

        static feed_string(string, sizeless, compressions) {
            string = m.pathfinding_message.sanitize_string(string, sizeless)
            var compression_return = m.pathfinding_message.decompress_string(string, compressions)
            var compression_fail = compression_return[1]
            string = compression_return[0]
            var packets = m.pathfinding_message.process_string(string)
            var msg = new m.pathfinding_message(packets[0], packets[1], packets.slice(4), compressions)
            msg.time = m.from_base_58(packets[3])
            msg.compression_fail = compression_fail
            assert (msg.id === packets[2].toString(), `ID check failed. ${msg.id} !== ${packets[2].toString()}`)
            return msg
        }

        static sanitize_string(string, sizeless) {
            try {
                string = Buffer(string)
            }
            finally {
                if (!sizeless) {
                    if (struct.unpack("!L", string.slice(0,4))[0] !== string.length - 4) {
                        throw "The following expression must be true: struct.unpack(\"!L\", string.slice(0,4))[0] === string.length - 4"
                    }
                    string = string.slice(4)
                }
                return string
            }
        }

        static decompress_string(string, compressions) {
            var compression_fail = false
            compressions = compressions || []
            for (var i = 0; i < compressions.length; i++) {
                console.log(`Checking ${compressions[i]} compression`)
                if (m.compression.indexOf(compressions[i]) > -1) {  // module scope compression
                    console.log(`Trying ${compressions[i]} compression`)
                    try {
                        string = m.decompress(string, compressions[i])
                        compression_fail = false
                        console.log(`Compression ${compressions[i]} succeeded`)
                        break
                    }
                    catch(err) {
                        compression_fail = true
                        console.log(`compresion ${compressions[i]} failed: ${err}`)
                        continue
                    }
                }
            }
            return [string, compression_fail]
        }

        static process_string(string) {
            var processed = 0
            var expected = string.length
            var pack_lens = []
            var packets = []
            function add(a, b) {
                return a + b
            }
            while (processed < expected) {
                pack_lens = pack_lens.concat(struct.unpack("!L", Buffer(string.slice(processed, processed+4))))
                processed += 4
                expected -= pack_lens.last()
            }
            if (processed > expected)   {
                throw [`Could not parse correctly processed=${processed}, expected=${expected}, pack_lens=${pack_lens}`]
            }
            // Then reconstruct the packets
            var start = processed;
            for (var i=0; i < pack_lens.length; i++) {
                var end = start + pack_lens[i]
                packets = packets.concat([string.slice(start, end)])
                start = end
            }
            return packets
        }

        get compression_used() {
            for (var i = 0; i < m.compression.length; i++) {
                for (var j = 0; j < this.compression.length; j++) {
                    if (m.compression[i] === this.compression[j]) {
                        return m.compression[i]
                    }
                }
            }
            return null
        }

        get time_58() {
            return m.to_base_58(this.time)
        }

        get id() {
            var payload_string = this.payload.join('')
            var payload_hash = m.SHA384(payload_string + this.time_58)
            return m.to_base_58(BigInt(payload_hash, 16))
        }

        get packets() {
            var meta = [this.msg_type, this.sender, this.id, this.time_58]
            return meta.concat(this.payload)
        }

        get __non_len_string() {
            var string = this.packets.join('')
            var headers = []
            for (var i = 0; i < this.packets.length; i++) {
                headers = headers.concat(struct.pack("!L", [this.packets[i].length]))
            }
            string = headers.join('') + string
            if (this.compression_used) {
                string = m.compress(string, this.compression_used)
            }
            return string
        }
        
        get string() {
            var string = this.__non_len_string
            return struct.pack("!L", [string.length]) + string
        }

        get length() {
            return this.__non_len_string.length
        }

        len() {
            return struct.pack("!L", [this.length])
        }
    };

    m.message = class message {
        constructor(msg, server) {
            this.msg = msg
            this.server = server
        }

        get time() {
            return this.msg.time
        }

        get sender() {
            return this.msg.sender
        }

        get id() {
            return this.msg.id
        }

        get packets() {
            return this.msg.payload
        }

        get length() {
            return this.msg.length
        }

        reply(args) {
            throw "Not implemented"
        }
    };
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