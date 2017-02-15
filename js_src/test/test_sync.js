"use strict";

const assert = require('assert');
const base = require('../base.js');
const sync = require('../sync.js');
var start_port = 44665;

describe('sync', function() {

    describe('sync_socket', function() {

        let transports = {
            'plaintext': 'Plaintext',
            'SSL/TLS': 'SSL',
            'websocket': 'ws'
        };

        for (let text in transports)    {

            function test_storage(leasing, done)    {
                var node1 = new sync.sync_socket('localhost', start_port++, leasing, new base.Protocol('sync', transports[text]));
                var node2 = new sync.sync_socket('localhost', start_port++, leasing, new base.Protocol('sync', transports[text]));

                node1.connect(node2.addr[0], node2.addr[1]);

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
        }

    });

});
