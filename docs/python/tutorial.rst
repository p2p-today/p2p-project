Tutorial
========

Mesh Socket
~~~~~~~~~~~

Basic Usage
-----------

To connect to a mesh network, you will use the :py:class:`~py2p.mesh.mesh_socket` object. You can instantiate this as follows:

.. code-block:: python

    >>> import py2p
    >>> sock = py2p.mesh_socket('0.0.0.0', 4444)

Using ``'0.0.0.0'`` will automatically grab your LAN address. If you want to use an outward-facing internet connection, there is a little more work. First you need to make sure that you have a port forward setup (NAT busting is not in the scope of this project). Then you will specify this outward address as follows:

.. code-block:: python

    >>> import py2p
    >>> sock = py2p.mesh_socket('0.0.0.0', 4444, out_addr=('35.24.77.21', 44565))

In addition, you can enable SSL encryption if you have `cryptography <https://cryptography.io/en/latest/installation/>`_ installed. This works by specifying a custom :py:class:`~py2p.base.protocol` object, like so:

.. code-block:: python

    >>> import py2p
    >>> sock = py2p.mesh_socket('0.0.0.0', 4444, prot=py2p.protocol('mesh', 'SSL'))

Eventually that will be the default, but while things are being tested it will default to plaintext. If you do not have `cryptography <https://cryptography.io/en/latest/installation/>`_ installed, this will generate an :py:exc:`ImportError`

Specifying a different protocol object will ensure that you *only* can connect to people who share your object structure. So if someone has ``'mesh2'`` instead of ``'mesh'``, you will fail to connect.

Unfortunately, this failure is currently silent. Because this is asynchronous in nature, raising an :py:exc:`Exception` is not possible. Because of this, it's good to perform the following check after connecting:

.. code-block:: python

    >>> import py2p, time
    >>> sock = py2p.mesh_socket('0.0.0.0', 4444)
    >>> sock.connect('192.168.1.14', 4567)
    >>> time.sleep(1)
    >>> assert sock.routing_table

To send a message, you should use the :py:meth:`~py2p.mesh.mesh_socket.send` method. Each argument you supply will correspond to a packet that your peer receives. In addition, there are two keyed arguments you can use. ``flag`` will specify how other nodes relay this. These flags are defined in :py:class:`py2p.base.flags` . ``broadcast`` will indicate that other nodes are supposed to relay it. ``whisper`` will indicate that your peers are *not* supposed to relay it. There are other technically valid options, but they are not recommended. ``type`` will specify what actions other nodes are supposed to take on it. It defaults to ``broadcast``, which indicates no change from the norm. There are other valid options, but they should normally be left alone, unless you've written a handler (see below) to act on this.

.. code-block:: python

    >>> sock.send('this is', 'a test')

Receiving is a bit simpler. When you call the :py:meth:`~py2p.mesh.mesh_socket.recv` method, you receive a :py:class:`~py2p.base.message` object. This has a number of methods outlined which you can find by clicking its name. Most notably, you can get the packets in a message with :py:attr:`.message.packets`, and reply directly with :py:meth:`.message.reply`.

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

In addition to this, you can register a custom handler for incoming messages. This is appended to the end of the included ones. When writing your handler, you must keep in mind that you are only passed a :py:class:`~py2p.base.message` object and a :py:class:`~py2p.mesh.mesh_connection`. Fortunately you can get access to everything you need from these objects.

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

If this does not take two arguments, :py:meth:`~py2p.base.base_socket.register_handler` will raise a :py:exc:`ValueError`. To help debug these services, you can specify a :py:attr:`~py2p.base.base_socket.debug_level` in the constructor. Using a value of 5, you can see when it enters into each handler, as well as every message which goes in or out.
