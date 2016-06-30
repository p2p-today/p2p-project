`Skip to file-wise API <#file-wise-api>`__

Public API
==========

Constants
---------

-  ``__version__``: A string containing the major, minor, and patch
   release number.
-  ``version_info``: A ``tuple`` version of the above
-  ``protocol_version``: A string containing the major and minor release
   number. This refers to the underlying protocol
-  ``node_policy_version``: A string containing the build number
   associated with this version. This refers to the node and its
   policies.

Classes
-------

-  `mesh_socket <#mesh_socket>`__

File-wise API
=============

base.py
=======

This is used mostly for inheriting common functions with
`mesh.py <#meshpy>`__ and the planned `chord.py <#chordpy>`__

Constants
---------

-  ``version``: A string containing the major, minor, and patch release
   number. This version refers to the underlying protocol.
-  ``protocol_version``: A string containing the major and minor release
   number. This refers to the underlying protocol
-  ``node_policy_version``: A string containing the build number
   associated with this version. This refers to the node and its
   policies.
-  ``user_salt``: A ``uuid4`` which is generated uniquely in each
   running instance
-  ``compression``: A ``list`` of the compression methods your instance
   supports
-  ``default_protocol``: The default `protocol <#protocol>`__
   definition. This uses an empty string as the subnet and
   ``SSL`` encryption, as supplied by `ssl_wrapper.py <#ssl_wrapperpy>`__ (in
   alpha releases this will use ``Plaintext``)
-  ``base_58``: The characterspace of base\_58, ordered from least to
   greatest value

Methods
-------

-  ``to_base_58(i)``: Takes an ``int`` (or ``long``) and returns its
   corresponding base\_58 string (type: ``bytes``)
-  ``from_base_58(string)``: Takes a base\_58 string (or ``bytes``) and
   returns its corresponding integer (type: ``int``, ``long``)
-  ``getUTC()``: Returns the current unix time in UTC (type: ``int``)
-  ``compress(msg, method)``: Shortcut method for compression (type:
   ``bytes``)
-  ``decompress(msg, method)``: Shortcut method for decompression (type:
   ``bytes``)
-  ``get_lan_ip()``: Returns either your current local IP, or
   ``"127.0.0.1"``

Classes
-------

flags
~~~~~

This class is used as a namespace to store the various protocol defined
flags.

-  ``broadcast``
-  ``bz2``
-  ``compression``
-  ``gzip``
-  ``handshake``
-  ``lzma``
-  ``peers``
-  ``waterfall``
-  ``resend``
-  ``response``
-  ``renegotiate``
-  ``request``
-  ``whisper``

pathfinding\_message
~~~~~~~~~~~~~~~~~~~~

This class is used internally to deal with packet parsing from a socket
level. If you find yourself calling this as a user, something's gone
wrong.

Constructor
^^^^^^^^^^^

``pathfinding_message(protocol, msg_type, sender, payload, compressions=None)``
``pathfinding_message.feed_string(protocol, string, sizeless=False, compressions=None)``

-  ``protocol``: The `protocol <#protocol>`__ this message uses
-  ``msg_type``: The chief `flag <#flags>`__ this message uses, to
   broadcast intent
-  ``sender``: The SHA384-based sender ID
-  ``payload``: A ``list`` of additional packets to send
-  ``compressions``: A ``list`` of possible compression methods used/to
   use
-  ``string``: The raw message to parse
-  ``sizeless``: An indicator as to whether this message contains the
   length header

Constants
^^^^^^^^^

-  ``protocol``: The protocol this message is sent under
-  ``msg_type``: The main `flag <#flags>`__ of the message (ie:
   ``['broadcast', 'waterfall', 'whisper', 'renegotiate']``)
-  ``sender``: The sender id of this message
-  ``time``: An ``int`` of the message's timestamp
-  ``compression``: The ``list`` of compression methods this message may
   be under
-  ``compression_fail``: A debug property which is triggered if you give
   compression methods, but the message fed from ``feed_string`` is
   actually in plaintext

Properties
^^^^^^^^^^

-  ``payload``: Returns the message's payload
-  ``compression_used``: Returns the compression method used
-  ``time_58``: Returns the timestamp in base\_58
-  ``id``: Returns the message's id
-  ``len``: Returns the messages length header
-  ``packets``: Returns a ``list`` of the packets in this message,
   excluding the length header
-  ``string``: Returns a string version of the message, including the
   length header
-  ``__non_len_string``: Returns the string of this message without the
   size header

Methods
^^^^^^^

-  ``__len__()``: Returns the length of this message excluding the
   length header

Class Methods
^^^^^^^^^^^^^

-  ``feed_string(ptorocol, string, sizeless=False, compressions=None)``:
   Given a `protocol <#protocol>`__, a string or ``bytes``, process
   this into a ``pathfinding_message``. If compressions are enabled, you
   must provide a ``list`` of possible methods. If the size header is
   not included, you must specify this with ``sizeless=True``. Possible
   errors:

   -  ``AttributeError``: Fed a non-string, non-\ ``bytes`` argument
   -  ``AssertionError``: Initial size header is incorrect
   -  ``Exception``: Unrecognized compression method fed in
      ``compressions``
   -  ``struct.error``: Packet headers are incorrect OR unrecognized
      compression
   -  ``IndexError``: See ``struct.error``

-  ``sanitize_string(string, sizeless=False)``: Given an ``str`` or
   ``bytes``, returns a ``bytes`` object with no size header. Possible
   errors:

   -  ``AttributeError``: Fed a non-string, non-\ ``bytes`` argument
   -  ``AssertionError``: Initial size header is incorrect

-  ``decompress_string(string, compressions=None)``: Given a ``bytes``
   object and list of possible compression methods, returns a
   decompressed version and a ``bool`` indicating if decompression
   failed. If decompression occurs, this will always return ``bytes``.
   If not, it will return whatever you pass in. Decompression failure is
   defined as it being unable to decompress despite a list of possible
   methods being provided. Possible errors:

   -  ``Exception``: Unrecognized compression method fed in
      ``compressions``

-  ``process_string(string)``: Given a ``bytes``, return a ``list`` of
   its contained packets. Possible errors:

   -  ``IndexError``: Packet headers are incorrect OR not fed plaintext
   -  ``struct.error``: See ``IndexError`` OR fed non-\ ``bytes`` object

message
~~~~~~~

This class is returned to the user when a non-automated message is
received. It contains sufficient information to parse a message or reply
to it.

Constructor
^^^^^^^^^^^

``message(msg, server)``

-  ``msg``: This contains the
   `pathfinding_message <#pathfinding_message>`__ you received
-  ``server``: The `base_socket <#base_socket>`__ which received the
   message

Constants
^^^^^^^^^

-  ``msg``: This contains the
   `pathfinding_message <#pathfinding_message>`__ you received
-  ``server``: The `base_socket <#base_socket>`__ which received the
   message

Properties
^^^^^^^^^^

-  ``time``: The UTC Unix time at which the message was sent
-  ``sender``: The original sender's ID
-  ``protocol``: The `protocol <#protocol>`__ you received this
   under
-  ``packets``: Returns a ``list`` of the packets received, with the
   first item being the subflag
-  ``id``: Returns the SHA384-based message id

Methods
^^^^^^^

-  ``reply(*args)``: Sends a `whisper <#flags>`__ to the original
   sender with the arguments being each packet after that. If you are
   not connected, it uses the `request/response <#flags>`__
   mechanism to try making a connection

protocol
~~~~~~~~

This class inherits most of its methods from a ``namedtuple``. This
means that each of the properties in the constructor can be accessed by
name or index. Mostly you'll be doing this by name.

Constructor
^^^^^^^^^^^

``protocol(subnet, encryption)``

Constants
^^^^^^^^^

-  ``subnet``: A flag to allow people with the same package version to
   operate different networks
-  ``encryption``: Defines the encryption standard used on the socket

Properties
^^^^^^^^^^

-  ``id``: Returns the SHA256-based protocol id

base\_socket
~~~~~~~~~~~~

Variables
^^^^^^^^^

-  ``debug_level``: The verbosity of the socket with debug prints
-  ``routing_table``: The current ``dict`` of peers in format
   ``{id: connection}``
-  ``awaiting_ids``: A ``list`` of connections awaiting a handshake
-  ``queue``: A ``deque`` of recently received
   `message <#message>`__\ s
-  ``daemon``: This node's `base_daemon <#base_daemon>`__ object

Properties
^^^^^^^^^^

-  ``outgoing``: A ``list`` of ids for outgoing connections
-  ``incoming``: A ``list`` of ids for incoming connections
-  ``status``: Returns ``"Nominal"`` or
   ``base_socket.daemon.exceptions`` if there are ``Exceptions``
   collected

Methods
^^^^^^^

-  ``recv(quantity=1)``: Receive `message <#message>`__\ s; If
   ``quantity != 1``, returns a ``list`` of
   `message <#message>`__\ s, otherwise returns one
-  ``__print__(*args, level=None)``: Prints debug information if
   ``level >= debug_level``

base\_daemon
~~~~~~~~~~~~

Constructor
^^^^^^^^^^^

``base_daemon(addr, port, server, prot=default_protocol)``

-  ``addr``: The address it should bind its incoming connection to
-  ``port``: The port it should bind its incoming connection to
-  ``server``: This daemon's `base_socket <#base_socket>`__
-  ``prot``: This daemon's `protocol <#protocol>`__

Variables
^^^^^^^^^

-  ``protocol``: This daemon's `protocol <#protocol>`__ object
-  ``server``: A pointer to this daemon's
   `base_socket <#base_socket>`__
-  ``sock``: This daemon's ``socket`` object
-  ``alive``: A checker to shutdown the daemon. If ``False``, its thread
   will stop running eventually.
-  ``exceptions``: A ``list`` of unhandled ``Exception``\ s raised in
   ``mainloop``
-  ``daemon``: A ``Thread`` which runs through ``mainloop``

Methods
^^^^^^^

-  ``__print__(*args, level=None)``: Prints debug information if
   ``level >= server.debug_level``

base\_connection
~~~~~~~~~~~~~~~~

Constructor
^^^^^^^^^^^

``base_connection(sock, server, prot=default_protocol, outgoing=False)``

-  ``sock``: A ``socket.socket``
-  ``server``: This node's `base_socket <#base_socket>`__
-  ``prot``: This node's `protocol <#protocol>`__
-  ``outgoing``: Whether or not this node is an outgoing connection

Variables
^^^^^^^^^

-  ``sock``: This connection's ``socket`` object
-  ``server``: A pointer to this connection's
   `base_socket <#base_socket>`__ object
-  ``protocol``: This connection's `protocol <#protocol>`__ object
-  ``outgoing``: A ``bool`` that states whether this connection is
   outgoing
-  ``buffer``: A ``list`` of recently received characters
-  ``id``: This node's SHA384-based id
-  ``time``: The time at which this node last received data
-  ``addr``: This node's outward-facing address
-  ``compression``: A ``list`` of this node's supported compression
   methods
-  ``last_sent``: A copy of the most recently sent ``whisper`` or
   ``broadcast``
-  ``expected``: The number of bytes expected in the next message
-  ``active``: A ``bool`` which says whether the next message is a size
   header, or a message (``True`` if message)

Methods
^^^^^^^

-  ``fileno()``: Returns ``sock``'s file number
-  ``collect_incoming_data(data)``: Adds new data to the buffer
-  ``find_terminator()``: Determines if a message has been fully
   received (name is a relic of when this had an ``end_of_tx`` flag)
-  ``__print__(*args, level=None)``: Prints debug information if
   ``level >= server.debug_level``

mesh.py
=======

Note: This inherits a *lot* from `base.py <#basepy>`__, and imported
values will *not* be listed here, for brevity's sake.

Constants
---------

-  ``compression``: A ``list`` of the compression methods your instance
   supports
-  ``max_outgoing``: The (rough) maximum number of outgoing connections
   your node will maintain
-  ``default_protocol``: The default `protocol <#protocol>`__ definition. This uses ``'mesh'`` as the subnet and
   ``SSL`` encryption, as supplied by `ssl\_wrapper.py <#ssl\_wrapperpy>`__ (in
   alpha releases this will use ``Plaintext``)

Classes
-------

mesh\_socket
~~~~~~~~~~~~

This peer-to-peer socket is the main purpose behind this library. It
maintains a connection to a mesh network. Details on how it works
specifically are outlined `here <../README.md>`__, but the basics are
outlined below.

It also inherits all the attributes of
`base_socket <#base_socket>`__, though they are also outlined here

Constructor
^^^^^^^^^^^

``mesh_socket(addr, port, prot=default_protocol, out_addr=None, debug_level=0)``

-  ``addr``: The address you'd like to bind to
-  ``port``: The port you'd like to bind to
-  ``prot``: The `protocol <#protocol>`__ you'd like to use
-  ``out_addr``: Your outward-facing address, if that is different from
   ``(addr, port)``
-  ``debug_level``: The verbosity at which this and its associated
   `mesh_daemon <#mesh_daemon>`__ prints debug information

Variables
^^^^^^^^^

-  ``protocol``: A `protocol <#protocol>`__ object which contains
   the subnet flag and the encryption method
-  ``debug_level``: The verbosity of the socket with debug prints
-  ``routing_table``: The current ``dict`` of peers in format
   ``{id: connection}``
-  ``awaiting_ids``: A ``list`` of connections awaiting a handshake
-  ``outgoing``: A ``list`` of ids for outgoing connections
-  ``incoming``: A ``list`` of ids for incoming connections
-  ``requests``: A ``dict`` of the requests this node has made in format
   ``{request_id: delayed_message_contents}``
-  ``waterfalls``: A ``deque`` of metadata for recently received
   `message <#message>`__\ s
-  ``queue``: A ``deque`` of recently received
   `message <#message>`__\ s
-  ``out_addr``: A ``tuple`` which contains the outward facing address
   and port
-  ``id``: This node's SHA384-based id
-  ``daemon``: This node's `mesh_daemon <#mesh_daemon>`__ object

Methods
^^^^^^^

-  ``connect(addr, port, id=None)``: Connect to another ``mesh_socket``
   (and assigns id if specified)
-  ``send(*args, type='broadcast')``: Send a message to your peers with
   each argument as a packet
-  ``recv(quantity=1)``: Receive `message <#message>`__\ s; If
   ``quantity != 1``, returns a ``list`` of
   `message <#message>`__\ s, otherwise returns one
-  ``handle_request(msg)``: Allows the daemon to parse subflag-level
   actions
-  ``waterfall(msg)``: Waterfalls a `message <#message>`__ to your
   peers

mesh\_daemon
~~~~~~~~~~~~

This inherits all the attributes of `base_daemon <#base_daemon>`__,
though they are also outlined here

Constructor
^^^^^^^^^^^

``mesh_daemon(addr, port, server, prot=default_protocol)``

-  ``addr``: The address it should bind its incoming connection to
-  ``port``: The port it should bind its incoming connection to
-  ``server``: This daemon's `mesh_socket <#mesh_socket>`__
-  ``prot``: This daemon's `protocol <#protocol>`__

Variables
^^^^^^^^^

-  ``protocol``: This daemon's `protocol <#protocol>`__ object
-  ``server``: A pointer to this daemon's
   `mesh_socket <#mesh_socket>`__
-  ``sock``: This daemon's ``socket`` object
-  ``alive``: A checker to shutdown the daemon. If ``False``, its thread
   will stop running eventually.
-  ``exceptions``: A ``list`` of unhandled ``Exception``\ s raised in
   ``mainloop``
-  ``daemon``: A ``Thread`` which runs through ``mainloop``

Methods
^^^^^^^

-  ``mainloop()``: The method through which ``daemon`` parses. This runs
   as long as ``alive`` is ``True``, and alternately calls the
   ``collect_incoming_data`` methods of
   `mesh_connection <#mesh_connection>`__\ s and ``handle_accept``.
-  ``handle_accept()``: Deals with incoming connections
-  ``disconnect(handler)``: Closes a given
   `mesh_connection <#mesh_connection>`__ and removes its
   information from ``server``
-  ``__print__(*args, level=None)``: Prints debug information if
   ``level >= server.debug_level``

mesh\_connection
~~~~~~~~~~~~~~~~

This inherits all the attributes of
`base_connection <#base_connection>`__, though they are also
outlined here

Constructor
^^^^^^^^^^^

``base_connection(sock, server, prot=default_protocol, outgoing=False)``

-  ``sock``: A ``socket.socket``
-  ``server``: This node's `mesh_socket <#mesh_socket>`__
-  ``prot``: This node's `protocol <#protocol>`__
-  ``outgoing``: Whether or not this node is an outgoing connection

Variables
^^^^^^^^^

-  ``sock``: This connection's ``socket`` object
-  ``server``: A pointer to this connection's
   `mesh_socket <#mesh_socket>`__ object
-  ``protocol``: This connection's `protocol <#protocol>`__ object
-  ``outgoing``: A ``bool`` that states whether this connection is
   outgoing
-  ``buffer``: A ``list`` of recently received characters
-  ``id``: This node's SHA384-based id
-  ``time``: The time at which this node last received data
-  ``addr``: This node's outward-facing address
-  ``compression``: A ``list`` of this node's supported compression
   methods
-  ``last_sent``: A copy of the most recently sent
   `whisper <#flags>`__ or `broadcast <#flags>`__
-  ``expected``: The number of bytes expected in the next message
-  ``active``: A ``bool`` which says whether the next message is a size
   header, or a message (``True`` if message)

Methods
^^^^^^^

-  ``fileno()``: Returns ``sock``'s file number
-  ``collect_incoming_data(data)``: Adds new data to the buffer
-  ``find_terminator()``: Determines if a message has been fully
   received (name is a relic of when this had an ``end_of_tx`` flag)
-  ``found_terminator()``: Deals with any data received when
   ``find_terminator`` returns ``True``
-  ``send(msg_type, *args, id=server.id, time=base.getUTC())``: Sends a
   message via ``sock``
-  ``__print__(*args, level=None)``: Prints debug information if
   ``level >= server.debug_level``

net.py
======

Deprecated. Set to be removed in next release.

ssl\_wrapper.py
==============

Variables
---------

-  ``cleanup_files``: Only present in python2; A list of files to clean up using the ``atexit`` module. Because of this setup, sudden crashes of Python will not clean up keys or certs.

Methods
-------

-  ``generate_self_signed_cert(cert_file, key_file)``: Given two file-like objects, generate an SSL certificate and key file
-  ``get_socket(server_side)``: Returns an ``ssl.SSLSocket`` for use in other parts of this library
-  ``cleanup()``: Only present in python2; Calls ``os.remove`` on all files in ``cleanup_files``.