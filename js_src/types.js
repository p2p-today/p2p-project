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
    if (x.isNegative()) {
        return Buffer.concat([new Buffer('-'), base.pack_value(size, x.negate())]);
    }
    else    {
        return Buffer.concat([new Buffer('+'), base.pack_value(size, x)]);
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

function determine_int_subtype(i)   {
    if (i.lt(0))    {
        if (!i.lt(-(1<<7)))  {
            return types.types.char;
        }
        else if (!i.lt(-(1<<15))) {
            return types.types.int16;
        }
        else if (!i.lt(BigInt[1].shiftLeft(31).negate()))   {
            return types.types.int32;
        }
        else if (!i.lt(BigInt[1].shiftLeft(63).negate()))   {
            return types.types.int64;
        }
    }
    else    {
        if (i.lt(1<<8))  {
            return types.types.uchar;
        }
        else if (i.lt(1<<16))    {
            return types.types.uint16;
        }
        else if (i.lt(BigInt[1].shiftLeft(32)))    {
            return types.types.uint32;
        }
        else if (i.lt(BigInt[1].shiftLeft(64)))    {
            return types.types.uint64;
        }
    }
    return types.types.bigint;
}

function determine_type(x)  {
    if (Number(parseFloat(x))===x)  {
        return determine_int_subtype(new BigInt(x));
    }
    else if (typeof x === 'string' || x instanceof String)  {
        return types.types.string;
    }
    else if (x instanceof Array)    {
        return types.types.array;
    }
    else    {
        return types.types.buffer;
    }
}

types.SerializableArray = class SerializableArray   {
    constructor()   {
        let types = [];
        let length = 0;
        Array.from(arguments).map((x, idx)=>{
            types.push(determine_type(x));
            this[idx] = types[idx].serialize(x);
            length++;
        });
        this.types = types;
        this.length = length;
    }

    static from_iterable(items) {
        items = Array.from(items);
        let types = items.map((x)=>{
            return determine_type(x);
        })
        return SerializableArray.from_array_pair(items, types);
    }

    static from_array_pair(items, types)    {
        let ret = new SerializableArray();
        for (let idx in items)  {
            ret[idx] = types[idx].serialize(items[idx]);
        }
        ret.types = types;
        ret.length = items.length;
        return ret;
    }

    static from_raw_array_pair(items, types)    {
        let ret = new SerializableArray();
        for (let idx in items)  {
            ret[idx] = items[idx];
        }
        ret.types = types;
        ret.length = items.length;
        return ret;
    }

    *[Symbol.iterator]() {
        for (let i = 0; i < this.length; i++)   {
            yield this[i];
        }
    }

    get(idx)    {
        return this.types[idx].deserialize(this[idx]);
    }

    *values()   {
        for (let i in this) {
            if (i !== 'types' && i !== 'length')    {
                yield this.get(i);
            }
        }
    }

    map(func)   {
        return Array.from(this).map(func);
    }

    mapValues(func) {
        return Array.from(this.values()).map(func);
    }

    serialize(sizeless) {
        let packets = this.map((x, idx)=>{
            return Buffer.concat([base.pack_value(4, x.length),
                                  Buffer.from(this.types[idx].flag),
                                  x]);
        });
        let ret = Buffer.concat(packets);
        if (!sizeless)  {
            return Buffer.concat([base.pack_value(4, ret.length), ret]);
        }
        else    {
            return ret;
        }
    }

    static serialize_iterable(iterable, sizeless)   {
        if (iterable instanceof SerializableArray)  {
            return iterable.serialize(sizeless);
        }
        else    {
            return SerializableArray.from_iterable(iterable).serialize(sizeless);
        }
    }

    static deserialize(string, sizeless)    {
        try {
            string = new Buffer(string)
        }
        finally {
            if (!sizeless) {
                if (base.unpack_value(string.slice(0,4)) + 4 !== string.length) {
                    //console.log(`slice given: ${string.slice(0, 4).inspect()}.  Value expected: ${string.length - 4}.  Value derived: ${base.unpack_value(string.slice(0, 4))}`)
                    throw new Error("The following expression must be true: unpack_value(string.slice(0,4)) === string.length - 4");
                }
                string = string.slice(4)
            }
        }
        let processed = 0;
        let expected = string.length;
        let packets = [];
        let types_ = [];
        while (processed < expected) {
            let len = base.unpack_value(new Buffer(string.slice(processed, processed+4)));
            processed += 4;
            types_.push(types.types.from_flag(string.slice(processed, processed+1)));
            processed += 1;
            packets = packets.concat(new Buffer(string.slice(processed, processed+len)));
            processed += len;
        }
        if (processed > expected)   {
            throw `Could not parse correctly processed=${processed}, expected=${expected}, packets=${packets}`;
        }
        return types.SerializableArray.from_raw_array_pair(packets, types_);
    }
}

types.SerializableTuple = types.SerializableArray;

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
                          (x)=>{return unpack_signed_value(8, x)}),
    array  : new Js2pType('\x3B',
                          (x)=>{return types.SerializableArray.serialize_iterable(x, true)},
                          (x)=>{return types.SerializableArray.deserialize(x, true)}),
    from_flag : (flag)=>{
        for (let i of ['string', 'bigint', 'uchar', 'uint16', 'uint32',
                       'uint64', 'char', 'int16', 'int32', 'int64', 'array'])   {
            if (flag.toString() === types.types[i].flag)    {
                return types.types[i];
            }
        }
        return types.types.buffer;
    }
};
