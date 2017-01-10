"use strict";

var assert = require('assert');
var base = require('../base.js');
var BigInt = require('big-integer');

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
                for (let flag of base.compression)   {
                    try {
                        assert(test_string.equals( base.decompress( base.compress(test_string, flag), flag ) ));
                    }
                    catch (e)   {
                        throw new Error(`${util.inspect(test_string)}, ${util.inspect(flag)}`, e);
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

    describe('InternalMessage', function()  {
        it('should pass some short, statically defined tests', function()  {
            var string = new Buffer([0,0,0,123,0,0,0,9,98,114,111,97,100,99,97,115,116,0,0,0,11,116,101,115,116,32,115,101,110,100,101,114,0,0,0,66,50,121,112,122,57,82,84,66,65,70,98,119,55,53,87,83,74,84,78,119,97,88,90,54,122,83,86,76,71,56,119,118,113,98,81,68,78,82,116,111,104,55,52,72,107,120,103,51,74,65,111,122,72,65,90,116,67,102,119,103,49,80,69,109,112,101,0,0,0,6,51,69,100,109,68,99,0,0,0,11,116,101,115,116,32,112,97,99,107,101,116]);
            var zlib = new Buffer([0,0,0,128,120,156,61,204,61,14,130,48,20,0,224,78,38,198,75,120,5,69,69,199,86,80,66,12,81,32,106,216,250,243,196,132,96,43,125,177,218,211,211,201,241,91,62,66,200,84,12,154,43,201,45,6,204,16,44,206,45,188,20,12,129,108,249,51,126,87,214,140,30,132,139,215,183,42,175,11,199,239,205,198,87,215,211,113,235,62,111,113,73,138,18,245,51,94,101,221,183,141,114,170,125,70,27,220,63,92,187,56,167,189,129,176,76,162,84,245,137,252,247,134,203,14,112,4,223,203,37,84]);
            var gzip = new Buffer([0,0,0,140,31,139,8,0,76,158,77,88,0,255,61,204,61,14,130,48,20,0,224,78,38,198,75,120,5,69,69,199,86,80,66,12,81,32,106,216,250,243,196,132,96,43,125,177,218,211,211,201,241,91,62,66,200,84,12,154,43,201,45,6,204,16,44,206,45,188,20,12,129,108,249,51,126,87,214,140,30,132,139,215,183,42,175,11,199,239,205,198,87,215,211,113,235,62,111,113,73,138,18,245,51,94,101,221,183,141,114,170,125,70,27,220,63,92,187,56,167,189,129,176,76,162,84,245,137,252,247,134,203,14,112,4,190,252,209,7,123,0,0,0]);
            var snappy = new Buffer([0,0,0,126,123,240,122,0,0,0,9,98,114,111,97,100,99,97,115,116,0,0,0,11,116,101,115,116,32,115,101,110,100,101,114,0,0,0,66,50,121,112,122,57,82,84,66,65,70,98,119,55,53,87,83,74,84,78,119,97,88,90,54,122,83,86,76,71,56,119,118,113,98,81,68,78,82,116,111,104,55,52,72,107,120,103,51,74,65,111,122,72,65,90,116,67,102,119,103,49,80,69,109,112,101,0,0,0,6,51,69,100,109,68,99,0,0,0,11,116,101,115,116,32,112,97,99,107,101,116]);

            var pm = base.InternalMessage.feed_string(string);
            var msg = new base.message(pm);

            var expected = [ new Buffer('broadcast'), new Buffer('test sender'), '2ypz9RTBAFbw75WSJTNwaXZ6zSVLG8wvqbQDNRtoh74Hkxg3JAozHAZtCfwg1PEmpe', '3EdmDc', new Buffer('test packet') ];

            assert (JSON.stringify(pm.packets) === JSON.stringify(expected), "InternalMessage is not extracting packets correctly");
            assert (JSON.stringify(msg.packets) === JSON.stringify(expected.slice(4)), "message is not extracting from InternalMessage correctly");

            if (base.zlib)  {
                var zlib_pm = base.InternalMessage.feed_string(zlib, false, [base.flags.zlib]);
                assert (JSON.stringify(zlib_pm.packets) === JSON.stringify(expected), "InternalMessage is not extracting zlib packets correctly");

                var gzip_pm = base.InternalMessage.feed_string(gzip, false, [base.flags.gzip]);
                assert (JSON.stringify(gzip_pm.packets) === JSON.stringify(expected), "InternalMessage is not extracting gzip packets correctly");
            }

            if (base.snappy)    {
                var snappy_pm = base.InternalMessage.feed_string(snappy, false, [base.flags.snappy]);
                assert (JSON.stringify(snappy_pm.packets) === JSON.stringify(expected), "InternalMessage is not extracting snappy packets correctly");
            }
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
                    var msg = new base.InternalMessage(base.flags.broadcast, new Buffer('\u00ff', 'ascii'), payload, compressions);
                    var deserialized = base.InternalMessage.feed_string(msg.string, false, compressions);
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
