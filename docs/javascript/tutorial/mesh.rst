Mesh Socket
~~~~~~~~~~~

Basic Usage
-----------

To connect to a mesh network, you will use the :js:class:`~js2p.mesh.mesh_socket` object. You can instantiate this as follows:

.. code-block:: javascript

    > const mesh = require('js2p').mesh;
    > sock = new mesh.mesh_socket('0.0.0.0', 4444);

Using ``'0.0.0.0'`` will automatically grab your LAN address. If you want to use an outward-facing internet connection, there is a little more work. First you need to make sure that you have a port forward setup (NAT busting is not in the scope of this project). Then you will specify this outward address as follows:

.. code-block:: javascript

    > const mesh = require('js2p').mesh;
    > sock = new mesh.mesh_socket('0.0.0.0', 4444, null, ['35.24.77.21', 44565]);

If `nodejs-websocket <https://www.npmjs.com/package/nodejs-websocket>`_ is installed, then you can use websockets as a transport layer (for instance, to allow communication with a browser). If `node-forge <https://www.npmjs.com/package/node-forge>`_ is installed, then you can use SSL/TLS as a transport layer. You can do this by providing a :js:class:`~js2p.base.protocol` object, like so:

.. code-block:: javascript

    > const mesh = require('js2p').mesh;
    > const base = require('js2p').base;
    > var app_description = 'A string which describes your application';
    > var SSL = new mesh.mesh_socket('0.0.0.0', 4444, new base.protocol(app_description, 'SSL'));
    > var WS = new mesh.mesh_socket('0.0.0.0', 5555, new base.protocol(app_description, 'ws'));

Specifying a different protocol object will ensure that you *only* can connect to people who share your object structure. So if someone has the description ``'mesh2'`` instead of ``'mesh'``, you will fail to connect.

Unfortunately, this failure is currently silent. Because this is asynchronous in nature, raising an error is not possible. Because of this, it's good to perform the following check the truthiness of :js:attr:`.mesh_socket.routing_table`. If it is truthy, then you are connected to the network.

To send a message, you should use the :js:func:`~js2p.mesh.mesh_socket.send` method. Each argument you supply will correspond to a packet that your peer receives. In addition, there are two keyed arguments you can use. ``flag`` will specify how other nodes relay this. These flags are defined in :js:data:`js2p.base.flags` . ``broadcast`` will indicate that other nodes are supposed to relay it. ``whisper`` will indicate that your peers are *not* supposed to relay it. There are other technically valid options, but they are not recommended. ``type`` will specify what actions other nodes are supposed to take on it. It defaults to ``broadcast``, which indicates no change from the norm. There are other valid options, but they should normally be left alone, unless you've written a handler (see below) to act on this.

.. code-block:: javascript

    > sock.send(['this is', 'a test']);

Receiving is a bit simpler. When you call the :js:func:`~js2p.mesh.mesh_socket.recv` method, you receive a :js:class:`~js2p.base.message` object. This has a number of methods outlined which you can find by clicking its name. Most notably, you can get the packets in a message with :js:attr:`~js2p.base.message.packets`, and reply directly with :js:func:`~js2p.base.message.reply`.

.. code-block:: javascript

    > sock.send(['Did you get this?']);
    > // a peer replies
    > var msg = sock.recv();
    > console.log(msg);
    message {
     type: 2
     packets: [ 'Yes', 'I did' ]
     sender: '8vu4oLsvVBsnnH6N83z6y6RZqrMKRrVHr44xRwXCFaU9qcyYsjJDzVfKwmdGp51K4d' }
    > msg.packets.forEach((packet) => {
    ... var str = packet.toString()
    ... console.log(util.inspect(str));
    ... });
    '2'
    'yes'
    'I did'
    > console.log(msg.packets);
    [ 2, 'yes', 'I did' ]
    > sock.recv(10).forEach((msg) => {
    ... msg.reply(["Replying to a list", {'here': 10, 'have some': 'data'}]);
    ... });

Events
------

In addition to the above, the :js:class:`js2p.mesh.mesh_socket` object has two :js:class:`Event` s.

First there's :js:func:`js2p.mesh.mesh_socket Event 'connect'`. This is called whenever you finalize a connection to your distributed service. It is *also* called if you reconnect to the service after some failure.

.. code-block:: javascript

    > sock.once('connect', (conn)=>{
    ... // conn is a reference to the socket, in case you're in a new scope
    ... // the .once() indicates that this event should only be called once
    ... });
    >
    > sock.on('connect', (conn)=>{
    ... // conn is still a reference to the socket
    ... // the .on() indicates that this event should be called *every* time
    ... });

This class has one other event: :js:func:`js2p.mesh.mesh_socket Event 'message'`. This one is a little bit trickier to use, and it's recommended that you only have one callback in place at any given time. The event is called any time you receive a message that *is not* handled by one of the "priveledged" callbacks. Such callbacks include the ones for dealing with new peers on the network.

.. code-block:: javascript

    > sock.on('message', (conn)=>{
    ... // note that you are not passed a reference to the message.
    ... // This means that you must explicitly recv().
    ... let msg = conn.recv();
    ... if (msg !== undefined)  {
    ..... // note the guard clause for if someone else registered a callback
    ..... msg.reply(['this is an example'])
    ..... }
    ... });

Advanced Usage
--------------

In addition to this, you can register a custom handler for incoming messages. This is appended to the end of the included ones. When writing your handler, you must keep in mind that you are only passed a :js:class:`~js2p.base.message` object and a :js:class:`~js2p.mesh.mesh_connection`. Fortunately you can get access to everything you need from these objects.

.. code-block:: python

    > funciton example(msg, handler)   {
    ... const packets = msg.packets;
    ... if (packets[0] === some_flag)   {
    ..... some_action(msg, handler);
    ..... return true; // This tells the socket that the message has been processed
    ..... }
    ... };
    > const js2p = require('js2p');
    > let sock = js2p.mesh.mesh_socket('0.0.0.0', 4444);
    > sock.register_handler(example);

Use In A Browser
----------------

There are a few differences if you want to use this in a browser. First, you can only use websockets as a transport layer. That means that any servers which want to listen *must* have `nodejs-websocket <https://www.npmjs.com/package/nodejs-websocket>`_ installed. The code run in the browser uses the natively supplied :js:class:`WebSocket` implementation.

Browser nodes also cannot receive connections. That means they *must* connect to a "server" at some point.

Lastly, you do not need to :js:func:`require` this module, it is provided for you in a file. This can be loaded either from the latest release (starting in 0.5), or by cloning the repository and calling ``make browser``.
