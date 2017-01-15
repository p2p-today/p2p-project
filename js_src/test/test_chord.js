"use strict";

const assert = require('assert');
const chord = require('../chord.js');
var start_port = 44765;

describe('chord', function() {

    describe('chord_socket', function() {

        it('should store values correctly', function(done) {
            this.timeout(2500);
            var node1 = new chord.chord_socket('localhost', start_port++);
            var node2 = new chord.chord_socket('localhost', start_port++);

            node1.join();
            node2.join();
            node1.connect(node2.addr[0], node2.addr[1]);

            setTimeout(()=>{
                node1.set('test', 'value');
                setTimeout(()=>{
                    let count = 6;
                    let errs = [];
                    function shouldEqual(desired) {
                        return function(val) {
                            try {
                                assert.equal(val.toString(), desired);
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
                    node1.get('test').then(shouldEqual('value'), onError);
                    node2.get('test').then(shouldEqual('value'), onError);
                    node2.update({
                        '测试': '成功',
                        'store': 'store'
                    });
                    setTimeout(()=>{
                        node1.get('测试').then(shouldEqual('成功'), onError);
                        node2.get('测试').then(shouldEqual('成功'), onError);
                        node1.get('store').then(shouldEqual('store'), onError);
                        node2.get('store').then(shouldEqual('store'), onError);
                        function check() {
                            if (!count) {
                                if (!errs.length) {
                                    done();
                                }
                                else {
                                    done(errs);
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

    });

});