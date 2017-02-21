"use strict";

const assert = require('assert');
const base = require('../base.js');
const chord = require('../chord.js');
const util = require('util');
var start_port = 44765;

describe('chord', function() {

    describe('ChordSocket', function() {

        let transports = {
            'plaintext': 'Plaintext',
            'SSL/TLS': 'SSL',
            'websocket': 'ws'
        };

        for (let text in transports)    {

            it(`should store values correctly (over ${text})`, function(done) {
                this.timeout(2500 * (3 && text === 'SSL/TLS' + 1));
                var node1 = new chord.ChordSocket('localhost', start_port++, new base.Protocol('chord', transports[text]));
                var node2 = new chord.ChordSocket('localhost', start_port++, new base.Protocol('chord', transports[text]));

                node1.join();
                node2.join();
                node1.connect(node2.addr[0], node2.addr[1]);

                setTimeout(()=>{
                    node1.set('test', 'value');
                    setTimeout(()=>{
                        let count = 10;
                        let errs = [];
                        function shouldEqual(desired) {
                            return function(val) {
                                try {
                                    assert.deepEqual(val, desired);
                                } catch(e) {
                                    errs.push(e);
                                }
                                --count;
                            }
                        }
                        function onError(e){
                            --count;
                            errs.push(e);
                        }
                        node1.get('test').then(shouldEqual('value')).catch(onError);
                        node2.get('test').then(shouldEqual('value')).catch(onError);
                        node2.update({
                            '测试': '成功',
                            'store': 'store',
                            'array': [1,2,3,4,5,6,7,8,9],
                            'number': 256
                        });
                        setTimeout(()=>{
                            node1.get('测试').then(shouldEqual('成功')).catch(onError);
                            node2.get('测试').then(shouldEqual('成功')).catch(onError);
                            node1.get('store').then(shouldEqual('store')).catch(onError);
                            node2.get('store').then(shouldEqual('store')).catch(onError);
                            node1.get('number').then(shouldEqual(256)).catch(onError);
                            node2.get('number').then(shouldEqual(256)).catch(onError);
                            node1.get('array').then(shouldEqual([1,2,3,4,5,6,7,8,9])).catch(onError);
                            node2.get('array').then(shouldEqual([1,2,3,4,5,6,7,8,9])).catch(onError);
                            function check() {
                                if (!count) {
                                    if (!errs.length) {
                                        done();
                                    }
                                    else {
                                        done(new Error(errs.concat([
                                            util.inspect(node1.status),
                                            util.inspect(node2.status)
                                        ])));
                                    }
                                }
                                else {
                                    setTimeout(check, 100);
                                }
                            }
                            check();
                        }, 500);
                    }, 500);
                }, 250);
            });
        }

    });

});
