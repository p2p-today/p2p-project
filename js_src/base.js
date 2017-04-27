/**
* Base Module
* ===========
*
* This module contains common classes and functions which are used throughout the rest of the js2p library.
*/

"use strict";

const buffer = require('buffer');  // These ensure parser compatability with browserify
const Buffer = buffer.Buffer;
const BigInt = require('big-integer');
const EventEmitter = require('events');
const SHA = require('jssha');
const util = require('util');
const msgpack = require('msgpack-lite');

/**
* .. note::
*
*     This library will likely issue a warning over the size of data that :js:class:`Buffer` can hold. On most implementations
*     of Javascript this is 2GiB, but the maximum size message that can be transmitted in our serialization scheme is 4GiB.
*     This shouldn't be a problem for most applications, but you can discuss it in :issue:`83`.
*/
if (buffer.kMaxLength < 4294967299) {
    console.warn(`This implementation of javascript does not support the maximum protocol length. The largest message you may receive is 4294967299 bytes, but you can only allocate ${buffer.kMaxLength}, or ${(buffer.kMaxLength / 4294967299 * 100).toFixed(2)}% of that.`);
}

var base;

if( typeof exports !== 'undefined' ) {
    if( typeof module !== 'undefined' && module.exports ) {
        base = exports = module.exports;
    }
    base = exports;
}
else {
    root.base = {};
    base = root;
}

/**
* .. js:data:: js2p.base.version_info
*
*     A list containing the version numbers in the format ``[major, minor, patch]``.
*
*     The first two numbers refer specifically to the protocol version. The last number increments with each build.
*
* .. js:data:: js2p.base.node_policy_version
*
*     This is the last number in :js:data:`~js2p.base.version_info`
*
* .. js:data:: js2p.base.protocol_version
*
*     This is the first two numbers of :js:data:`~js2p.base.version_info` joined in the format ``'a.b'``
*
*     .. warning::
*
*         Nodes with different versions of this variable will actively reject connections with each other
*
* .. js:data:: js2p.base.version
*
*     This is :js:data:`~js2p.base.version_info` joined in the format ``'a.b.c'``
*/

base.version_info = [0, 7, 757];
base.node_policy_version = base.version_info[2].toString();
base.protocol_version = base.version_info.slice(0, 2).join(".");
base.version = base.version_info.join('.');

base.flags = {
    /**
    * .. js:data:: js2p.base.flags
    *
    *     A "namespace" which defines protocol reserved flags
    */
    reserved: [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
               0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F,
               0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17,
               0x18, 0x19, 0x1A, 0x1B, 0x1C, 0x1D, 0x1E, 0x1F,
               0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27,
               0x28, 0x29, 0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F],

    //main flags
    broadcast:   0x00,
    renegotiate: 0x01,
    whisper:     0x02,
    ping:        0x03,
    pong:        0x04,

    //sub-flags
    //broadcast: 0x00,
    compression: 0x01,
    //whisper:   0x02,
    //ping:      0x03,
    //pong:      0x04,
    handshake:   0x05,
    notify:      0x06,
    peers:       0x07,
    request:     0x08,
    resend:      0x09,
    response:    0x0A,
    store:       0x0B,
    retrieve:    0x0C,
    retrieved:   0x0D,
    forward:     0x0E,
    new_paths:   0x0F,
    revoke_paths: 0x10,
    delta:       0x11,

    //implemented compression methods
    gzip:     0x11,
    zlib:     0x13,
    snappy:   0x20,

    //compression methods
    bz2:      0x10,
    lzma:     0x12,
    bwtc:     0x14,
    context1: 0x15,
    defsum:   0x16,
    dmc:      0x17,
    fenwick:  0x18,
    huffman:  0x19,
    lzjb:     0x1A,
    lzjbr:    0x1B,
    lzp3:     0x1C,
    mtf:      0x1D,
    ppmd:     0x1E,
    simple:   0x1F
};

base.compression = []; //base.flags.snappy, base.flags.zlib, base.flags.gzip];

try {
    base.snappy = require('snappy');
    base.compression.push(base.flags.snappy);
}
catch (e) {
    console.warn("Couldn't load snappy compression (Ignore if in browser)");
}

try {
    base.zlib = require('zlibjs');
    base.compression.push(base.flags.zlib);
    base.compression.push(base.flags.gzip);
}
catch (e) {
    console.warn("Couldn't load zlib/gzip compression");
}


base.compress = function compress(text, method) {
    /**
    * .. js:function:: js2p.base.compress(text, method)
    *
    *     This function is a shortcut for compressing data using a predefined method
    *
    *     :param text:      The string or Buffer-like object you wish to compress
    *     :param method:    A compression method as defined in :js:data:`~js2p.base.flags`
    *
    *     :returns: A variabley typed object containing a compressed version of text
    */
    if (method === base.flags.zlib) {
        return base.zlib.deflateSync(new Buffer(text));
    }
    else if (method === base.flags.gzip)    {
        return base.zlib.gzipSync(new Buffer(text));
    }
    else if (method === base.flags.snappy)  {
        return base.snappy.compressSync(new Buffer(text));
    }
    else {
        throw new Error("Unknown compression method");
    }
};


base.decompress = function decompress(text, method) {
    /**
    * .. js:function:: js2p.base.decompress(text, method)
    *
    *     This function is a shortcut for decompressing data using a predefined method
    *
    *     :param text:      The string or Buffer-like object you wish to decompress
    *     :param method:    A compression method as defined in :js:data:`~js2p.base.flags`
    *
    *     :returns: A variabley typed object containing a decompressed version of text
    */
    if (method === base.flags.zlib) {
        return base.zlib.inflateSync(new Buffer(text));
    }
    else if (method === base.flags.gzip) {
        return base.zlib.gunzipSync(new Buffer(text));
    }
    else if (method === base.flags.snappy) {
        return base.snappy.uncompressSync(new Buffer(text));
    }
    else {
        throw new Error("Unknown compression method");
    }
};


// User salt generation pulled from: http://stackoverflow.com/a/2117523
base.user_salt = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    var r = Math.random()*16|0;
    var v = c === 'x' ? r : (r&0x3|0x8);
    return v.toString(16);
});

base.intersect = function intersect()    {
    /**
    * .. js:function:: js2p.base.intersect(array1, array2, [array3, [...]])
    *
    *     This function returns the intersection of two or more arrays.
    *     That is, it returns an array of the elements present in all arrays,
    *     in the order that they were present in the first array.
    *
    *     :param arrayn: Any array-like object
    *
    *     :returns: An array
    */
    var last = arguments.length - 1;
    var seen={};
    var result=[];
    for (let i = 1; i <= last; i++)   {
        for (var j = 0; j < arguments[i].length; j++)  {
            if (seen[arguments[i][j]])  {
                seen[arguments[i][j]] += 1;
            }
            else if (i === 1)    {
                seen[arguments[i][j]] = 1;
            }
        }
    }
    for (let i = 0; i < arguments[0].length; i++) {
        if ( seen[arguments[0][i]] === last)
            result.push(arguments[0][i]);
        }
    return result;
}

base.unpack_value = function unpack_value(str)  {
    /**
    * .. js:function:: js2p.base.unpack_value(str)
    *
    *     This function unpacks a string into its corresponding big endian value
    *
    *     :param str: The string you want to unpack
    *
    *     :returns: A big-integer
    */
    str = new Buffer(str, 'ascii');
    var val = BigInt.zero;
    for (let i = 0; i < str.length; i++)    {
        val = val.shiftLeft(8);
        val = val.add(str[i]);
    }
    return val;
}

base.pack_value = function pack_value(len, i) {
    /**
    * .. js:function:: js2p.base.pack_value(len, i)
    *
    *     This function packs an integer i into a buffer of length len
    *
    *     :param len:   An integral value
    *     :param i:     An integeral value
    *
    *     :returns: A big endian buffer of length len
    */
    var arr = new Buffer(new Array(len));
    if (!BigInt.isInstance(i))  {
        i = BigInt(i);
    }
    for (let j = 0; j < len && i.compare(0); j++)    {
        arr[len - j - 1] = i.and(0xff).valueOf();
        i = i.shiftRight(8);
    }
    return arr;
}

base.base_58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';

base.to_base_58 = function to_base_58(i) {
    /**
    * .. js:function:: js2p.base.to_base_58(i)
    *
    *     Takes an integer and returns its corresponding base_58 string
    *
    *     :param i: An integral value
    *
    *     :returns: the corresponding base_58 string
    */
    var string = "";
    if (!BigInt.isInstance(i)) {
        i = new BigInt(i);
    }
    while (i.notEquals(0)) {
        string = base.base_58[i.mod(58)] + string;
        i = i.divide(58);
    }
    if (!string)    {
        string = "1";
    }
    return string;
};


base.from_base_58 = function from_base_58(string) {
    /**
    * .. js:function:: js2p.base.from_base_58(string)
    *
    *     Takes a base_58 string and returns its corresponding integer
    *
    *     :param string: A base_58 string or string-like object
    *
    *     :returns: A big-integer
    */
    try {
        string = string.toString()
    }
    finally {
        var decimal = new BigInt(0);
        //for char in string {
        for (let i = 0; i < string.length; i++) {
            decimal = decimal.times(58).plus(base.base_58.indexOf(string[i]));
        }
        return decimal;
    }
};


base.getUTC = function getUTC() {
    /**
    * .. js:function:: js2p.base.getUTC()
    *
    *     :returns: An integral value containing the unix timestamp in seconds UTC
    */
    return Math.floor(Date.now() / 1000);
};


base.SHA384 = function SHA384(text) {
    /**
    * .. js:function:: js2p.base.SHA384(text)
    *
    *     This function returns the hex digest of the SHA384 hash of the input text
    *
    *     :param string text: A string you wish to hash
    *
    *     :returns: the hex SHA384 hash
    */
    var hash = new SHA("SHA-384", "ARRAYBUFFER");
    hash.update(new Buffer(text));
    return hash.getHash("HEX");
};


base.SHA256 = function SHA256(text) {
    /**
    * .. js:function:: js2p.base.SHA256(text)
    *
    *     This function returns the hex digest of the SHA256 hash of the input text
    *
    *     :param string text: A string you wish to hash
    *
    *     :returns: the hex SHA256 hash
    */
    var hash = new SHA("SHA-256", "ARRAYBUFFER");
    hash.update(new Buffer(text));
    return hash.getHash("HEX");
};


base.Protocol = class Protocol {
    /**
    * .. js:class:: js2p.base.Protocol(subnet, encryption)
    *
    *     This class is used as a subnet object. Its role is to reject undesired connections.
    *     If you connect to someone who has a different Protocol object than you, this descrepency is detected,
    *     and you are silently disconnected.
    *
    *     :param string subnet:     The subnet ID you wish to connect to. Ex: ``'mesh'``
    *     :param string encryption: The encryption method you wish to use. Ex: ``'Plaintext'``
    */
    constructor(subnet, encryption) {
        this.subnet = subnet;
        this.encryption = encryption;
    }

    get id() {
        /**
        *     .. js:attribute:: js2p.base.Protocol.id
        *
        *         The ID of your desired network
        */
        var protocol_hash = base.SHA256([this.subnet, this.encryption, base.protocol_version].join(''));
        return base.to_base_58(new BigInt(protocol_hash, 16));
    }
};

base.default_protocol = new base.Protocol('', 'Plaintext');

function getCertKeyPair()   {
    const pki = require('node-forge').pki;
    var keys = pki.rsa.generateKeyPair(1024);
    var cert = pki.createCertificate();
    cert.publicKey = keys.publicKey;
    cert.serialNumber = '01';
    cert.validity.notBefore = new Date();
    cert.validity.notAfter = new Date();
    cert.validity.notAfter.setFullYear(cert.validity.notBefore.getFullYear() + 1);
    var attrs = [{
        name: 'commonName',
        value: 'example.org'
    }, {
        name: 'countryName',
        value: 'US'
    }, {
        shortName: 'ST',
        value: 'Virginia'
    }, {
        name: 'localityName',
        value: 'Blacksburg'
    }, {
        name: 'organizationName',
        value: 'Test'
    }, {
        shortName: 'OU',
        value: 'Test'
    }];
    cert.setSubject(attrs);
    cert.setIssuer(attrs);
    cert.setExtensions([{
        name: 'basicConstraints',
        cA: false
    }]);
    cert.sign(keys.privateKey);
    return [pki.certificateToPem(cert), pki.privateKeyToPem(keys.privateKey)];
}

base.get_server = function get_server(aProtocol)    {
    if (aProtocol.encryption === 'Plaintext')   {
        return new require('net').Server();
    }
    else if (aProtocol.encryption === 'ws' || aProtocol.encryption === 'wss')    {
        if (require('net').connect === undefined)   {
            return null;
        }
        var options = {
            secure: aProtocol.encryption === 'wss'
        };
        return require('nodejs-websocket').createServer(options);
    }
    else if (aProtocol.encryption === 'SSL')    {
        let certKeyPair = getCertKeyPair();
        let options = {
            cert: certKeyPair[0],
            key: certKeyPair[1]
        };
        return require('tls').createServer(options);
    }
    else    {
        throw new Error("Unknown transport protocol");
    }
}

base.get_socket = function get_socket(addr, port, aProtocol)    {
    if (aProtocol.encryption === 'Plaintext')   {
        var conn = new require('net').Socket();
        conn.connect(port, addr);
        return conn;
    }
    else if (aProtocol.encryption === 'ws' || aProtocol.encryption === 'wss')    {
        var url = `${aProtocol.encryption}://${addr}:${port}`;
        if (require('net').connect === undefined)   {
            return new WebSocket(url);
        }
        else    {
            return new require('nodejs-websocket').connect(url);
        }
    }
    else if (aProtocol.encryption === 'SSL')    {
        let options = {
            rejectUnauthorized: false
        };
        return require('tls').connect(port, addr, options);
    }
    else    {
        throw new Error("Unknown transport protocol");
    }
}

base.InternalMessage = class InternalMessage {
    /**
    * .. js:class:: js2p.base.InternalMessage(msg_type, sender, payload, compression, timestamp)
    *
    *     This is the message serialization/deserialization class.
    *
    *     :param msg_type:          This is the main flag checked by nodes, used for routing information
    *     :param sender:            The ID of the person sending the message
    *     :param payload:           A list of "packets" that you want your peers to receive
    *     :param compression:       A list of compression methods that the receiver supports
    *     :param number timestamp:  The time at which this message will be sent in seconds UTC
    */
    constructor(msg_type, sender, payload, compression, timestamp) {
        this.__msg_type = msg_type;
        this.__sender = sender;
        this.__payload = payload || [];
        this.__time = timestamp || base.getUTC();
        this.__compression = compression || [];
        this.compression_fail = false
        this.__str = null;
        this.__id = null;
        this.__full_str = null;
    }

    __clear_cache() {
        this.__str = null;
        this.__id = null;
        this.__full_str = null;
    }

    get msg_type()  {
        return this.__msg_type;
    }

    set msg_type(x) {
        this.__clear_cache();
        this.__msg_type = x;
    }

    get sender()    {
        return this.__sender;
    }

    set sender(x)   {
        this.__clear_cache();
        this.__sender = x;
    }

    get payload()   {
        return [...this.__payload];
    }

    set payload(x)  {
        this.__clear_cache();
        this.__payload = Array.from(x);
    }

    get time()  {
        return this.__time;
    }

    set time(x) {
        this.__clear_cache();
        this.__time = x;
    }

    get compression()   {
        return [...this.__compression];
    }

    set compression(x)  {
        this.__full_str = null;
        this.__compression = Array.from(x);
    }

    static feed_string(string, sizeless, compressions) {
        /**
        *     .. js:function:: js2p.base.InternalMessage.feed_string(string, sizeless, compressions)
        *
        *         This method deserializes a message
        *
        *         :param string:        The message you would like to deserialize
        *         :param sizeless:      A bool-like object describing whether the size header is present
        *         :param compressions:  A list of possible compression methods this message may be under
        *
        *         :returns: A :js:class:`~js2p.base.InternalMessage` object containing the deserialized message
        */
        string = base.InternalMessage.sanitize_string(string, sizeless);
        var compression_return = base.InternalMessage.decompress_string(string, compressions);
        var compression_fail = compression_return[1];
        string = compression_return[0];
        var id = string.slice(0, 32);
        let serialized = string.slice(32);
        let hash = Buffer.from(base.SHA256(serialized), "hex");
        if (Buffer.compare(id, hash)) {
            throw new Error(`ID check failed. ${util.inspect(hash)} !== ${util.inspect(id)}`);
        }
        var packets = msgpack.decode(serialized);
        var msg = new base.InternalMessage(packets[0], packets[1], packets.slice(3), compressions);
        msg.time = packets[2];
        msg.compression_fail = compression_fail;
        msg.__id = id;
        msg.__str = serialized;
        return msg;
    }

    static sanitize_string(string, sizeless) {
        try {
            string = new Buffer(string)
        }
        finally {
            if (!sizeless) {
                if (base.unpack_value(string.slice(0,4)) + 4 !== string.length) {
                    //console.log(`slice given: ${string.slice(0, 4).inspect()}.  Value expected: ${string.length - 4}.  Value derived: ${base.unpack_value(string.slice(0, 4))}`)
                    throw "The following expression must be true: unpack_value(string.slice(0,4)) === string.length - 4"
                }
                string = string.slice(4)
            }
            return string
        }
    }

    static decompress_string(string, compressions) {
        var compression_fail = false
        compressions = base.intersect(compressions || [], base.compression);
        for (var i = 0; i < compressions.length; i++) {
            //console.log(`Checking ${compressions[i]} compression`)
            if (base.compression.indexOf(compressions[i]) > -1) {  // module scope compression
                //console.log(`Trying ${compressions[i]} compression`)
                try {
                    string = base.decompress(string, compressions[i])
                    compression_fail = false
                    //console.log(`Compression ${compressions[i]} succeeded`)
                    break
                }
                catch(err) {
                    compression_fail = true
                    //console.log(`compresion ${compressions[i]} failed: ${err}`)
                    continue
                }
            }
        }
        return [string, compression_fail]
    }

    get compression_used() {
        /**
        *     .. js:attribute:: js2p.base.InternalMessage.compression_used
        *
        *         Returns the compression method used in this message, as defined in :js:data:`~js2p.base.flags`, or ``undefined`` if none
        */
        return base.intersect(base.compression, this.compression)[0];
    }

    get time_58() {
        /**
        *     .. js:attribute:: js2p.base.InternalMessage.time
        *
        *         Returns the timestamp of this message
        *
        *
        *     .. js:attribute:: js2p.base.InternalMessage.time_58
        *
        *         Returns the timestamp encoded in base_58
        */
        return base.to_base_58(this.time);
    }

    get id() {
        /**
        *     .. js:attribute:: js2p.base.InternalMessage.id
        *
        *         Returns the ID/checksum associated with this message
        */
        if (this.__id === null) {
            try     {
                let payload_hash = base.SHA256(this.__non_len_string);
                this.__id = Buffer.from(payload_hash, "hex");
            }
            catch (err) {
                console.log(err);
                console.log(this.payload);
            }
        }
        return this.__id;
    }

    get packets() {
        /**
        *     .. js:attribute:: js2p.base.InternalMessage.payload
        *
        *         Returns the payload "packets" associated with this message
        *
        *
        *     .. js:attribute:: js2p.base.InternalMessage.packets
        *
        *         Returns the total "packets" associated with this message
        */
        return [this.msg_type, this.sender, this.time, ...this.payload];
    }

    get __non_len_string() {
        if (this.__str === null)  {
            this.__str = msgpack.encode(this.packets);
        }
        return this.__str;
    }

    get string() {
        /**
        *     .. js:attribute:: js2p.base.InternalMessage.string
        *
        *         Returns a Buffer containing the serialized version of this message
        */
        if (this.__full_str === null)   {
            var string = this.__non_len_string;
            var id = new Buffer(this.id);
            var total = Buffer.concat([id, string]);
            if (this.compression_used) {
                total = base.compress(total, this.compression_used);
            }
            this.__full_str = Buffer.concat([base.pack_value(4, total.length), total]);
        }
        return this.__full_str;
    }

    get length() {
        /**
        *     .. js:attribute:: js2p.base.InternalMessage.length
        *
        *         Returns the length of this message when serialized
        */
        return this.__non_len_string.length
    }

    len() {
        return pack_vlaue(4, this.length)
    }
};

base.Message = class Message {
    /**
    * .. js:class:: js2p.base.Message(msg, server)
    *
    *     This is the Message class we present to the user.
    *
    *     :param js2p.base.InternalMessage msg: This is the serialization object you received
    *     :param js2p.base.BaseSocket sender:      This is the "socket" object that received it
    */
    constructor(msg, server) {
        this.msg = msg
        this.server = server
    }

    /* istanbul ignore next */
    inspect()   {
        var packets = this.packets;
        var type = packets[0];
        var payload = packets.slice(1);
        var text = "Message {\n";
        text += ` type: ${util.inspect(type)}\n`;
        text += ` packets: ${util.inspect(payload)}\n`;
        text += ` sender: ${util.inspect(this.sender.toString())} }`;
        return text;
    }

    get time() {
        /**
        *     .. js:attribute:: js2p.base.Message.time
        *
        *         Returns the time (in seconds UTC) this Message was sent at
        */
        return this.msg.time
    }

    get time_58() {
        /**
        *     .. js:attribute:: js2p.base.Message.time_58
        *
        *         Returns the time (in seconds UTC) this Message was sent at, encoded in base_58
        */
        return this.msg.time_58
    }

    get sender() {
        /**
        *     .. js:attribute:: js2p.base.Message.sender
        *
        *         Returns the ID of this Message's sender
        */
        return this.msg.sender
    }

    get id() {
        /**
        *     .. js:attribute:: js2p.base.Message.id
        *
        *         Returns the ID/checksum associated with this Message
        */
        return this.msg.id
    }

    get packets() {
        /**
        *     .. js:attribute:: js2p.base.Message.packets
        *
        *         Returns the packets the sender wished you to have, sans metadata
        */
        return this.msg.payload
    }

    get length() {
        /**
        *     .. js:attribute:: js2p.base.Message.length
        *
        *         Returns the serialized length of this Message
        */
        return this.msg.length
    }

    get protocol()  {
        /**
        *     .. js:attribute:: js2p.base.Message.protocol
        *
        *         Returns the :js:class:`~js2p.base.Protocol` associated with this Message
        */
        return this.server.protocol
    }

    reply(packs) {
        /**
        *     .. js:function:: js2p.base.Message.reply(packs)
        *
        *         Replies privately to this Message.
        *
        *         .. warning::
        *
        *             Using this method has potential effects on the network composition.
        *             If you are not connected to the sender, we cannot garuntee
        *             the message will get through. If successful, you will experience
        *             higher network load on average.
        *
        *         :param packs: A list of packets you want the other user to receive
        */
        if (this.server.routing_table.get(this.sender)) {
            this.server.routing_table.get(this.sender).send(base.flags.whisper, [base.flags.whisper, ...packs]);
        }
        else    {
            var request_hash = base.SHA384(this.sender + base.to_base_58(base.getUTC()));
            var request_id = base.to_base_58(new BigInt(request_hash, 16));
            this.server.requests[request_id] = [packs, base.flags.whisper, base.flags.whisper];
            this.server.send([request_id, this.sender], base.flags.broadcast, base.flags.request);
            console.log("You aren't connected to the original sender. This reply is not guarunteed, but we're trying to make a connection and put the message through.");
        }
    }
};

base.BaseConnection = class BaseConnection    {
    /**
    * .. js:class:: js2p.base.BaseConnection(sock, server, outgoing)
    *
    *     This is the template class for connection abstracters.
    *
    *     :param sock:                          This is the raw socket object
    *     :param js2p.base.BaseSocket server:  This is a link to the :js:class:`~js2p.base.BaseSocket` parent
    *     :param outgoing:                      This bool describes whether ``server`` initiated the connection
    */
    constructor(sock, server, outgoing)   {
        this.sock = sock;
        this.server = server;
        this.outgoing = outgoing || false;
        this.buffer = new Buffer(0);
        this.id = null;
        this.time = base.getUTC();
        this.addr = null;
        this.compression = [];
        this.last_sent = [];
        this.expected = 4;
        this.active = false;
        var self = this;

        /* istanbul ignore else */
        if (this.sock.on)   {
            this.sock.on('data', (data)=>{
                self.collect_incoming_data(self, data);
            });
            this.sock.on('text', (data)=>{
                self.collect_incoming_data(self, new Buffer(data));
            });
            this.sock.on('binary', (inStream)=>{
                inStream.on("readable", ()=>{
                    var newData = inStream.read();
                    if (newData)    {
                        self.collect_incoming_data(self, newData);
                    }
                });
            });
            this.sock.on('end', ()=>{
                self.onEnd();
            });
            this.sock.on('error', (err)=>{
                self.onError(err);
            });
            this.sock.on('close', ()=>{
                self.onClose();
            });
        }
        else    {
            // This part handles browser receives
            this.sock.onmessage = (evt)=>{
                var fileReader = new FileReader();
                fileReader.onload = function() {
                    var data = fileReader.result;
                    self.collect_incoming_data(self, Buffer.from(data));
                };
                fileReader.readAsArrayBuffer(evt.data);
            };
            this.sock.onend = (evt)=>{
                self.onEnd();
            };
            this.sock.onerror = (evt)=>{
                self.onError(evt);
            };
            this.sock.onclose = (evt)=>{
                self.onClose();
            };
        }
    }

    onEnd() {
        /**
        *     .. js:function:: js2p.base.BaseConnection.onEnd()
        *
        *         This function is run when a connection is ended
        */
        console.log(`Connection to ${this.id || this} ended. This is the template function`);
    }

    onError(err)    {
        /**
        *     .. js:function:: js2p.base.BaseConnection.onError()
        *
        *         This function is run when a connection experiences an error
        */
        if (this.sock.end)  {
            this.sock.end();
            this.sock.destroy(); //These implicitly remove from routing table
        }
        else    {
            this.sock.close();
        }
    }

    onClose()   {
        /**
        *     .. js:function:: js2p.base.BaseConnection.onClose()
        *
        *         This function is run when a connection is closed
        */
        console.log(`Connection to ${this.id || this} closed. This is the template function`);
    }

    send_InternalMessage(msg)   {
        /**
        *     .. js:function:: js2p.base.BaseConnection.send_InternalMessage(msg)
        *
        *         Sends a message through its connection.
        *
        *         :param js2p.base.InternalMessage msg:      A :js:class:`~js2p.base.InternalMessage` object
        *
        *         :returns: the :js:class:`~js2p.base.InternalMessage` object you just sent, or ``undefined`` if the sending was unsuccessful
        */
        msg.compression = this.compression;
        // console.log(msg.payload);
        if (msg.msg_type === base.flags.whisper || msg.msg_type === base.flags.broadcast) {
            this.last_sent = [msg.msg_type, ...msg.packets];
        }
        // this.__print__(`Sending ${[msg.len()].concat(msg.packets)} to ${this}`, 4);
        if (msg.compression_used)   {
            //console.log(`Compressing with ${JSON.stringify(msg.compression_used)}`);
            // self.__print__(`Compressing with ${msg.compression_used}`, level=4)
        }
        // try {
            //console.log(`Sending message ${JSON.stringify(msg.string.toString())} to ${this.id}`);
            if (this.protocol.encryption === 'ws' || this.protocol.encryption === 'wss')    {
                this.sock.send(new Buffer(msg.string, 'ascii'));
            }
            else    {
                this.sock.write(msg.string, 'ascii');
            }
            return msg;
        // }
        // catch(e)   {
        //     self.server.daemon.exceptions.append((e, traceback.format_exc()))
        //     self.server.disconnect(self)
        // }
    }

    send(msg_type, packs, id, time)  {
        /**
        *     .. js:function:: js2p.base.BaseConnection.send(msg_type, packs, id, time)
        *
        *         Sends a message through its connection.
        *
        *         :param msg_type:      Message type, corresponds to the header in a :js:class:`~js2p.base.InternalMessage` object
        *         :param packs:         A list of Buffer-like objects, which correspond to the packets to send to you
        *         :param id:            The ID this message should appear to be sent from (default: your ID)
        *         :param number time:   The time this message should appear to be sent from (default: now in UTC)
        *
        *         :returns: the :js:class:`~js2p.base.InternalMessage` object you just sent, or ``undefined`` if the sending was unsuccessful
        */

        //This section handles waterfall-specific flags
        // console.log(packs);
        id = id || this.server.id;  //Latter is returned if key not found
        time = time || base.getUTC();
        //Begin real method
        var msg = new base.InternalMessage(msg_type, id, packs, this.compression, time);
        return this.send_InternalMessage(msg);
    }

    get protocol()  {
        return this.server.protocol;
    }

    collect_incoming_data(self, data) {
        /**
        *     .. js:function:: js2p.base.BaseConnection.collect_incoming_data(self, data)
        *
        *         Collects and processes data which just came in on the socket
        *
        *         :param self:          A reference to this connection. Will be refactored out.
        *         :param Buffer data:   The data which was just received
        */
        self.buffer = Buffer.concat([self.buffer, data]);
        //console.log(self.buffer);
        self.time = base.getUTC();
        while (self.buffer.length >= self.expected) {
            if (!self.active)   {
                // this.__print__(this.buffer, this.expected, this.find_terminator(), level=4)
                self.expected = base.unpack_value(self.buffer.slice(0, 4)).add(4);
                self.active = true;
                // this.found_terminator();
            }
            if (self.active && self.buffer.length >= self.expected) {  //gets checked again because the answer may have changed
                self.found_terminator();
            }
        }
        return true;
    }

    found_terminator()  {
        /**
        *     .. js:function:: js2p.base.BaseConnection.found_terminator()
        *
        *         This method is called when the expected amount of data is received
        *
        *         :returns: The deserialized message received
        */
        //console.log("I got called");
        let msg_data = this.buffer.slice(0, this.expected);
        this.buffer = this.buffer.slice(this.expected);
        this.expected = 4;
        this.active = false;
        return base.InternalMessage.feed_string(msg_data, false, this.compression);
    }

    handle_renegotiate(packets) {
        /**
        *     .. js:function:: js2p.base.BaseConnection.handle_renegotiate(packets)
        *
        *         This function handles connection renegotiations. This is used when compression methods
        *         fail, or when a node needs a message resent.
        *
        *         :param packs: The array of packets which were received to initiate the renegotiation
        *
        *         :returns: ``true`` if action was taken, ``undefined`` if not
        */
        if (packets[0] === base.flags.renegotiate)  {
            if (packets[3] === base.flags.compression)  {
                var respond = (base.intersect(this.compression, packets[4]).length !== this.compression.length);
                this.compression = packets[4];
                // self.__print__("Compression methods changed to: %s" % repr(self.compression), level=2)
                if (respond)    {
                    var new_methods = base.intersect(base.compression, this.compression);
                    self.send(base.flags.renegotiate, base.flags.compression, new_methods)
                }
                return true;
            }
            else if (packets[3] === base.flags.resend)  {
                var type = self.last_sent[0];
                var packs = self.last_sent.slice(1);
                self.send(type, packs);
                return true;
            }
        }
    }

    __print__() {

    }
};

base.BaseSocket = class BaseSocket extends EventEmitter   {
    /**
    * .. js:class:: js2p.base.BaseSocket(addr, port [, protocol [, out_addr [, debug_level]]])
    *
    *     This is the template class for socket abstracters. This class extends :js:class:`EventEmitter`.
    *
    *     :param string addr:                   The address you'd like to bind to
    *     :param number port:                   The port you'd like to bind to
    *     :param js2p.base.Protocol protocol:   The subnet you're looking to connect to
    *     :param array out_addr:                Your outward-facing address
    *     :param number debug_level:            The verbosity of debug prints
    *
    *     .. js:attribute:: js2p.base.BaseSocket.routing_table
    *
    *         A :js:class:`Map` which contains :js:class:`~js2p.base.BaseConnection` s keyed by their IDs
    *
    *     .. js:attribute:: js2p.base.BaseSocket.awaiting_ids
    *
    *         An array which contains :js:class:`~js2p.base.BaseConnection` s that are awaiting handshake information
    */
    constructor(addr, port, protocol, out_addr, debug_level)   {
        super();
        var self = this;
        if (addr === '0.0.0.0') {
            let ip = require('ip');
            this.addr = [ip.address(), port];
        }
        else    {
            this.addr = [addr, port];
        }
        this.incoming = base.get_server(protocol);
        if (this.incoming)  {
            this.incoming.listen(port, addr);
        }
        this.protocol = protocol || base.default_protocol;
        this.out_addr = out_addr || this.addr;
        this.debug_level = debug_level || 0;

        this.awaiting_ids = [];
        this.routing_table = new Map();
        this.id = base.to_base_58(BigInt(base.SHA384(`(${addr}, ${port})${this.protocol.id}${base.user_salt}`), 16));
        this.__handlers = [];
        this.exceptions = [];
    }

    get status()    {
        /**
        *     .. js:attribute:: js2p.base.BaseSocket.status
        *
        *         This attribute describes whether the socket is operating as expected.
        *
        *         It will either return a string ``"Nominal"`` or a list of Error/Traceback pairs
        */
        if (this.exceptions.length) {
            return this.exceptions;
        }
        return "Nominal";
    }

    get outgoing()  {
        /**
        *     .. js:attribute:: js2p.mesh.MeshSocket.outgoing
        *
        *         This is an array of all outgoing connections. The length of this array is used to determine
        *         whether the "socket" should automatically initiate connections
        */
        var outs = [];
        for (let key of this.routing_table.keys()) {
            let node = this.routing_table.get(key);
            if (node.outgoing)  {
                outs.push(node);
            }
        }
        return outs;
    }

    // get *outgoing()  {
    //     for (let node of Object.values(this.routing_table)) {
    //         if (node.outgoing)   {
    //             yield node;
    //         }
    //     }
    // }

    // get *incoming() {
    //     for (let node of Object.values(this.routing_table)) {
    //         if (!node.outgoing)  {
    //             yield node;
    //         }
    //     }
    // }

    register_handler(callback)  {
        /**
        *     .. js:function:: js2p.base.BaseSocket.register_handler(callback)
        *
        *         This registers a message callback. Each is run through until one returns ``true``,
        *         rather like :js:func:`Array.some()`. The callback is expected to be of the form:
        *
        *         .. code-block:: javascript
        *
        *             function callback(msg, conn)  {
        *                 var packets = msg.packets;
        *                 if (packets[0] === some_expected_value)   {
        *                     some_action(msg, conn);
        *                     return true;
        *                 }
        *             }
        *
        *         :param function callback: A function formatted like the above
        */
        this.__handlers.push(callback);
    }

    handle_msg(msg, conn) {
        for (let handler of this.__handlers)    {
            // self.__print__("Checking handler: %s" % handler.__name__, level=4)
            // console.log(`Entering handler ${handler.name}`);
            if (handler(msg, conn)) {
                // self.__print__("Breaking from handler: %s" % handler.__name__, level=4)
                // console.log(`breaking from ${handler.name}`);
                return true
            }
        }
        return false;
    }
};
