# p2p.py

### Constants

---------

* `version`: The protocol version your socket will use
* `user_salt`: A `uuid4` which is generated uniquely in each running instance
* `compression`: A `list` of the compression methods your instance supports
* `sep_sequence`: A string which contains the default packet separator
* `max_outgoing`: The (rough) maximum number of outgoing connections your node will maintain
* `default_protocol`: The default `protocol` definition. This uses `sep_sequence` as the packet separator, an empty string as the subnet, and `PKCS1_v1.5` encryption, as supplied by `net.py`
* `base_58`: The characterspace of base_58, ordered from least to greatest value

### Methods

---------

* `to_base_58(i)`: Takes an `int` and returns its corresponding base_58 string (type: `str`)
* `from_base_58(string)`: Takes a base_58 string and returns its corresponding integer (type: `int`)
* `getUTC()`: Returns the current unix time in UTC (type: `int`)
* `compress(msg, method)`: Shortcut method for compression (type: `str`/`bytes`)
* `decompress(msg, method)`: Shortcut method for decompression (type: `str`/`bytes`)

### pathfinding_message

--------

This class is used internally to deal with packet parsing from a socket level. If you find yourself calling this as a user, something's gone wrong.

`pathfinding_message(protocol, msg_type, sender, payload, compression=None)`
`pathfinding_message.feed_string(protocol, string, sizeless=False, compressions=None)`

Constants:

* `protocol`: The protocol this message is sent under
* `msg_type`: The main flag of the message (ie: ['broadcast', 'waterfall', 'whisper', 'renegotiate'])
* `sender`: The sender id of this message
* `time`: An `int` of the message's timestamp
* `compression`: The list of compression methods this message may be under
* `compression_fail`: A debug property which is triggered if you give compression methods, but the message fed from `feed_string` is actually in plaintext

Public properties:

* `payload`: Returns the message's payload
* `compression_used`: Returns the compression method used
* `time_58`: Returns the timestamp in base_58
* `id`: Returns the message's id
* `len`: Returns the messages length header
* `packets`: Returns a `list` of the packets in this message, excluding the length header
* `string`: Returns a string version of the message, including the length header

Private properties:

* `__non_len_string`: Returns the string of this message without the size header

Methods:

* `__len__()`: Returns the length of this message excluding the length header

### message

---------

This class inherits most of its methods from a `namedtuple`. This means that each of the properties in the constructor can be accessed by name or index. Mostly you'll be doing this by name.

`message(msg, sender, protocol, time, server)`

Constants:

* `msg`: This contains the raw message string you received
* `sender`: This is either a `p2p_connection` to the original sender, or their id
* `protocol`: This `protocol` object contains the relevant metadata to parse `msg`
* `time`: A UTC unix timestamp of the original broadcast
* `server`: The `p2p_socket` which received the message

Properties:

* `packets`: Returns a `list` of the packets received, with the first item being the subflag
* `id`: Returns the SHA384-based message id

Methods:
* `reply(*args)`: Sends a `whisper` to the original sender with the arguments being each packet after that. If you are not connected, it uses the `request`/`response` mechanism to try making a connection

### protocol

---------

This class inherits most of its methods from a `namedtuple`. This means that each of the properties in the constructor can be accessed by name or index. Mostly you'll be doing this by name.

`protocol(sep, subnet, encryption)`

Constants:

* `sep`: This contains the packet separator flag
* `subnet`: A mostly-unused flag to allow people with the same separator to operate different networks
* `encryption`: Defines the encryption standard used on the socket

Properties:

* `id`: Returns the SHA256-based protocol id

### p2p_socket

---------

Variables:

* `protocol`: A `protocol` object which contains the packet separator, the subnet flag, and the encryption method
* `debug_level`: The verbosity of the socket with debug prints
* `routing_table`: The current `dict` of peers in format {id: connection}
* `awaiting_ids`: A `list` of connections awaiting a handshake
* `outgoing`: A `list` of ids for outgoing connections
* `incoming`: A `list` of ids for incoming connections
* `requests`: A `dict` of the requests this node has made in format {request_id: delayed_message_contents}
* `waterfalls`: A `deque` of metadata for recently received messages
* `queue`: A `deque` of recently received `message`s
* `out_addr`: A `tuple` which contains the outward facing address
* `id`: This node's SHA384-based id
* `daemon`: This node's `p2p_daemon` object

Public methods:

* `connect(addr, port, id=None)`: Connect to another `p2p_socket` (and assigns id if specified)
* `send(*args, type='broadcast'): Send a message to your peers with each argument as a packet
* `recv(quantity=1)`: Receive `message`s; If `quantity != 1`, returns a `list` of `message`s, otherwise returns one

Private methods:

* `handle_request(msg)`: Allows the daemon to parse subflag-level actions
* `waterfall(msg)`: Waterfalls a `message` to your peers
* `debug(level=1)`: Determines whether a debug message should be printed

### p2p_daemon

---------

Variables:

* `protocol`: This daemon's `protocol` object
* `server`: A pointer to this daemon's `p2p_socket`
* `sock`: This daemon's `socket` object
* `exceptions`: A `list` of unhandled `Exception`s raised in `mainloop`
* `daemon`: A `thread` which runs through `mainloop`

Private methods:

* `mainloop()`: Receives data from all ready `socket`s, acts on this data, then receives incoming connections
* `handle_accept()`: Receives any incoming connections
* `disconnect(handler)`: Removes a handler from all of the `p2p_socket`'s databases
* `debug(level=1)`: Determines whether a debug message should be printed

### p2p_connection

---------

Variables:

* `sock`: This connection's `socket` object
* `server`: A pointer to this connection's `p2p_socket` object
* `protocol`: This connection's `protocol` object
* `outgoing`: A `bool` that states whether this connection is outgoing
* `buffer`: A `list` of recently received characters
* `id`: This node's SHA384-based id
* `time`: The time at which this node last received data
* `addr`: This node's outward-facing address
* `compression`: A `list` of this node's supported compression methods
* `last_sent`: A copy of the most recently sent `whisper` or `broadcast`
* `expected`: The number of bytes expected in the next message
* `active`: A `bool` which says whether the next message is a size header, or a message (`True` if message)

Public methods:

* `send(msg_type, *args, id=self.server.id, time=to_base_58(getUTC()))`: Sends a message to the peer, with each argumet as a packet and `msg_type` as the routing flag
* `fileno()`: Returns `sock`'s file number

Private methods:

* `collect_incoming_data(data)`: Adds new data to the buffer
* `find_terminator()`: Determines if a message has been fully received (name is a relic of when this had an end_of_tx flag)
* `found_terminator()`: Ran when a message has been fully received (name is a relic of when this had an end_of_tx flag)
* `debug(level=1)`: Determines whether a debug message should be printed

# rsa.py

### Constants

---------

* `uses_RSA`: Defines whether you're using the `rsa` module
* `decryption_error`: The `Exception` this module catches when decryption fails
* `key_request`: The message used to request a peer's key
* `size_request`: The message used to request a peer's keysize
* `end_of_message`: The flag used to denote the end of a message
* `hashtable`: (only used with PyCrypto) A `dict` containing the various hash methods used

### Methods

---------

* `newkeys(size)`: Wrapper for the relevant crypto library which returns a public and private key of the specified size
* `encrypt(msg, key)`: Returns an encrypted copy of the specified message
* `decrypt(msg, key)`: Decrypts the given ciphertext
* `sign(msg, key, hashop)`: Returns a signature given a message and hashop
* `verify(msg, sig, key)`: Verifies a signature
* `PublicKey(n, e)`: Returns a public key object

### secureSocket

---------

This class inherits most of its methods from a `socket.socket`. This means that the methods should work *roughly* the same way, with a few differences. The `suppress_warnings` flag will allow you to make keys outside of `range(354, 8193)`. Note that if you're using PyCrypto, it will not let you build if `keysize % 256 != 0 or keysize < 1024`.

`secureSocket(sock_family=socket.AF_INET, sock_type=socket.SOCK_STREAM, proto=0, fileno=None, keysize=1024, suppress_warnings=False)`

Constants:

* `pub`: The `socket`'s public key
* `priv`: The `socket`'s private key
* `key_async`: A temporary `thread` which generates the `socket`'s key
* `keysize`: The `socket`'s key size
* 'msgsize`: The maximum packet size you can encrypt
* `key`: Your peer's key
* `peer_keysize`: Your peer's key size
* `peer_msgsize`: Your peer's maximum packet size
* `buffer`: Temporary storage for if you request a specific number of characters
* `key_exchange`: A temporary `thread` which deals with the handshake

Public methods:

* `connect(ip)`: Attempts to connect to the given address
* `bind(ip)`: Binds to the given ip address (inherited from `socket.socket`)
* `listen(i)`: Allow the given number of incoming connections to queue
* `accept()`: Returns a connection and address
* `close()`: Closes the connection
* `dup()`: Returns a copy of the `socket`
* `settimeout(i)`: Sets the `socket` timeout; blocks if a handshake is occurring
* `send(msg)`: Sends an encrypted message, with an encrypted signature; blocks if a handshake is occurring
* `recv(size=None)`: Receives a message. If a size is given, returns that number of characters. Blocks if no message is available, or `raise`s `socket.timeout` if not received within the assigned timeout; blocks completely if a handshake is occurring
* `sign(msg, hashop='best')`: Returns a signature of the given text; If you define a hashop, it will use that. Otherwise it uses the largest available. Valid ops are `['SHA-512', 'SHA-384', 'SHA-256', 'SHA-1', 'MD5']`
* `verify(msg, sig, key=None)`: Returns whether the signature is valid. If a key is not specified, defaults to its own key

Private methods:

* `__recv(size)`: `socket.socket`'s `recv` method
* `__send__(msg)`: Sends an encrypted copy of the given text
* `__recv__()`: Receives and decrypts a message
* `requestKey()`: Request side of a handshake
* `sendKey()`: Send side of a handshake
* `handshake(order)`: Exchanges keys with your peer; If order evaluates to `True`, it sends the key first
* `mapKey()`: If your keys are undefined, grabs them from `key_async`
