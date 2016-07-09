from __future__ import print_function
import hashlib, inspect, json, random, select, socket, struct, sys, traceback
from .base import flags, compression, to_base_58, from_base_58, getUTC, \
                intersect, protocol, get_socket, base_connection, message, \
                base_daemon, base_socket, pathfinding_message, json_compressions

default_protocol = protocol('chord', "Plaintext")  # SSL")
k = 160  # SHA-1 namespace
limit = 2**k
hashes = ['sha1', 'sha224', 'sha256', 'sha384', 'sha512']

if sys.version_info >= (3,):
    xrange = range

def distance(a, b):
    """This is a clockwise ring distance function.
    It depends on a globally defined k, the key size.
    The largest possible node id is 2**k (or limit)."""
    if a == b:
        return 0
    elif a < b:
        return b - a
    else:
        return limit + b - a

def most_common(lst):
    """Returns the most common element in a list"""
    return max(set(lst), key=lst.count)

class chord_connection(base_connection):
    def send(self, msg_type, *args, **kargs):
        """Sends a message through its connection. The first argument is message type. All after that are content packets"""
        # This section handles waterfall-specific flags
        id = kargs.get('id', self.server.id)  # Latter is returned if key not found
        time = kargs.get('time', getUTC())
        # Begin real method
        msg = pathfinding_message(self.protocol, msg_type, id, list(args), self.compression)
        if msg_type in [flags.whisper, flags.broadcast]:
            self.last_sent = [msg_type] + list(args)
        self.__print__("Sending %s to %s" % ([msg.len] + msg.packets, self), level=4)
        if msg.compression_used: self.__print__("Compressing with %s" % msg.compression_used, level=4)
        try:
            self.sock.send(msg.string)
        except (IOError, socket.error) as e:
            self.server.daemon.exceptions.append((e, traceback.format_exc()))
            self.server.disconnect(self)

    def found_terminator(self):
        try:
            msg = super(chord_connection, self).found_terminator()
        except (IndexError, struct.error):
            self.__print__("Failed to decode message: %s. Expected compression: %s." % \
                            (raw_msg, intersect(compression, self.compression)[0]), level=1)
            self.send(flags.renegotiate, flags.compression, json.dumps([]))
            self.send(flags.renegotiate, flags.resend)
            return
        packets = msg.packets
        self.__print__("Message received: %s" % packets, level=1)
        if self.handle_renegotiate(packets):
            return
        self.server.handle_msg(message(msg, self.server), self)

    @property
    def id_10(self):
        return from_base_58(self.id)

class chord_daemon(base_daemon): 
    def mainloop(self):
        while self.alive:
            conns = list(self.server.routing_table.values()) + self.server.awaiting_ids
            if conns:
                for handler in select.select(conns, [], [], 0.01)[0]:
                    self.process_data(handler)
                for handler in conns:
                    self.kill_old_nodes(handler)
            self.handle_accept()

    def handle_accept(self):
        """Handle an incoming connection"""
        if sys.version_info >= (3, 3):
            exceptions = (socket.error, ConnectionError)
        else:
            exceptions = (socket.error, )
        try:
            conn, addr = self.sock.accept()
            self.__print__('Incoming connection from %s' % repr(addr), level=1)
            handler = chord_connection(conn, self.server)
            handler.send(flags.whisper, flags.handshake, self.server.id, self.protocol.id, \
                            json.dumps(self.server.out_addr), json_compressions)
            handler.sock.settimeout(1)
            self.server.awaiting_ids.append(handler)
        except exceptions:
            pass

    def process_data(self, handler):
        """Collects incoming data from nodes"""
        try:
            while not handler.find_terminator():
                if not handler.collect_incoming_data(handler.sock.recv(1)):
                    self.__print__("disconnecting node %s while in loop" % handler.id, level=6)
                    self.server.disconnect(handler)
                    return
            handler.found_terminator()
        except socket.timeout:  # pragma: no cover
            return  # Shouldn't happen with select, but if it does...
        except Exception as e:
            if isinstance(e, socket.error) and e.args[0] in (9, 104, 10053, 10054, 10058):
                node_id = handler.id
                if not node_id:
                    node_id = repr(handler)
                self.__print__("Node %s has disconnected from the network" % node_id, level=1)
            else:
                self.__print__("There was an unhandled exception with peer id %s. This peer is being disconnected, and the relevant exception is added to the debug queue. If you'd like to report this, please post a copy of your mesh_socket.status to github.com/gappleto97/p2p-project/issues." % handler.id, level=0)
                self.exceptions.append((e, traceback.format_exc()))
            self.server.disconnect(handler)

class chord_socket(base_socket):
    def __init__(self, addr, port, prot=default_protocol, out_addr=None, debug_level=0):
        super(chord_socket, self).__init__(addr, port, prot, out_addr, debug_level)
        self.data = dict(((method, {}) for method in hashes))
        self.daemon = chord_daemon(addr, port, self)
        self.register_handler(self.__handle_handshake)
        self.register_handler(self.__handle_peers)
        self.register_handler(self.__handle_response)
        self.register_handler(self.__handle_request)

    @property
    def id_10(self):
        return from_base_58(self.id)

    def __findFinger__(self, key):
        current=self
        for x in xrange(k):
            if distance(current.id_10, key) > \
               distance(self.routing_table.get(x, self).id_10, key):
                current=self.routing_table.get(x, self)
        return current

    def __get_fingers(self, id):
        """Returns a finger table for your peer"""
        peer_list = []
        for x in xrange(k):
            finger = self.__findFinger__(id + 2**x)
            peer_list.append((finger.addr, x, finger.id))
        return peer_list

    def handle_msg(self, msg, conn):
        """Decides how to handle various message types, allowing some to be handled automatically"""
        if not super(mesh_socket, self).handle_msg(msg, conn):
            self.__print__("Ignoring message with invalid subflag", level=4)

    def __handle_handshake(self, msg, handler):
        packets = msg.packets
        if packets[0] == flags.handshake:
            if packets[2] != self.protocol.id:
                self.disconnect(handler)
                return True
            elif handler is not self.routing_table.get(packets[1], handler):
                self.__resolve_connection_conflict(handler, packets[1])
            handler.id = packets[1]
            handler.addr = json.loads(packets[3].decode())
            handler.compression = json.loads(packets[4].decode())
            handler.compression = [algo.encode() for algo in handler.compression]
            self.__print__("Compression methods changed to %s" % repr(handler.compression), level=4)
            if handler in self.awaiting_ids:
                self.awaiting_ids.remove(handler)
            handler.send(flags.whisper, flags.peers, json.dumps(self.__get_fingers(handler.id_10)))
            for x in xrange(k):
                goal = self.id_10 + 2**x
                if distance(self.__findFinger__(goal).id_10, goal) > distance(key, goal):
                    former = self.__findFinger__(goal)
                    self.routing_table[x] = handler
                    if former.outgoing and former not in self.routing_table.values():
                        self.disconnect(former)
            return True

    def __handle_peers(self, msg, handler):
        packets = msg.packets
        if packets[0] == flags.peers:
            new_peers = json.loads(packets[1].decode())
            for addr, index, key in new_peers:
                goal = self.id_10 + 2**index
                if distance(self.__findFinger__(goal).id_10, goal) > distance(key, goal):
                    self.connect(*addr)
            return True

    def __handle_response(self, msg, handler):
        packets = msg.packets
        if packets[0] == flags.response:
            self.__print__("Response received for request id %s" % packets[1], level=1)
            if self.requests.get(packets[1]):
                addr = json.loads(packets[2].decode())
                if addr:
                    msg = self.requests.get(packets[1])
                    self.requests.pop(packets[1])
                    self.connect(addr[0][0], addr[0][1], addr[1])
                    self.routing_table[addr[1]].send(*msg)
            return True

    def __handle_request(self, msg, handler):
        packets = msg.packets
        if packets[0] == flags.request:
            if packets[1] == b'*':
                handler.send(flags.whisper, flags.peers, json.dumps(self.__get_peer_list()))
            elif self.routing_table.get(packets[2]):
                handler.send(flags.broadcast, flags.response, packets[1], json.dumps([self.routing_table.get(packets[2]).addr, packets[2].decode()]))
            return True

    def dump_data(self, start, end=None):
        i = start
        ret = dict(((method, {}) for method in hashes))
        for method in self.data:
            for key in self.data[method]:
                if key >= start % limit and (not end or key < end % limit):
                    print(method, key, self.data)
                    ret[method].update({key: self.data[method][key]})
        return ret

    def connect(self, addr, port):
        """Connects to a specified node. Specifying ID will immediately add to routing table. Blocking"""
        self.__print__("Attempting connection to %s:%s" % (addr, port), level=1)
        if socket.getaddrinfo(addr, port)[0] == socket.getaddrinfo(*self.out_addr)[0]:
            self.__print__("Connection already established", level=1)
            return False
        conn = get_socket(self.protocol, False)
        conn.settimeout(1)
        conn.connect((addr, port))
        handler = chord_connection(conn, self, outgoing=True)
        handler.send(flags.whisper, flags.handshake, self.id, self.protocol.id, \
                     json.dumps(self.out_addr), json_compressions)
        self.awaiting_ids.append(handler)

    def __lookup(self, method, key):
        raise NotImplementedError

    def lookup(self, key):
        if not isinstance(key, bytes):
            key = str(key).encode()
        keys = [int(hashlib.new(algo, key).hexdigest(), 16) % limit for algo in hashes]
        vals = [self.__lookup(method, x) for method, x in zip(hashes, keys)]  # TODO: see if these work with generators
        common = most_common(vals)
        if common is not None and vals.count(common) > len(hashes) // 2:
            return common
        raise KeyError("This key does not have an agreed-upon value", vals)

    def __getitem__(self, key):
        return self.lookup(key)

    def __store(self, method, key, value):
        raise NotImplementedError

    def update(self, update_dict):
        for key in update_dict:
            value = update_dict[key]
            if not isinstance(key, bytes):
                key = str(key).encode()
            keys = [int(hashlib.new(algo, key).hexdigest(), 16) % limit for algo in hashes]
            for method, x in zip(hashes, keys):
                self.__store(method, x, value)

    def __setitem__(self, key, value):
        return self.update({key: value})

    def disconnect(self, handler):
        """Disconnects a node"""
        node_id = handler.id
        if not node_id:
            node_id = repr(handler)
        self.__print__("Connection to node %s has been closed" % node_id, level=1)
        if handler in self.awaiting_ids:
            self.awaiting_ids.remove(handler)
        elif handler in self.routing_table.values():
            for key in self.routing_table:
                if self.routing_table[key] is handler:
                    self.routing_table.remove(key)
        try:
            handler.sock.shutdown(socket.SHUT_RDWR)
        except:
            pass