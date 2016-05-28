var BigInt = require('./BigInteger/BigInteger.js')
var struct = require('./pack/jspack.js')
var SHA = require('./SHA/src/sha.js')

version = "0.1.C"

var to_base_58 = function(i) {
    //Takes an integer and returns its corresponding base_58 string
    string = ""
    if (!BigInt.isInstance(i)) {
        i = BigInt(i)
    }
    while (i.notEquals(0)) {
        string = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'[i.mod(58)] + string
        i = i.divide(58)
    }
    return string
}


var from_base_58 = function(string) {
    //Takes a base_58 string and returns its corresponding integer
    decimal = BigInt(0)
    //for char in string {
    for (i = 0; i < string.length; i++) {
        console.log(decimal)
        decimal = decimal.times(58).plus('123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'.indexOf(string[i]))
    }
    return decimal
}


var getUTC = function() {
    return Math.floor(Date.now() / 1000)
}


var SHA384 = function(text) {
    var hash = new SHA("SHA-384", "TEXT");
    hash.update(text);
    return hash.getHash("HEX");
}


var SHA256 = function(text) {
    var hash = new SHA("SHA-256", "TEXT");
    hash.update(text);
    return hash.getHash("HEX");
}

class protocol {
    constructor(sep, subnet, encryption) {
        this.sep = sep
        this.subnet = subnet
        this.encryption = encryption
    }

    id() {
        var protocol_hash = SHA256([this.sep, this.subnet, this.encryption, version].join(''))
        return to_base_58(BigInt(protocol_hash, 16))
    }
}

var unpack = function(fmt, str) {
    arr = [];
    for(var i=0; i<str.length; i++) {
        arr.push(str.charCodeAt(i))
    }
    return struct.Unpack(fmt, arr)
}

var pack = function(fmt, vals) {
    res = struct.Pack(fmt, vals)
    return String.fromCharCode.apply(null, res)
}

var construct_message = function(prot, comp_types, msg_type, id, packets, time) {
    var time = typeof time !== 'undefined' ?  time : to_base_58(getUTC());

    var msg_hash = SHA384(packets.join(prot.sep) + time)
    var msg_id = to_base_58(BigInt(msg_hash, 16))

    packets = [msg_type, id, msg_id, time].concat(packets)
    msg = packets.join(prot.sep)

    //compression_used = ""
    //for method in compression:
    //    if method in comp_types:
    //        compression_used = method
    //        msg = compress(msg, method)
    //        break

    size = pack("!L", msg.length)
    return size, msg
}