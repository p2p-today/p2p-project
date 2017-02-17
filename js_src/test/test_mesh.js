"use strict";

var assert = require('assert');
var base = require('../base.js');
var mesh = require('../mesh.js');
const util = require('util');
var start_port = 44565;

describe('mesh', function() {

    describe('mesh_socket', function()  {

        let transports = {
            'plaintext': 'Plaintext',
            'SSL/TLS': 'SSL',
            'websocket': 'ws'
        };

        for (let text in transports)    {

            it(`should propagate messages to everyone in the network (over ${text})`, function(done)   {
                this.timeout(6000 * (3 && text === 'SSL/TLS' + 1));
                let count = 3;

                let nodes = [new mesh.mesh_socket('localhost', start_port++, new base.Protocol('mesh', transports[text]))];
                for (let j = 1; j < count; j++) {
                    let node = new mesh.mesh_socket('localhost', start_port++, new base.Protocol('mesh', transports[text]));
                    let addr = nodes[nodes.length - 1].addr;
                    node.connect(addr[0], addr[1]);
                    nodes.push(node);
                }
                let errs = [];
                for (let h = 1; h < count; h++) {
                    nodes[h].on('message', ()=>{
                        try {
                            assert.ok(nodes[h].recv());
                        }
                        catch (e)   {
                            errs.push(e);
                        }
                        if (--count == 1)   {
                            if (errs.length)
                                done(new Error(util.inspect(errs)));
                            else
                                done();
                        }
                    });
                }
                setTimeout(()=>{
                    nodes[0].send(['hello']);
                }, 250*count);
            });

            it(`should reject connections with a different Protocol object (over ${text})`, function(done)    {
                this.timeout(2000 * (3 && text === 'SSL/TLS' + 1));
                var node1 = new mesh.mesh_socket('localhost', start_port++, new base.Protocol('mesh1', transports[text]));
                var node2 = new mesh.mesh_socket('localhost', start_port++, new base.Protocol('mesh2', transports[text]));

                node1.connect(node2.addr[0], node2.addr[1]);
                setTimeout(function()   {
                    assert.ok(!node1.routing_table.size);
                    assert.ok(!node2.routing_table.size);
                    done();
                }, 500);
            });

            function register_1(msg, handler)   {
                var packets = msg.packets;
                if (packets[1].toString() === 'test')   {
                    handler.send(base.flags.whisper, [base.flags.whisper, 'success']);
                    return true;
                }
            }

            function register_2(msg, handler)   {
                var packets = msg.packets;
                if (packets[1].toString() === 'test')   {
                    msg.reply(['success']);
                    return true;
                }
            }

            function test_callback(callback, register, done)    {
                var node1 = new mesh.mesh_socket('localhost', start_port++, new base.Protocol('mesh', transports[text]));
                var node2 = new mesh.mesh_socket('localhost', start_port++, new base.Protocol('mesh', transports[text]));

                if (register)   {
                    node2.register_handler(callback);
                }
                else    {
                    node2.on('message', callback);
                }
                node1.connect(node2.addr[0], node2.addr[1]);

                setTimeout(function()   {
                    node1.send(['test']);
                    setTimeout(function()   {
                        assert.ok(node1.recv());
                        assert.ok(!node2.recv());
                        node1.send(['not test']);
                        setTimeout(function()   {
                            assert.ok(!node1.recv());
                            if (register)   {
                                assert.ok(node2.recv());
                            }
                            done();
                        }, 500);
                    }, 500);
                }, 250);
            }

            it(`should be able to register and use message callbacks (over ${text})`, function(done)  {
                this.timeout(2000 * (3 && text === 'SSL/TLS' + 1));
                test_callback(register_1, true, done);
            });

            it(`should let you reply to messages via the message object (over ${text})`, function(done)   {
                this.timeout(2000 * (3 && text === 'SSL/TLS' + 1));
                test_callback(register_2, true, done);
            });

            function on_2(conn) {
                let msg = conn.recv();
                let packets = msg.packets;
                if (packets[1].toString() === 'test')   {
                    msg.reply(['success']);
                    return true;
                }
            }

            it(`should be able to register and use event emitter (over ${text})`, function(done)  {
                this.timeout(2000 * (3 && text === 'SSL/TLS' + 1));
                test_callback(on_2, false, done);
            });
        }



    });

});
