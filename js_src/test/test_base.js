"use strict";

const assert = require('assert');
const base = require('../base.js');

describe('base', function() {

    describe('compress/decompress', function() {

        it('should always be reversable', function() {
            for (var i = 0; i < 1000; i++)  {
                // Step one: generate a random buffer up to size 40
                var len = Math.floor(Math.random() * 40);
                var pre_buffer = [];
                for (var j = 0; j < len; j++)   {
                    pre_buffer.push(Math.floor(Math.random() * 256));
                }
                // Then: For each flag in compression, assert that the compressed then decompressed version equals the original
                var test_string = new Buffer(pre_buffer);
                for (var j = 0; j < base.compression.length; j++)   {
                    assert(test_string.equals( base.decompress( base.compress(test_string, base.compression[j]), base.compression[j] ) ));
                }
            }
        });
    });

    describe('to_base_58/from_base_58', function()  {
        it('should always be reversable', function()    {
            for (var i = 0; i < 1000; i++)  {
                var test = Math.floor(Math.random() * 1000000000);
                var shouldEqual = base.from_base_58(base.to_base_58(test));
                assert(shouldEqual.equals(test), `${test} != ${shouldEqual}`);
            }
        });

        it('should return "1" if fed 0', function() {
            assert.equal("1", base.to_base_58(0));
        });
    });

    describe('pathfinding_message', function()  {
        it('should pass some short, statically defined tests', function()  {
            var string = '\x00\x00\x00{\x00\x00\x00\t\x00\x00\x00\x0b\x00\x00\x00B\x00\x00\x00\x06\x00\x00\x00\x0bbroadcasttest sender2ypz9RTBAFbw75WSJTNwaXZ6zSVLG8wvqbQDNRtoh74Hkxg3JAozHAZtCfwg1PEmpe3EdmDctest packet';
            var zlib = Buffer("\x00\x00\x00{x\x9cc``\xe0d``\xe0\x06b' f\x03\xb1\x93\x8a\xf2\x13S\x92\x13\x8bKJR\x8bK\x14\x8aS\xf3RR\x8b\x8c*\x0b\xaa,\x83B\x9c\x1c\xdd\x92\xca\xcdM\xc3\x83\xbdB\xfc\xca\x13#\xa2\xcc\xaa\x82\xc3|\xdc-\xca\xcb\n\x93\x02]\xfc\x82J\xf23\xccM<\xb2+\xd2\x8d\xbd\x1c\xf3\xab<\x1c\xa3J\x9c\xd3\xca\xd3\r\x03\\s\x0bR\x8d]Sr]\x92\xc1F\x16$&g\xa7\x96\x00\x00\xbfC%T", "ascii");
            var gzip = Buffer("\x00\x00\x00\x87\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\x03c``\xe0d``\xe0\x06b' f\x03\xb1\x93\x8a\xf2\x13S\x92\x13\x8bKJR\x8bK\x14\x8aS\xf3RR\x8b\x8c*\x0b\xaa,\x83B\x9c\x1c\xdd\x92\xca\xcdM\xc3\x83\xbdB\xfc\xca\x13#\xa2\xcc\xaa\x82\xc3|\xdc-\xca\xcb\n\x93\x02]\xfc\x82J\xf23\xccM<\xb2+\xd2\x8d\xbd\x1c\xf3\xab<\x1c\xa3J\x9c\xd3\xca\xd3\r\x03\\s\x0bR\x8d]Sr]\x92\xc1F\x16$&g\xa7\x96\x00\x00m\xbeb\xef{\x00\x00\x00", "ascii");

            var pm = base.pathfinding_message.feed_string(string);
            var msg = new base.message(pm);

            var zlib_pm = base.pathfinding_message.feed_string(zlib, false, [base.flags.zlib]);

            var gzip_pm = base.pathfinding_message.feed_string(gzip, false, [base.flags.gzip]);

            var expected = [ Buffer('broadcast'), Buffer('test sender'), '2ypz9RTBAFbw75WSJTNwaXZ6zSVLG8wvqbQDNRtoh74Hkxg3JAozHAZtCfwg1PEmpe', '3EdmDc', Buffer('test packet') ];

            assert (JSON.stringify(pm.packets) == JSON.stringify(expected), "pathfinding_message is not extracting packets correctly");
            assert (JSON.stringify(msg.packets) == JSON.stringify(expected.slice(4)), "message is not extracting from pathfinding_message correctly");

            assert (JSON.stringify(zlib_pm.packets) == JSON.stringify(expected), "pathfinding_message is not extracting zlib packets correctly");

            assert (JSON.stringify(gzip_pm.packets) == JSON.stringify(expected), "pathfinding_message is not extracting gzip packets correctly");
        });
    });
});
