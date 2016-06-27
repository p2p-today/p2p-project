var base = require('./p2p.js');
const assert = require('assert');

var string = '\u0000\u0000\u0000{\u0000\u0000\u0000\t\u0000\u0000\u0000\u000b\u0000\u0000\u0000B\u0000\u0000\u0000\u0006\u0000\u0000\u0000\u000bbroadcasttest sender2ypz9RTBAFbw75WSJTNwaXZ6zSVLG8wvqbQDNRtoh74Hkxg3JAozHAZtCfwg1PEmpe3EdmDctest packet'
var pm = base.pathfinding_message.feed_string(base.default_protocol, string)
var msg = new base.message(pm)

var expected = [ 'broadcast', 'test sender', '2ypz9RTBAFbw75WSJTNwaXZ6zSVLG8wvqbQDNRtoh74Hkxg3JAozHAZtCfwg1PEmpe', '3EdmDc', 'test packet' ]

assert (JSON.stringify(pm.packets) == JSON.stringify(expected), "pathfinding_message is not extracting packets correctly")
assert (JSON.stringify(msg.packets) == JSON.stringify(expected.slice(4)), "message is not extracting from pathfinding_message correctly")