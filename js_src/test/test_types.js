"use strict";

const assert = require('assert');
const types = require('../types.js');
const BigInt = require('big-integer');

function get_random_buffer(len) {
    var pre_buffer = [];
    for (var j = 0; j < len; j++)   {
        pre_buffer.push(Math.floor(Math.random() * 256));
    }
    return new Buffer(pre_buffer);
}

describe('types', function()    {

    describe('char', function() {

        it('should always be reversible', function()    {
            for (var i = 0; i < 500; i++)  {
                let val = Math.ceil(Math.random() * 0xff - 0x80);
                try {
                    assert(types.types.char.deserialize(types.types.char.serialize(val)).equals(val));
                }
                catch (e)   {
                    throw new Error(val, e);
                }
            }
        });
    });

    describe('uchar', function() {

        it('should always be reversible', function()    {
            for (var i = 0; i < 500; i++)  {
                let val = Math.ceil(Math.random() * 0xff);
                try {
                    assert(types.types.uchar.deserialize(types.types.uchar.serialize(val)).equals(val));
                }
                catch (e)   {
                    throw new Error(val, e);
                }
            }
        });
    });

    describe('int16', function() {

        it('should always be reversible', function()    {
            for (var i = 0; i < 500; i++)  {
                let val = Math.ceil(Math.random() * 0xffff - 0x8000);
                try {
                    assert(types.types.int16.deserialize(types.types.int16.serialize(val)).equals(val));
                }
                catch (e)   {
                    throw new Error(val, e);
                }
            }
        });
    });

    describe('uint16', function() {

        it('should always be reversible', function()    {
            for (var i = 0; i < 500; i++)  {
                let val = Math.ceil(Math.random() * 0xffff);
                try {
                    assert(types.types.uint16.deserialize(types.types.uint16.serialize(val)).equals(val));
                }
                catch (e)   {
                    throw new Error(val, e);
                }
            }
        });
    });

    describe('int32', function() {

        it('should always be reversible', function()    {
            for (var i = 0; i < 500; i++)  {
                let val = Math.ceil(Math.random() * 0xffffffff - 0x80000000);
                try {
                    assert(types.types.int32.deserialize(types.types.int32.serialize(val)).equals(val));
                }
                catch (e)   {
                    throw new Error(val, e);
                }
            }
        });
    });

    describe('uint32', function() {

        it('should always be reversible', function()    {
            for (var i = 0; i < 500; i++)  {
                let val = Math.ceil(Math.random() * 0xffffffff);
                try {
                    assert(types.types.uint32.deserialize(types.types.uint32.serialize(val)).equals(val));
                }catch (e)   {
                    throw new Error(val, e);
                }
            }
        });
    });

    describe('int64', function() {

        it('should always be reversible', function()    {
            for (var i = 0; i < 500; i++)  {
                let val = Math.ceil(Math.random() * 0xffffffffffffffff - 0x8000000000000000);
                try {
                    assert(types.types.int64.deserialize(types.types.int64.serialize(val)).equals(val));
                }
                catch (e)   {
                    throw new Error(val, e);
                }
            }
        });
    });

    describe('uint64', function() {

        it('should always be reversible', function()    {
            for (var i = 0; i < 500; i++)  {
                let val = Math.ceil(Math.random() * 0xffffffffffffffff);
                try {
                    assert(types.types.uint64.deserialize(types.types.uint64.serialize(val)).equals(val));
                }
                catch (e)   {
                    throw new Error(val, e);
                }
            }
        });
    });

    describe('bigint', function() {

        it('should always be reversible', function()    {
            for (var i = 0; i < 500; i++)  {
                let val = Math.ceil(Math.random() * (0xffffffffffffffff - 0x8000000000000000) * 0xffff);
                try {
                    assert(types.types.bigint.deserialize(types.types.bigint.serialize(val)).equals(val));
                }
                catch (e)   {
                    throw new Error(val, e);
                }
            }
        });
    });

    describe('string', function() {

        it('should always be reversible', function()    {
            for (var i = 0; i < 500; i++)  {
                let val = get_random_buffer(Math.ceil(Math.random() * 32)).toString();
                try {
                    assert(types.types.string.deserialize(types.types.string.serialize(val)) === val);
                }
                catch (e)   {
                    throw new Error(val, e);
                }
            }
        });
    });

    describe('buffer', function() {

        it('should always be reversible', function()    {
            for (var i = 0; i < 500; i++)  {
                let val = get_random_buffer(Math.ceil(Math.random() * 32));
                try {
                    assert(!types.types.buffer.deserialize(types.types.buffer.serialize(val)).compare(val));
                }
                catch (e)   {
                    throw new Error(val, e);
                }
            }
        });
    });
});
