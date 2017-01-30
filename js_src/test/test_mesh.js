"use strict";

var assert = require('assert');
var base = require('../base.js');
var mesh = require('../mesh.js');
var start_port = 44565;

describe('mesh', function() {

    describe('mesh_socket', function()  {

        let transports = {
            'plaintext': 'Plaintext',
            'SSL/TLS': 'SSL',
            'websocket': 'wss'
        };

        for (let text in transports)    {

            it(`should propagate messages to everyone in the network (over ${text})`, function(done)   {
                this.timeout(6000 * (3 && text === 'SSL/TLS' + 1));
                var count = 3;

                var nodes = [new mesh.mesh_socket('localhost', start_port++, new base.protocol('mesh', transports[text]))];
                for (var j = 1; j < count; j++) {
                    var node = new mesh.mesh_socket('localhost', start_port++, new base.protocol('mesh', transports[text]));
                    var addr = nodes[nodes.length - 1].addr;
                    node.connect(addr[0], addr[1]);
                    nodes.push(node);
                }
                setTimeout(function()   {
                    nodes[0].send(['hello']);
                    setTimeout(function()   {
                        for (var h = 1; h < count; h++) {
                            var msg = nodes[h].recv();
                            assert.ok(msg);
                        }
                        done();
                    }, count * 500);
                }, count * 250);
            });

            it(`should reject connections with a different protocol object (over ${text})`, function(done)    {
                this.timeout(2000 * (3 && text === 'SSL/TLS' + 1));
                var node1 = new mesh.mesh_socket('localhost', start_port++, new base.protocol('mesh1', transports[text]));
                var node2 = new mesh.mesh_socket('localhost', start_port++, new base.protocol('mesh2', transports[text]));

                node1.connect(node2.addr[0], node2.addr[1]);
                setTimeout(function()   {
                    assert.deepEqual(node1.routing_table, {});
                    assert.deepEqual(node2.routing_table, {});
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

            function test_callback(callback, done)    {
                var node1 = new mesh.mesh_socket('localhost', start_port++, new base.protocol('mesh', transports[text]));
                var node2 = new mesh.mesh_socket('localhost', start_port++, new base.protocol('mesh', transports[text]));

                node2.register_handler(callback);
                node1.connect(node2.addr[0], node2.addr[1]);

                setTimeout(function()   {
                    node1.send(['test']);
                    setTimeout(function()   {
                        assert.ok(node1.recv());
                        assert.ok(!node2.recv());
                        node1.send(['not test']);
                        setTimeout(function()   {
                            assert.ok(!node1.recv());
                            assert.ok(node2.recv());
                            done();
                        }, 500);
                    }, 500);
                }, 250);
            }

            it(`should be able to register and use message callbacks (over ${text})`, function(done)  {
                this.timeout(2000 * (3 && text === 'SSL/TLS' + 1));
                test_callback(register_1, done);
            });

            it(`should let you reply to messages via the message object (over ${text})`, function(done)   {
                this.timeout(2000 * (3 && text === 'SSL/TLS' + 1));
                test_callback(register_2, done);
            });
        }



    });

});
