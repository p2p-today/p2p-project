"use strict";

const assert = require('assert');
const base = require('../base.js');
const BigInt = require('big-integer');

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

function test_pathfinding_message(payload, instance)  {
    if (!instance)  {
        var msg = new base.pathfinding_message(base.flags.broadcast, new Buffer('\u00ff', 'ascii'), payload);
    }
    else    {
        var msg = instance;
    }
    var expected_packets = [new Buffer(base.flags.broadcast), new Buffer('\u00ff', 'ascii'), msg.id, msg.time_58].concat(payload);
    var packets = msg.packets;
    for (var j = 0; j < packets.length; j++)    {
        assert.equal(packets[j].toString(), expected_packets[j].toString(), `At position ${j}: ${packets[j]} != ${expected_packets[j]}`);
    }
    var p_hash_info = payload.concat(msg.time_58).join('');
    var p_hash = base.SHA384(p_hash_info);
    assert.equal(msg.id, base.to_base_58(new BigInt(p_hash, 16)));
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
                for (var j = 0; j < base.compression.length; j++)   {
                    assert(test_string.equals( base.decompress( base.compress(test_string, base.compression[j]), base.compression[j] ) ));
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

    describe('protocol', function() {
        it('should have information assigned to the correct getters', function()    {
            for (var i = 0; i < 250; i++)   {
                var sub = get_random_buffer(4);
                var enc = get_random_buffer(4);
                // Make sure it's normal ascii. utf-8 intentionally not supported here
                for (var j = 0; j < 4; j++) {
                    sub[j] = sub[j] % 128;
                    enc[j] = enc[j] % 128;
                }
                var test = new base.protocol(sub, enc);
                assert.equal(test.subnet, sub);
                assert.equal(test.encryption, enc);
                var p_hash_info = [sub, enc, base.protocol_version].join('');
                var p_hash = base.SHA256(p_hash_info);
                assert.equal(test.id, base.to_base_58(new BigInt(p_hash, 16)));
            }
        });
    });

    describe('pathfinding_message', function()  {
        it('should pass some short, statically defined tests', function()  {
            const string = '\x00\x00\x00{\x00\x00\x00\t\x00\x00\x00\x0b\x00\x00\x00B\x00\x00\x00\x06\x00\x00\x00\x0bbroadcasttest sender2ypz9RTBAFbw75WSJTNwaXZ6zSVLG8wvqbQDNRtoh74Hkxg3JAozHAZtCfwg1PEmpe3EdmDctest packet';
            const zlib = new Buffer("\x00\x00\x00{x\x9cc``\xe0d``\xe0\x06b' f\x03\xb1\x93\x8a\xf2\x13S\x92\x13\x8bKJR\x8bK\x14\x8aS\xf3RR\x8b\x8c*\x0b\xaa,\x83B\x9c\x1c\xdd\x92\xca\xcdM\xc3\x83\xbdB\xfc\xca\x13#\xa2\xcc\xaa\x82\xc3|\xdc-\xca\xcb\n\x93\x02]\xfc\x82J\xf23\xccM<\xb2+\xd2\x8d\xbd\x1c\xf3\xab<\x1c\xa3J\x9c\xd3\xca\xd3\r\x03\\s\x0bR\x8d]Sr]\x92\xc1F\x16$&g\xa7\x96\x00\x00\xbfC%T", "ascii");
            const gzip = new Buffer("\x00\x00\x00\x87\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\x03c``\xe0d``\xe0\x06b' f\x03\xb1\x93\x8a\xf2\x13S\x92\x13\x8bKJR\x8bK\x14\x8aS\xf3RR\x8b\x8c*\x0b\xaa,\x83B\x9c\x1c\xdd\x92\xca\xcdM\xc3\x83\xbdB\xfc\xca\x13#\xa2\xcc\xaa\x82\xc3|\xdc-\xca\xcb\n\x93\x02]\xfc\x82J\xf23\xccM<\xb2+\xd2\x8d\xbd\x1c\xf3\xab<\x1c\xa3J\x9c\xd3\xca\xd3\r\x03\\s\x0bR\x8d]Sr]\x92\xc1F\x16$&g\xa7\x96\x00\x00m\xbeb\xef{\x00\x00\x00", "ascii");

            var pm = base.pathfinding_message.feed_string(string);
            var msg = new base.message(pm);

            var zlib_pm = base.pathfinding_message.feed_string(zlib, false, [base.flags.zlib]);

            var gzip_pm = base.pathfinding_message.feed_string(gzip, false, [base.flags.gzip]);

            var expected = [ new Buffer('broadcast'), new Buffer('test sender'), '2ypz9RTBAFbw75WSJTNwaXZ6zSVLG8wvqbQDNRtoh74Hkxg3JAozHAZtCfwg1PEmpe', '3EdmDc', new Buffer('test packet') ];

            assert (JSON.stringify(pm.packets) == JSON.stringify(expected), "pathfinding_message is not extracting packets correctly");
            assert (JSON.stringify(msg.packets) == JSON.stringify(expected.slice(4)), "message is not extracting from pathfinding_message correctly");

            assert (JSON.stringify(zlib_pm.packets) == JSON.stringify(expected), "pathfinding_message is not extracting zlib packets correctly");

            assert (JSON.stringify(gzip_pm.packets) == JSON.stringify(expected), "pathfinding_message is not extracting gzip packets correctly");
        });

        it('should serialize and deserialize', function()   {
            this.timeout(0);
            for (var i = 0; i < 250; i++)   {
                for (var j = 0; j <= base.compression.length; j++)  {
                    var compressions = [];
                    if (j < base.compression.length)    {
                        compressions.push(base.compression[j]);
                    }
                    var payload = get_random_array(Math.floor(Math.random() * 16));
                    var msg = new base.pathfinding_message(base.flags.broadcast, new Buffer('\u00ff', 'ascii'), payload, compressions);
                    var deserialized = base.pathfinding_message.feed_string(msg.string, false, compressions);
                    test_pathfinding_message(payload, deserialized);
                }
            }
        });

        it('should have information assigned to the correct getters', function()    {
            for (var i = 0; i < 250; i++)   {
                var payload = get_random_array(Math.floor(Math.random() * 16));
                test_pathfinding_message(payload);
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
                var base_msg = new base.pathfinding_message(base.flags.broadcast, sen, pac);
                var test = new base.message(base_msg, null);
                assert.equal(test.packets, pac);
                assert.equal(test.msg, base_msg);
                assert.equal(test.sender.toString(), sen);
                assert.equal(test.id, base_msg.id);
                assert.equal(test.time, base_msg.time);
                assert.equal(test.time_58, base_msg.time_58);
                assert(base.from_base_58(test.time_58).equals(test.time));
            }
        })
    });
});
