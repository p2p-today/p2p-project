/**
* Type Module
* ===========
*
* This module contains functions and classes related to the serialization scheme
*
* Currently this is for experimental primitive serialization support.
*/

"use strict";

const BigInt = require('big-integer');
const base = require('./base.js');

var types;

if( typeof exports !== 'undefined' ) {
    if( typeof module !== 'undefined' && module.exports ) {
        types = exports = module.exports;
    }
    types = exports;
}
else {
    root.types = {};
    types = root;
}

class Js2pType {
    constructor(flag, serializer, deserializer) {
        this.flag = flag;
        this.serialize = serializer;
        this.deserialize = deserializer;
    }
};

function big_int_serialize(x)   {
    x = new BigInt(x);
    let size = Math.ceil(x.toString(16).length / 2)
    let ret = base.pack_value(size, x);
    if (x.isNegative()) {
        return Buffer.concat([new Buffer('-'), ret]);
    }
    else    {
        return Buffer.concat([new Buffer('+'), ret]);
    }
}

function big_int_deserialize(buff)  {
    let val = base.unpack_value(buff.slice(1));
    if (buff.slice(0, 1).toString() === '-')    {
        return val.negate();
    }
    else    {
        return val;
    }
}

function pack_signed_value(len, x)  {
    x = new BigInt(x);
    if (x.isPositive()) {
        return base.pack_value(len, x);
    }
    else    {
        return base.pack_value(len, BigInt[1].shiftLeft(8*len).plus(x));
    }
}

function unpack_signed_value(len, x)  {
    let val = base.unpack_value(x);
    let middle = BigInt[1].shiftLeft(8*len-1);
    if (!middle.gt(val))    {
        return BigInt[1].shiftLeft(8*len).minus(val).negate();
    }
    else    {
        return val;
    }
}

types.types = {
    buffer : new Js2pType('\x30', Buffer.from, (buff)=>{return buff}),
    string : new Js2pType('\x31', Buffer.from, (buff)=>{return buff.toString()}),
    bigint : new Js2pType('\x32', big_int_serialize, big_int_deserialize),
    uchar  : new Js2pType('\x33',
                          (x)=>{return base.pack_value(1, x)},
                          base.unpack_value),
    char   : new Js2pType('\x34',
                          (x)=>{return pack_signed_value(1, x)},
                          (x)=>{return unpack_signed_value(1, x)}),
    uint16 : new Js2pType('\x35',
                          (x)=>{return base.pack_value(2, x)},
                          base.unpack_value),
    int16  : new Js2pType('\x36',
                          (x)=>{return pack_signed_value(2, x)},
                          (x)=>{return unpack_signed_value(2, x)}),
    uint32 : new Js2pType('\x37',
                          (x)=>{return base.pack_value(4, x)},
                          base.unpack_value),
    int32  : new Js2pType('\x38',
                          (x)=>{return pack_signed_value(4, x)},
                          (x)=>{return unpack_signed_value(4, x)}),
    uint64 : new Js2pType('\x39',
                          (x)=>{return base.pack_value(8, x)},
                          base.unpack_value),
    int64  : new Js2pType('\x3A',
                          (x)=>{return pack_signed_value(8, x)},
                          (x)=>{return unpack_signed_value(8, x)})
    // array  : new Js2pType('\x3B',
    //                       partial(SerializableTuple.serialize_iterable, sizeless:True),
    //                       partial(SerializableTuple.deserialize, sizeless:True))

    // types = [buffer, string, bigint, char,
    //             uchar, uint16, int16, uint32,
    //             int32, uint64, int64, array],
};
