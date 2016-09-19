"use strict";

const BigInt = require('./BigInteger/BigInteger.js');
const SHA = require('./SHA/src/sha.js');
const zlib = require('./zlib/bin/node-zlib.js');
const assert = require('assert');

if (buffer.kMaxLength < 4294967299) {
    console.log(`WARNING: This implementation of javascript does not support the maximum protocol length. The largest message you may receive is 4294967299 bytes, but you can only allocate ${buffer.kMaxLength}, or ${(buffer.kMaxLength / 4294967299 * 100).toFixed(2)}% of that.`);
}

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

m.version_info = [0, 4, 319];
m.node_policy_version = m.version_info[2].toString();
m.protocol_version = m.version_info.slice(0, 2).join(".");
m.version = m.version_info.join('.');

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

m.compression = [];// [m.flags.zlib, m.flags.gzip];
m.json_compressions = JSON.stringify(m.compression);

// User salt generation pulled from: http://stackoverflow.com/a/2117523
m.user_salt = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random()*16|0;
    const v = c === 'x' ? r : (r&0x3|0x8);
    return v.toString(16);
});

m.unpack_value = function(str)  {
    str = new Buffer(str, 'ascii');
    var val = BigInt.zero;
    for (var i = 0; i < str.length; i++)    {
        val = val.shiftLeft(8);
        val = val.add(str[i]);
    }
    return val;
}

m.pack_value = function(len, i) {
    var arr = new Buffer(new Array(len));
    for (var j = 0; j < len && i != 0; j++)    {
        arr[len - j - 1] = i & 0xff;
        i = i >> 8;
    }
    return arr;
}

m.base_58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';

m.to_base_58 = function(i) {
    //Takes an integer and returns its corresponding base_58 string
    var string = "";
    if (!BigInt.isInstance(i)) {
        i = new BigInt(i);
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
        var decimal = new BigInt(0);
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
        return zlib.deflateSync(new Buffer(text));
    }
    else if (method === m.flags.gzip) {
        return zlib.gzipSync(new Buffer(text));
    }
    else {
        throw "Unknown compression method";
    }
};


m.decompress = function(text, method) {
    if (method === m.flags.zlib) {
        return zlib.inflateSync(new Buffer(text));
    }
    else if (method === m.flags.gzip) {
        return zlib.gunzipSync(new Buffer(text));
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

    get id() {
        var protocol_hash = m.SHA256([this.subnet, this.encryption, m.protocol_version].join(''));
        return m.to_base_58(new BigInt(protocol_hash, 16));
    }
};

m.default_protocol = new m.protocol('', 'Plaintext');

m.pathfinding_message = class pathfinding_message {
    constructor(msg_type, sender, payload, compression, timestamp) {
        this.msg_type = new Buffer(msg_type);
        this.sender = new Buffer(sender);
        this.payload = payload || [];
        for (var i = 0; i < this.payload.length; i++)   {
            this.payload[i] = new Buffer(this.payload[i]);
        }
        this.time = timestamp || m.getUTC();
        this.compression = compression || [];
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
            string = new Buffer(string)
        }
        finally {
            if (!sizeless) {
                if (m.unpack_value(string.slice(0,4)) + 4 !== string.length) {
                    console.log(`slice given: ${string.slice(0, 4).inspect()}.  Value expected: ${string.length - 4}.  Value derived: ${m.unpack_value(string.slice(0, 4))}`)
                    throw "The following expression must be true: unpack_value(string.slice(0,4)) === string.length - 4"
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
        var processed = 0;
        var expected = string.length;
        var pack_lens = [];
        var packets = [];
        while (processed < expected) {
            pack_lens = pack_lens.concat(m.unpack_value(new Buffer(string.slice(processed, processed+4))));
            processed += 4;
            expected -= pack_lens[pack_lens.length - 1];
        }
        if (processed > expected)   {
            throw `Could not parse correctly processed=${processed}, expected=${expected}, pack_lens=${pack_lens}`;
        }
        // Then reconstruct the packets
        for (var i=0; i < pack_lens.length; i++) {
            var end = processed + pack_lens[i];
            packets = packets.concat([string.slice(processed, end)]);
            processed = end;
        }
        return packets;
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
        return m.to_base_58(new BigInt(payload_hash, 16))
    }

    get packets() {
        var meta = [this.msg_type, this.sender, this.id, this.time_58]
        return meta.concat(this.payload)
    }

    get __non_len_string() {
        var string = this.packets.join('')
        var headers = []
        for (var i = 0; i < this.packets.length; i++) {
            headers = headers.concat(m.pack_value(4, this.packets[i].length))
        }
        string = Buffer.concat(headers.concat(new Buffer(string, 'ascii')));
        if (this.compression_used) {
            string = m.compress(string, this.compression_used)
        }
        return string
    }

    get string() {
        var string = this.__non_len_string
        return Buffer.concat([m.pack_value(4, string.length), string]);
    }

    get length() {
        return this.__non_len_string.length
    }

    len() {
        return pack_vlaue(4, this.length)
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

    get protocol()  {
        return this.server.protocol
    }

    reply(args) {
        throw "Not implemented"
    }
};

m.base_connection = class base_connection   {
    constructor(sock, server, outgoing)   {
        this.sock = sock;
        this.server = server;
        this.outgoing = outgoing | false;
        this.buffer = new Buffer(0);
        this.id = null;
        this.time = m.getUTC();
        this.addr = null;
        this.compression = [];
        this.last_sent = [];
        this.expected = 4;
        this.active = false;
        const self = this;

        this.sock.on('data', function(data) {
            self.collect_incoming_data(self, data);
        });
    }

    send(msg_type, packs, id, time)  {
        /**Sends a message through its connection.
        *
        * Args:
        *     msg_type:   Message type, corresponds to the header in a py2p.base.pathfinding_message object
        *     packs:      A list of Buffer-like objects, which correspond to the packets to send to you
        *     id:         The ID this message should appear to be sent from (default: your ID)
        *     time:       The time this message should appear to be sent from (default: now in UTC)
        *
        * Returns:
        *     the pathfinding_message object you just sent, or None if the sending was unsuccessful
        **/

        //This section handles waterfall-specific flags
        id = id || this.server.id;  //Latter is returned if key not found
        time = time || m.getUTC();
        //Begin real method
        const msg = new m.pathfinding_message(msg_type, id, packs, this.compression, time);
        if (msg_type === m.flags.whisper || msg_type === m.flags.broadcast) {
            this.last_sent = [msg_type].concat(packs);
        }
        // this.__print__(`Sending ${[msg.len()].concat(msg.packets)} to ${this}`, 4);
        if (msg.compression_used)   {
            console.log(`Compressing with ${JSON.stringify(msg.compression_used)}`);
            // self.__print__(`Compressing with ${msg.compression_used}`, level=4)
        }
        // try {
            console.log(`Sending message ${JSON.stringify(msg.string.toString())} to ${this.id}`);
            this.sock.write(msg.string, 'ascii')
            return msg
        // }
        // catch(e)   {
        //     self.server.daemon.exceptions.append((e, traceback.format_exc()))
        //     self.server.disconnect(self)
        // }
    }

    get protocol()  {
        return this.server.protocol;
    }

    collect_incoming_data(self, data) {
        self.buffer = Buffer.concat([self.buffer, data]);
        console.log(self.buffer);
        self.time = m.getUTC();
        if (!self.active && self.buffer.length >= self.expected) {
            // this.__print__(this.buffer, this.expected, this.find_terminator(), level=4)
            self.expected = m.unpack_value(self.buffer.slice(0, 4)).add(4);
            self.active = true;
            // this.found_terminator();
        }
        if (self.active && self.buffer.length >= self.expected) {
            self.found_terminator();
        }
        return true;
    }

    found_terminator()  {
        console.log("I got called");
        var msg = m.pathfinding_message.feed_string(this.buffer.slice(0, this.expected), false, this.compression);
        this.buffer = this.buffer.slice(this.expected);
        this.expected = 4;
        this.active = false;
        return msg;
    }

    handle_renegotiate(packets) {

    }

    __print__() {

    }
};

m.base_socket = class base_socket   {
    constructor(addr, port, protocol, out_addr, debug_level)   {
        const self = this;
        this.addr = [addr, port];
        this.incoming = new net.Server();
        this.incoming.listen(port, addr);
        this.protocol = protocol || m.default_protocol;
        this.out_addr = out_addr || this.addr;
        this.debug_level = debug_level || 0;

        this.awaiting_ids = [];
        this.routing_table = {};
        this.id = m.to_base_58(BigInt(m.SHA384(`(${addr}, ${port})${this.protocol.id}${m.user_salt}`), 16));
        this.__handlers = [];
    }

    register_handler(callback)  {
        this.__handlers = this.__handlers.concat(callback);
    }

    handle_msg(msg, conn) {
        this.__handlers.some(function(handler)  {
            // self.__print__("Checking handler: %s" % handler.__name__, level=4)
            console.log(`Entering handler ${handler.name}`);
            if (handler(msg, conn)) {
                // self.__print__("Breaking from handler: %s" % handler.__name__, level=4)
                console.log(`breaking from ${handler.name}`);
                return true
            }
        });
    }
};