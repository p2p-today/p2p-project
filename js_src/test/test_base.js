"use strict";

const assert = require('assert');
const base = require('../base.js');
const BigInt = require('big-integer');
const util = require('util');

function get_random_buffer(len) {
    var pre_buffer = [];
    for (var j = 0; j < len; j++)   {
        pre_buffer.push(Math.floor(Math.random() * 256));
    }
    return new Buffer(pre_buffer);
}

function get_random_array(len)  {
    var ret = [];
    for (var i = 0; i < len; i++)   {
        ret.push(get_random_buffer(Math.floor(Math.random() * 20)));
    }
    return ret;
}

function test_InternalMessage(payload, instance)  {
    if (!instance)  {
        var msg = new base.InternalMessage(base.flags.broadcast, new Buffer('\u00ff', 'ascii'), payload);
    }
    else    {
        var msg = instance;
    }
    var expected_packets = [base.flags.broadcast, new Buffer('\u00ff', 'ascii'), msg.time, ...payload];
    var packets = msg.packets;
    for (var j = 0; j < packets.length; j++)    {
        assert.equal(packets[j].toString(), expected_packets[j].toString(), `At position ${j}: ${packets[j]} != ${expected_packets[j]}`);
    }
    var p_hash = base.SHA256(msg.__non_len_string);
    assert.equal(util.inspect(msg.id), util.inspect(Buffer.from(p_hash, "hex")));
}

describe('base', function() {

    describe('compress/decompress', function() {

        it('should always be reversable', function() {
            this.timeout(1500);
            for (var i = 0; i < 500; i++)  {
                // Step one: generate a random buffer up to size 40
                var len = Math.floor(Math.random() * 40);
                var test_string = get_random_buffer(len);
                // Then: For each flag in compression, assert that the compressed then decompressed version equals the original
                for (let flag of base.compression)   {
                    try {
                        assert(test_string.equals( base.decompress( base.compress(test_string, flag), flag ) ));
                    }
                    catch (e)   {
                        throw new Error(`${util.inspect(test_string)}, ${util.inspect(flag)}: ${util.inspect(e)}`);
                    }
                }
            }
        });

        it('should raise an exception when given an unkown method', function()  {
            function compress_err()    {
                base.compress('', get_random_buffer(4).toString());
            }
            function decompress_err()    {
                base.decompress('', get_random_buffer(4).toString());
            }
            for (var i = 0; i < 100; i++)   {
                assert.throws(compress_err, Error);
                assert.throws(decompress_err, Error);
            }
        });
    });

    describe('to_base_58/from_base_58', function()  {
        it('should return "1" if fed 0', function() {
            this.timeout(25);
            assert.equal("1", base.to_base_58(0));
        });

        it('should always be reversable', function()    {
            this.timeout(125);
            for (var i = 0; i < 500; i++)  {
                var test = Math.floor(Math.random() * 1000000000);
                var shouldEqual = base.from_base_58(base.to_base_58(test));
                assert(shouldEqual.equals(test), `${test} != ${shouldEqual}`);
            }
        });
    });

    describe('Protocol', function() {
        it('should have information assigned to the correct getters', function()    {
            for (var i = 0; i < 250; i++)   {
                var sub = get_random_buffer(4);
                var enc = get_random_buffer(4);
                // Make sure it's normal ascii. utf-8 intentionally not supported here
                for (var j = 0; j < 4; j++) {
                    sub[j] = sub[j] % 128;
                    enc[j] = enc[j] % 128;
                }
                var test = new base.Protocol(sub, enc);
                assert.equal(test.subnet, sub);
                assert.equal(test.encryption, enc);
                var p_hash_info = [sub, enc, base.protocol_version].join('');
                var p_hash = base.SHA256(p_hash_info);
                assert.equal(test.id, base.to_base_58(new BigInt(p_hash, 16)));
            }
        });
    });

    describe('InternalMessage', function()  {
        it('should serialize and deserialize', function()   {
            let iters = 250;
            this.timeout(0);
            this.slow(1000 * iters);
            for (var i = 0; i < iters; i++)   {
                var payload = get_random_array(Math.floor(Math.random() * 16));
                var msg = new base.InternalMessage(base.flags.broadcast, new Buffer('\u00ff', 'ascii'), payload, []);
                var deserialized = base.InternalMessage.feed_string(msg.string, false, []);
                test_InternalMessage(payload, deserialized);
            }
        });

        it('should serialize and deserialize (with compression)', function()    {
            let iters = 250;
            this.timeout(0);
            this.slow(1500 * iters * base.compression.length);
            for (var i = 0; i < iters; i++)   {
                for (var j = 0; j < base.compression.length; j++)  {
                    var payload = get_random_array(Math.floor(Math.random() * 16));
                    var msg = new base.InternalMessage(base.flags.broadcast, new Buffer('\u00ff', 'ascii'), payload, [base.compression[j]]);
                    var deserialized = base.InternalMessage.feed_string(msg.string, false, [base.compression[j]]);
                    test_InternalMessage(payload, deserialized);
                }
            }
        });

        it('should have information assigned to the correct getters', function()    {
            for (var i = 0; i < 250; i++)   {
                var payload = get_random_array(Math.floor(Math.random() * 16));
                test_InternalMessage(payload);
            }
        });
    });

    describe('message', function()  {
        it('should have information assigned to the correct getters', function()    {
            for (var i = 0; i < 150; i++)   {
                var sen = get_random_buffer(4);
                for (var j = 0; j < 4; j++) {  // utf-8 is supported here, but it doesn't make much sense to have that as a sender id
                    sen[j] = sen[j] % 128;
                }
                var pac = get_random_array(36);
                var base_msg = new base.InternalMessage(base.flags.broadcast, sen, pac);
                var test = new base.message(base_msg, null);
                assert.equal(util.inspect(test.packets), util.inspect(pac));
                assert.equal(test.msg, base_msg);
                assert.equal(test.sender.toString(), sen);
                assert.equal(util.inspect(test.id), util.inspect(base_msg.id));
                assert.equal(test.time, base_msg.time);
                assert.equal(test.time_58, base_msg.time_58);
                assert(base.from_base_58(test.time_58).equals(test.time));
            }
        })
    });
});
