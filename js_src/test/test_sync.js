"use strict";

const assert = require('assert');
const sync = require('../sync.js');
var start_port = 44665;

describe('sync', function() {

    describe('sync_socket', function() {

        function test_storage(leasing, done)    {
            var node1 = new sync.sync_socket('localhost', start_port++, leasing);
            var node2 = new sync.sync_socket('localhost', start_port++, leasing);

            node1.connect(node2.addr[0], node2.addr[1]);

            setTimeout(function()   {
                node1.set('test', 'value');
                setTimeout(function()   {
                    assert.ok(node1.get('test'));
                    assert.ok(node2.get('test'));
                    node2.update({
                        '测试': '成功',
                        'store': 'store'
                    });
                    setTimeout(function()   {
                        assert.equal(node1.get('测试').toString(), '成功');
                        assert.equal(node2.get('测试').toString(), '成功');
                        assert.equal(node1.get('store').toString(), 'store');
                        assert.equal(node2.get('store').toString(), 'store');
                        done();
                    }, 500);
                }, 500);
            }, 250);
        };

        it('should store values correctly when leasing', function(done) {
            this.timeout(2500);
            test_storage(true, done);
        });

        it('should store values correctly when not leasing', function(done) {
            this.timeout(2500);
            test_storage(false, done);
        });

    });

});