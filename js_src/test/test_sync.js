"use strict";

const assert = require('assert');
const base = require('../base.js');
const sync = require('../sync.js');
var start_port = 44665;

describe('sync', function() {

    describe('SyncSocket', function() {

        let transports = {
            'plaintext': 'Plaintext',
            'SSL/TLS': 'SSL',
            'websocket': 'ws'
        };

        for (let text in transports)    {

            function test_storage(leasing, done)    {
                var node1 = new sync.SyncSocket('localhost', start_port++, new base.Protocol('sync', transports[text]), leasing);
                var node2 = new sync.SyncSocket('localhost', start_port++, new base.Protocol('sync', transports[text]), leasing);

                node1.connect(...node2.addr);

                setTimeout(function()   {
                    node1.set('test', 'value');
                    node2.update({
                        '测试': '成功',
                        'store': 'store',
                        'array': [1,2,3,4,5,6,7,8,9],
                        'number': 256
                    });
                    setTimeout(function()   {
                        assert.ok(node1.get('test'));
                        assert.ok(node2.get('test'));
                        assert.equal(node1.get('测试'), '成功');
                        assert.equal(node2.get('测试'), '成功');
                        assert.equal(node1.get('store'), 'store');
                        assert.equal(node2.get('store'), 'store');
                        assert.equal(node1.get('number'), 256);
                        assert.equal(node2.get('number'), 256);
                        assert.deepEqual(node1.get('array'), [1,2,3,4,5,6,7,8,9]);
                        assert.deepEqual(node2.get('array'), [1,2,3,4,5,6,7,8,9]);
                        done();
                    }, 500);
                }, 250);
            };

            it(`should store values correctly when leasing (over ${text})`, function(done) {
                this.timeout(2500 * (3 && text === 'SSL/TLS' + 1));
                test_storage(true, done);
            });

            it(`should store values correctly when not leasing (over ${text})`, function(done) {
                this.timeout(2500 * (3 && text === 'SSL/TLS' + 1));
                test_storage(false, done);
            });

            function test_delta(done)    {
                var node1 = new sync.SyncSocket('localhost', start_port++, new base.Protocol('sync', transports[text]), false);
                var node2 = new sync.SyncSocket('localhost', start_port++, new base.Protocol('sync', transports[text]), false);
                var node3 = new sync.SyncSocket('localhost', start_port++, new base.Protocol('sync', transports[text]), false);

                node1.connect(...node2.addr);
                node1.connect(...node3.addr);

                setTimeout(function()   {
                    setTimeout(function()   {
                        node1.apply_delta('store', {'seven': 7})
                        node2.apply_delta('store', {'array': [1, 2, 3, 4, 5, 6, 7, 8, 9], 'number': 256})
                        node3.apply_delta('store', {'three': {'three': 'three'}})
                        setTimeout(function()   {
                            let should_be = {'seven': 7,
                                             'array': [1, 2, 3, 4, 5, 6, 7, 8, 9],
                                             'number': 256,
                                             'three': {'three': 'three'}};
                            assert.deepEqual(node1.get('store'), should_be);
                            assert.deepEqual(node2.get('store'), should_be);
                            assert.deepEqual(node3.get('store'), should_be);
                            done();
                        }, 500);
                    }, 250);
                }, 250);
            };

            it(`should apply deltas correctly when not leasing (over ${text})`, function(done) {
                this.timeout(2500 * (3 && text === 'SSL/TLS' + 1));
                test_delta(done);
            });
        }

    });

});
