Usage Guide
===========

Basic Usage
-----------

To connect to a mesh network, you will use the ``mesh_socket`` object. You can instantiate this as follows:

.. code-block:: python

    >>> import py2p
    >>> sock = py2p.mesh_socket('0.0.0.0', 4444)

Using ``'0.0.0.0'`` will automatically grab you LAN address. If you want to use an outward-facing internet connection, you will need to specify this address as follows:

.. code-block:: python

    >>> import py2p
    >>> sock = py2p.mesh_socket('0.0.0.0', 4444, out_addr=('8.8.8.8', 8888))

In addition, you can enable SSL encryption if you have `PyOpenSSL` or `cryptography` installed. This works by specifying a custom protocol object, like so:

.. code-block:: python

    >>> import py2p
    >>> sock = py2p.mesh_socket('0.0.0.0', 4444, prot=py2p.protocol('mesh', 'SSL'))

Eventually that will be the default, but while things are being tested it will default to plaintext. Specifying a different protocol object will ensure that you *only* can connect to people who share your object structure. So if someone has ``'mesh2'`` instead of ``'mesh'``, you will fail to connect.

Unfortunately, this failure is currently silent. Because this is asynchronous in nature, raising an ``Exception`` is not possible. Because of this, it's good to perform the following check after connecting:

.. code-block:: python

    >>> import py2p, time
    >>> sock = py2p.mesh_socket('0.0.0.0', 4444)
    >>> sock.connect('192.168.1.14', 4567)
    >>> time.sleep(1)
    >>> assert sock.routing_table

To send a message, you should use the ``send`` method. Each argument you supply will correspond to a packet that your peer receives. In addition, there are two keyed arguments you can use. ``flag`` will specify how other nodes relay this. ``b'broadcast'`` will indicate that other nodes are supposed to relay it. ``b'whisper'`` will indicate that your peers are *not* supposed to relay it. There are other technically valid options, but they are not recommended. ``type`` will specify what actions other nodes are supposed to take on it. It defaults to ``b'broadcast'``, which indicates no change from the norm. There are other valid options, but they should normally be left alone, unless you've written a handler (see below) to act on this.

.. code-block:: python

    >>> sock.send('this is', 'a test')

Receiving is a bit simpler. When you call the ``recv`` method, you receive a `message` object. This has a number of methods outlined `here <https://github.com/gappleto97/p2p-project/blob/master/py_src/API.rst>`__. Most notably, you can get the packets in a message with ``message.packets``, and reply directly with ``message.reply()``.

.. code-block:: python

    >>> sock.send('Did you get this?')
    >>> msg = sock.recv()
    >>> print(msg)
    message(type=b'whisper', packets=[b'yes', b'I did'], sender=b'6VnYj9LjoVLTvU3uPhy4nxm6yv2wEvhaRtGHeV9wwFngWGGqKAzuZ8jK6gFuvq737V')
    >>> print(msg.packets)
    [b'whisper', b'yes', b'I did']
    >>> for msg in sock.recv(10):
    ...     msg.reply("Replying to a list")

Advanced Usage
--------------

In addition to this, you can register a custom handler for incoming messages. This is appended to the end of the included ones. When writing your handler, you must keep in mind that you are only passed a message object and a link to the receiving connection. Fortunately you can get access to everything you need from these objects. To see what methods each has, see the `API docs <https://github.com/gappleto97/p2p-project/blob/master/py_src/API.rst>`__. An example service would look like this:

.. code-block:: python

    >>> def relay_tx(msg, handler):
    ...     """Relays bitcoin transactions to various services"""
    ...     packets = msg.packets  # Gives a list of the non-metadata packets
    ...     server = msg.server    # Returns your mesh_socket object
    ...     if packets[0] == b'tx_relay':  # It's important that this flag is bytes
    ...         from pycoin import tx, services
    ...         relay = tx.Tx.from_bin(packets[1])
    ...         services.blockchain_info.send_tx(relay)
    ...         services.insight.InsightProvider().send_tx(relay)
    ...         return True        # This tells the daemon to stop calling handlers
    ... 
    >>> import py2p
    >>> sock = py2p.mesh_socket('0.0.0.0', 4444)
    >>> sock.register_handler(relay_tx)

If this does not take two arguments, `register_handler` will raise a `ValueError`. To help debug these services, you can specify a `debug_level` in the constructor. Using a value of 5, you can see when it enters into each handler, as well as every message which goes in or out.
