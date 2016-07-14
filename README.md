Documentation for individual implementations can be found in their respective folders.

Current build status:

[![Shippable Status for gappleto97/p2p-project](https://img.shields.io/shippable/5750887b2a8192902e225466/master.svg?maxAge=3600&label=Linux)](https://app.shippable.com/projects/5750887b2a8192902e225466) [ ![Travis-CI Status for gappleto97/p2p-project](https://img.shields.io/travis/gappleto97/p2p-project/master.svg?maxAge=3600&label=OSX)](https://travis-ci.org/gappleto97/p2p-project) [ ![Appveyor Status for gappleto97/p2p-project](https://img.shields.io/appveyor/ci/gappleto97/p2p-project/master.svg?maxAge=3600&label=Windows)](https://ci.appveyor.com/project/gappleto97/p2p-project) [ ![Code Climate Score](https://img.shields.io/codeclimate/github/gappleto97/p2p-project.svg?maxAge=3600)](https://codeclimate.com/github/gappleto97/p2p-project) [ ![Codecov Status for gappleto97/p2p-project](https://img.shields.io/codecov/c/github/gappleto97/p2p-project/master.svg?maxAge=3600)](https://codecov.io/gh/gappleto97/p2p-project)

[ ![Issues in Progress](https://img.shields.io/waffle/label/gappleto97/p2p-project/queued.svg?maxAge=3600&labal=queued)](https://waffle.io/gappleto97/p2p-project) [ ![Issues in Progress](https://img.shields.io/waffle/label/gappleto97/p2p-project/in%20progress.svg?maxAge=3600)](https://waffle.io/gappleto97/p2p-project) [ ![Issues in Progress](https://img.shields.io/waffle/label/gappleto97/p2p-project/in%20review.svg?maxAge=3600&label=in%20review)](https://waffle.io/gappleto97/p2p-project)

# Mass Broadcast Protocol

1.  **Abstract**

    This project is meant to be a simple, portable peer-to-peer network, which can be implemented in other languages without much difficulty.

2.  **Problem**
    
    There are very few ways to construct a peer to peer network in dynamic languages. Everyone who does this needs to reinvent the wheel. For example, in Python, the only two such libraries either never made it out of beta, or were to connect to a cryptocurrency. There is certainly no way to communicate *between* these languages.

3.  **Design Goals**

    The network should be unorganized. This means that it's very simple for connections to be added, and for routes to repair themselves in the event of obstruction. It also means that there is no central point of failure, nor overhead to maintaining a structure.

    The network should also be as flexible as possible. It should be able to carry binary data and should have various flags to determine how a message is treated.

    In languages that allow it, network nodes should be able to register custom callbacks, which can respond to incoming data in real time and act upon it as needed.

    Most importantly, nodes should use features that are common across multiple languages.

    And as an afterthought, nodes should be optimized for performance and data density where possible.

4.  **Packet Structure**

    The first step to any of this is being able to understand messages sent through the network. To do this, you need to build a parser. Each message can be considered to have three segments: a header, metadata, and payload. The header is used to figure out the size of a message, as well as how to divide up its various packets. The metadata is used to assist propagation functions. And the payload is what the user on the other end receives.

    A more formal definition would look like:

        Size of message    - 4 (big-endian) bytes defining the size of the message
        ------------------------All below may be compressed------------------------
        Size of packet 0   - 4 bytes defining the plaintext size of packet 0
        Size of packet 1   - 4 bytes defining the plaintext size of packet 1
        ...
        Size of packet n-1 - 4 bytes defining the plaintext size of packet n-1
        Size of packet n   - 4 bytes defining the plaintext size of packet n
        ---------------------------------End Header--------------------------------
        Pathfinding header - [broadcast, waterfall, whisper, renegotiate]
        Sender ID          - A base_58 SHA384-based ID for the sender
        Message ID         - A base_58 SHA384-based ID for the message packets
        Timestamp          - A base_58 unix UTC timestamp of initial broadcast
        Payload packets
          Payload header   - [broadcast, whisper, handshake, peers, request, response]
          Payload contents

    To understand this, let's work from the bottom up. When a user wants to construct a message, they feed a list of packets. For this example, let's say it's `['broadcast', 'test message']`. When this list is fed into a node, it adds the metadata section, and the list becomes:

    `['broadcast', '6VnYj9LjoVLTvU3uPhy4nxm6yv2wEvhaRtGHeV9wwFngWGGqKAzuZ8jK6gFuvq737V', '72tG7phqoAnoeWRKtWoSmseurpCtYg2wHih1y5ZX1AmUvihcH7CPZHThtm9LGvKtj7', '3EfSDb', 'broadcast', 'test message']`.

    The pathfinding header alerts nodes to how they should treat the message. If it is `broadcast` or `waterfall` they are to forward this message to their peers. If it is `whisper` they are not to do so. `renegotiate` is exclusivley used for connection management.

    The sender ID is used to identify a user in your routing table. So if a user wants to reply to a message, they look up this ID in their routing table. As will be discussed below, there are methods you can specifically request a user ID to connect to.

    The message ID is used to filter out messages that a node has seen before. This can also be used as a checksum.

    One thing to notice is that the sender ID, message ID, and timestamp are all in a strange encoding. This is base_58, borrowed from Bitcoin. It's a way to encode numbers that allows for sufficient density while still maintaining some human readability. This will get defined formally later in the paper.

    All of this still leaves out the header. Constructing this goes as follows:

    For each packet, compute its length and pack this into four bytes. So a message of length 6 would look like `'\x00\x00\x00\x06'`. Take the resulting string and prepend it to the packets. In this example, you would end up with: `'\x00\x00\x00\t\x00\x00\x00B\x00\x00\x00B\x00\x00\x00\x06\x00\x00\x00\t\x00\x00\x00\x0cbroadcast6VnYj9LjoVLTvU3uPhy4nxm6yv2wEvhaRtGHeV9wwFngWGGqKAzuZ8jK6gFuvq737V7iSCRDcHZwYtxGbTCz1rwDbUkt7YrbAh2VdS4A75hRuM6xan2gjmZqiVjLkMqiHE3Q3EfSDbbroadcasttest message'`.

    After running this message through whatever compression algorith which has been negotiated with the node's peer, it compute the message's size, and pack this into four bytes: `'\x00\x00\x00\xc0'`. This results in a final message of:

    `'\x00\x00\x00\xc0\x00\x00\x00\t\x00\x00\x00B\x00\x00\x00B\x00\x00\x00\x06\x00\x00\x00\t\x00\x00\x00\x0cbroadcast6VnYj9LjoVLTvU3uPhy4nxm6yv2wEvhaRtGHeV9wwFngWGGqKAzuZ8jK6gFuvq737V7iSCRDcHZwYtxGbTCz1rwDbUkt7YrbAh2VdS4A75hRuM6xan2gjmZqiVjLkMqiHE3Q3EfSDbbroadcasttest message'`

5.  **Parsing a Message**

    Let's keep with our example above. How do we parse the resulting string?

    First, check the first four bytes. Because we don't know how much data to receive through our socket, we always first check for a four byte header. Then we can toss it aside and collect that much information. If we know the message will be compressed, this is when it gets decompressed.

    Next, we need to split up the packets. To do that, take each four bytes and sum their values until the number of remaining bytes equals that sum. If it does not, throw an error. An example script would look like:

    ```python
    def get_packets(string):
        processed = 0
        expected = len(string)
        pack_lens = []
        packets = []
        # First find each packet's length
        while processed != expected:
            length = struct.unpack("!L", string[processed:processed+4])[0]
            processed += 4
            expected -= length
            pack_lens.append(length)
        # Then reconstruct the packets
        for index, length in enumerate(pack_lens):
            start = processed + sum(pack_lens[:index])
            end = start + length
            packets.append(string[start:end])
        return packets
    ```

    From the above script we get back `['broadcast', '6VnYj9LjoVLTvU3uPhy4nxm6yv2wEvhaRtGHeV9wwFngWGGqKAzuZ8jK6gFuvq737V', '72tG7phqoAnoeWRKtWoSmseurpCtYg2wHih1y5ZX1AmUvihcH7CPZHThtm9LGvKtj7', '3EfSDb', 'broadcast', 'test message']`

    A node will use the entirety of this list to decide what to do with it. In this case, it would forward it to its peers, then present to the user the payload: `['broadcast', 'test message']`.

    Now that we know how to construct a message, examples will no longer include the headers. They will include the metadata and payload only.

6.  **IDs and Encoding**

    Knowing the overall message structure is great, but it's not very useful if you can't construct the metadata. To do this, there are three parts.

    *   _base_58_

        This encoding is taken from Bitcoin. If you've ever seen a Bitcoin address, you've seen base\_58 encoding in action. The goal behind it is to provide data compression without compromising its human readability. Base\_58, for the purposes of this protocol, is defined by the following python methods.

        ```python
        base_58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

        def to_base_58(i):
            string = ""
            while i:
                string = base_58[i % 58] + string
                i = i // 58    # Floor division is needed to prevent floats
            return string.encode()

        def from_base_58(string):
            if isinstance(string, bytes):
                string = string.decode()
            decimal = 0
            for char in string:
                decimal = decimal * 58 + base_58.index(char)
            return decimal
        ```

    *   _Node IDs_

        A node ID is taken from a SHA-384 hash of three other elements. First, your outward facing address. Second, the ID of your subnet. Third, a 'user salt' generated on startup. This hash is then converted into base_58.

        That 'subnet ID' we mentioned will be explored in more detail later on, but for now consider it a constant.

    *   _Message IDs_

        A message ID is also a SHA-384 hash. In this case, it is on a message's payload and its timestamp.

        To get the hash, first join each packet together in order. Append to this the message's timestamp in base\_58. The ID you will use is the hash of this string, encoded into base\_58.

7.  **Node Construction**

    Now your node is ready to parse messages on the network, but it can't yet connect. There are important elements it needs to store in order to interact with it correctly.

    1.  A daemon thread which receives messages and incoming connections
    2.  A routing table of peers with the IDs and corresponding connection objects
    3.  A "waterfall queue" of recently received message IDs and timestamps
    4.  A user-interactable queue of recently received messages
    5.  A "protocol", which contains:
        1.  A sub-net flag
        2.  An encryption method (or "Plaintext")
        3.  A way to obtain a SHA256-based ID of this

    That last element is the 'subnet ID' we referred to in section 4. This object is used to weed out undesired connections. If someone has the wrong protocol object, then your node will reject them from connecting. A rough definition would be as follows:

    ```python
    class protocol(namedtuple("protocol", ['subnet', 'encryption'])):
        @property
        def id(self):
            info = [str(x) for x in self] + [protocol_version]
            h = hashlib.sha256(''.join(info).encode())
            return to_base_58(int(h.hexdigest(), 16))
    ```

    Or more explicitly in javascript:

    ```javascript
    class protocol {
        constructor(subnet, encryption) {
            this.subnet = subnet;
            this.encryption = encryption;
        }

        get id() {
            var info = [this.subnet, this.encryption, protocol_version];
            var hash = SHA256(info.join(''));
            return to_base_58(BigInt(hash, 16));
        }
    }
    ```

8.  **Connecting to the Network**

    This is where the protocol object becomes important.

    When you connect to a node, each will send a message in the following format:

        whisper
        [your id]
        [message id]
        [timestamp]
        handshake
        [your id]
        [your protocol id]
        [your outward-facing address]
        [json-ized list of supported compression methods, in order of preference]

    When your node receives the corresponding message, the first thing your node does is compare their protocol ID against your own. If they do not match, your node shuts down the connection.

    If they do match, your node adds them to your routing table (`{ID: connection}`), and makes a note of their outward facing address and supported compression methods. Then your node sends a standard response:

        whisper
        [your id]
        [message id]
        [timestamp]
        peers
        [json-ized copy of your routing table in format: [[addr, port], id]]

    Upon receiving this message, your node attempts to connect to each given address. Now you're connected to the network! But how do you process the incoming messages?

9.  **Message Propagation**

    A message is initially broadcast with the `broadcast` flag. The broadcasting node, as well as all receivers, store this message's ID and timestamp in their waterfall queue. The reciving nodes then re-broadcast this message to each of their peers, but changing the flag to `waterfall`.

    A node which receives these waterfall packets goes through the following steps:

    1.  If the message ID is not in the node's waterfall queue, continue and add it to the waterfall queue
    2.  Perform cleanup on the waterfall queue
        1.  Remove all possible duplicates (sending may be done in multiple threads, which may result in duplicate copies)
        2.  Remove all IDs with a timestamp more than 1 minute ago
    3.  Re-broadcast this message to all peers (optionally excluding the one you received it from)

    ![Figure one](./figure_one.png)

10. **Renegotiating a Connection**

    It may be that at some point a message fails to decompress on your end. If this occurs, you have an easy solution, your node can send a `renegotiate` message. This flag is used to indicate that a message should never be presented to the user, and is only used for connection management. At this time there are two possible operations.

    The `compression` subflag will allow your node to renegotiate your compression methods. A message using this subflag should be constructed like so:

        renegotiate
        [your id]
        [message id]
        [timestamp]
        compression
        [json-ized list of desired compression methods, in order of preference]

    Your peer will respond with the same message, excluding any methods they do not support. If this list is different than the one you sent, you reply, trimming the list of methods *your node* does not support. This process is repeated until the two agree upon a list.

    Your node may also send a `resend` subflag, which requests your peer to resend the previous `whisper` or `broadcast`. This is structured like so:

        renegotiate
        [your id]
        [message id]
        [timestamp]
        resend

11. **Peer Requests**

    If you want to privately reply to a message where you are not directly connected to a sender, the following method can be used:

    First, your node broadcasts a message to the network containing the `request` subflag. This is constructed as follows:

        broadcast
        [your id]
        [message id]
        [timestamp]
        request
        [a unique, base_58 id you assign]
        [the id of the desired peer]

    Then your node places this in a dictionary so your node can watch for when this is responded to. A peer who gets this will reply:

        broadcast
        [their id]
        [message id]
        [timestamp]
        response
        [the id you assigned]
        [address of desired peer in format: [[addr, port], id] ]

    When this is received, your node removes the request from your dictionary, makes a connection to the given address, and sends the message.

    Another use of this mechanism is to request a copy of your peers' routing tables. To do this, your node may send a message structured like so:

        whisper
        [your id]
        [message id]
        [timestamp]
        request
        *

    A node who receives this will respond exactly as they do after a successful handshake. Note that while it is technically valid to send this request as a `broadcast`, it is generally discouraged.

12.  **Potential Flaws**

    The network has a few immediately obvious shortcomings.

    First, the maximum message size is 4,294,967,299 bytes (including compression and headers). It could well be that in the future there will be more data to send in a single message. But equally so, a present-day attacker could use this to halt essentially every connection on the network. A short-term solution would be to have a soft-defined limit, but as has been shown in other protocols, this can calcify over time and do damage.

    Second, in a worst case scenario, every node will receive a given message n-1 times, and each message will generate n<sup>2</sup> total broadcasts, where n is the number of connected nodes. In most larger cases this will not happen, as a given node will not be connected to everyone else. But in smaller networks this will be common, and in well-connected networks this could slow things down. This calls for optimization, and will need to be explored. For instance, not propagating to a peer you receive a message from reduces the number of total broadcasts to (n-1)<sup>2</sup>. Limiting your number of connections can bring this down to min(max_conns, n-1) * (n-1).

    Thrid, there is quite a lot of extra data being sent. Using the default parameters, if you want to send a 4 character message it will be expanded to 159 characters. That's ~42x larger. If you want these differences to be negligble, you need to send messages on the order of 512 characters. Then there is only an increase of ~34% (0% with decent compression). This can be improved by reducing the size of the various IDs being sent, or making the packet headers shorter. Both of these have disadvantages, however.

    Results using opportunistic compression look roughly as follows (last updated in 0.4.231):

    For 4 characters…

        original  4
        plaintext 167  (4175%)
        lzma      220  (5500%)
        bz2       189  (4725%)
        gzip      156  (3900%)

    For 512 characters…

        original  512
        plaintext 677  (132.2%)
        lzma      568  (110.9%)
        bz2       555  (108.4%)
        gzip      487  (95.1%)

    Because the reference implementation supports all of these (excepting environment variations), this means that the overhead will drop away after ~500 characters. Communications with other implementations may be slower than this, however.
