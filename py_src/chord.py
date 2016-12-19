from __future__ import print_function
from __future__ import absolute_import

import hashlib
import json
import random
import select
import socket
import struct
import sys
import time
import traceback
import warnings

try:
    from .cbase import protocol
except:
    from .base import protocol

from .base import (flags, compression, to_base_58, from_base_58,
                base_connection, message, base_daemon, base_socket,
                InternalMessage, json_compressions)
from .utils import (getUTC, get_socket, intersect, awaiting_value, most_common)

max_outgoing = 4
default_protocol = protocol('chord', "Plaintext")  # SSL")
hashes = [b'sha1', b'sha224', b'sha256', b'sha384', b'sha512']

if sys.version_info >= (3,):
    xrange = range


def distance(a, b, limit=2**384):
    """This is a clockwise ring distance function.
    It depends on a globally defined k, the key size.
    The largest possible node id is limit (or 2**k)."""
    return (b - a) % limit


def get_hashes(key):
    [hashlib.new(algo.decode(), key).digest() for algo in hashes]


class chord_connection(base_connection):
    """The class for chord connection abstraction. This inherits from :py:class:`py2p.base.base_connection`"""
    def __init__(self, *args, **kwargs):
        super(chord_connection, self).__init__(*args, **kwargs)
        self.leeching = True

    def found_terminator(self):
        """This method is called when the expected amount of data is received

        Returns:
            ``None``
        """
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
        """Returns the nodes ID as an integer"""
        return from_base_58(self.id)

    def __hash__(self):
        return self.id_10 or id(self)


class chord_daemon(base_daemon):
    """The class for chord daemon. This inherits from :py:class:`py2p.base.base_daemon`"""
    def mainloop(self):
        """Daemon thread which handles all incoming data and connections"""
        while self.main_thread.is_alive() and self.alive:
            conns = list(self.server.routing_table.values()) + self.server.awaiting_ids
            for handler in select.select(conns + [self.sock], [], [], 0.01)[0]:
                if handler == self.sock:
                    self.handle_accept()
                else:
                    self.process_data(handler)
            for handler in conns:
                self.kill_old_nodes(handler)

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
            handler.sock.settimeout(1)
            self.server.awaiting_ids.append(handler)
        except exceptions:
            pass


class chord_socket(base_socket):
    """The class for chord socket abstraction. This inherits from :py:class:`py2p.base.base_socket`"""
    def __init__(self, addr, port, prot=default_protocol, out_addr=None, debug_level=0):
        """Initializes a chord socket

        Args:
            addr:           The address you wish to bind to (ie: "192.168.1.1")
            port:           The port you wish to bind to (ie: 44565)
            k:              This number indicates the node counts the network can support. You must have > (k+1) nodes.
                                You may only have up to 2**k nodes, but at that count you will likely get ID conficts.
            prot:           The protocol you wish to operate over, defined by a :py:class:`py2p.base.protocol` object
            out_addr:       Your outward facing address. Only needed if you're connecting over the internet. If you
                                use '0.0.0.0' for the addr argument, this will automatically be set to your LAN address.
            debug_level:    The verbosity you want this socket to use when printing event data

        Raises:
            socket.error:   The address you wanted could not be bound, or is otherwise used
        """
        super(chord_socket, self).__init__(addr, port, prot, out_addr, debug_level)
        self.id_10 = from_base_58(self.id)
        self.data = dict(((method, {}) for method in hashes))
        self.daemon = chord_daemon(addr, port, self)
        self.requests = {}
        self.register_handler(self.__handle_handshake)
        self.register_handler(self.__handle_peers)
        self.register_handler(self.__handle_meta)
        self.register_handler(self.__handle_response)
        self.register_handler(self.__handle_request)
        self.register_handler(self.__handle_retrieve)
        self.register_handler(self.__handle_store)
        self.leeching = True

    def request_peers(self):
        pass

    @property
    def addr(self):
        """An alternate binding for ``self.out_addr``, in order to better handle self-references in the daemon thread"""
        return self.out_addr

    @property
    def data_storing(self):
        return (node for node in self.routing_table.values() if not node.leeching)

    def handle_msg(self, msg, conn):
        """Decides how to handle various message types, allowing some to be handled automatically"""
        if not super(chord_socket, self).handle_msg(msg, conn):
            self.__print__("Ignoring message with invalid subflag", level=4)

    def __get_peer_list(self):
        """This function is used to generate a list-formatted group of your
        peers. It goes in format ``[ ((addr, port), ID), ...]``
        """
        peer_list = [(self.routing_table[key].addr, key.decode())
                     for key in self.routing_table]
        random.shuffle(peer_list)
        return peer_list

    def disconnect_least_efficient(self):
        """Disconnects the node which provides the least value.

        This is determined by finding the node which is the closest to
        its neighbors, using the modulus distance metric

        Returns:
            A :py:class:`bool` that describes whether a node was disconnected
        """
        def get_id(o):
            return o.id_10

        def smallest_gap(lst):
            coll = sorted(lst, key=get_id)
            coll_len = len(lst)
            circular_triplets = ((coll[x], coll[(x+1)%coll_len], coll[(x+2)%coll_len]) for x in range(coll_len))
            narrowest = None
            gap = 2**384
            for beg, mid, end in circular_triplets:
                if distance(beg.id_10, end.id_10) < gap and mid.outgoing:
                    gap = distance(beg.id_10, end.id_10)
                    narrowest = mid
            return narrowest

        relevant_nodes = (node for node in self.data_storing if not node.leeching)
        to_kill = smallest_gap(relevant_nodes)
        if to_kill:
            self.disconnect(to_kill)
            return True
        return False

    def __handle_handshake(self, msg, handler):
        """This callback is used to deal with handshake signals. Its two primary jobs are:

             - reject connections seeking a different network
             - set connection state

             Args:
                msg:        A :py:class:`~py2p.base.message`
                handler:    A :py:class:`~py2p.chord.chord_connection`

             Returns:
                Either ``True`` or ``None``
        """
        packets = msg.packets
        if packets[0] == flags.handshake:
            if packets[2] != self.protocol.id:
                self.disconnect(handler)
            elif not handler.id:
                handler.id = packets[1]
                self._send_handshake(handler)
                handler.addr = json.loads(packets[3].decode())
                handler.compression = json.loads(packets[4].decode())
                handler.compression = [algo.encode() for algo in handler.compression]
                self.__print__("Compression methods changed to %s" % repr(handler.compression), level=4)
                if handler in self.awaiting_ids:
                    self.awaiting_ids.remove(handler)
                self.routing_table.update({packets[1]: handler})
            return True

    def __handle_meta(self, msg, handler):
        """This callback is used to deal with handshake signals. Its two primary jobs are:

             - reject connections seeking a different network
             - set connection state

             Args:
                msg:        A :py:class:`~py2p.base.message`
                handler:    A :py:class:`~py2p.chord.chord_connection`

             Returns:
                Either ``True`` or ``None``
        """
        packets = msg.packets
        if packets[0] == flags.notify:
            new_meta = bool(int(packets[1]))
            if new_meta != handler.leeching:
                self._send_meta(handler)
                handler.leeching = new_meta
                if len(self.outgoing) > max_outgoing:
                    self.disconnect_least_efficient()
                if not self.leeching:
                    handler.send(flags.whisper, flags.peers, json.dumps(self.__get_peer_list()))
            return True

    def __handle_peers(self, msg, handler):
        """This callback is used to deal with peer signals. Its primary jobs
        is to connect to the given peers, if this does not exceed
        :py:const:`py2p.mesh.max_outgoing`

             Args:
                msg:        A :py:class:`~py2p.base.message`
                handler:    A :py:class:`~py2p.mesh.chord_connection`

             Returns:
                Either ``True`` or ``None``
        """
        packets = msg.packets
        if packets[0] == flags.peers:
            new_peers = json.loads(packets[1].decode())

            def is_prev(id):
                return distance(from_base_58(id), self.id_10) <= distance(self.prev, self.id_10)

            def is_next(id):
                return distance(self.id_10, from_base_58(id)) <= distance(self.id_10, self.next)

            for addr, id in new_peers:
                if len(self.outgoing) < max_outgoing or is_prev(id) or is_next(id):
                    try:
                        self.connect(addr[0], addr[1], id.encode())
                    except:  # pragma: no cover
                        self.__print__("Could not connect to %s because\n%s" %
                                       (addr, traceback.format_exc()), level=1)
                        continue
            return True

    def __handle_response(self, msg, handler):
        """This callback is used to deal with response signals. Its two primary jobs are:
             - if it was your request, send the deferred message
             - if it was someone else's request, relay the information
             Args:
                msg:        A :py:class:`~py2p.base.message`
                handler:    A :py:class:`~py2p.chord.chord_connection`
             Returns:
                Either ``True`` or ``None``
        """
        packets = msg.packets
        if packets[0] == flags.response:
            self.__print__("Response received for request id %s" % packets[1], level=1)
            if self.requests.get((packets[1], packets[2])):
                value = self.requests.get((packets[1], packets[2]))
                value.value = packets[3]
                if value.callback:
                    value.callback_method(packets[1], packets[2])
            return True

    def __handle_request(self, msg, handler):
        """This callback is used to deal with request signals. Its three primary jobs are:
             - respond with a peers signal if packets[1] is ``'*'``
             - if you know the ID requested, respond to it
             - if you don't, make a request with your peers
             Args:
                msg:        A :py:class:`~py2p.base.message`
                handler:    A :py:class:`~py2p.chord.chord_connection`
             Returns:
                Either ``True`` or ``None``
        """
        packets = msg.packets
        if packets[0] == flags.request:
            if packets[1] == b'*':
                handler.send(flags.whisper, flags.peers, json.dumps(self.__get_fingers()))
            else:
                goal = from_base_58(packets[1])
                node = self.find(goal)
                if node is not self:
                    node.send(flags.whisper, flags.request, packets[1], msg.id)
                    ret = awaiting_value()
                    ret.callback = handler
                    self.requests.update({(packets[1], msg.id): ret})
                else:
                    handler.send(flags.whisper, flags.response, packets[1], packets[2], self.out_addr)
            return True

    def __handle_retrieve(self, msg, handler):
        """This callback is used to deal with data retrieval signals. Its two primary jobs are:
             - respond with data you possess
             - if you don't possess it, make a request with your closest peer to that key
             Args:
                msg:        A :py:class:`~py2p.base.message`
                handler:    A :py:class:`~py2p.chord.chord_connection`
             Returns:
                Either ``True`` or ``None``
        """
        packets = msg.packets
        if packets[0] == flags.retrieve:
            if packets[1] in hashes:
                val = self.__lookup(packets[1], from_base_58(packets[2]), handler)
                if isinstance(val.value, str):
                    self.__print__(val.value)
                    handler.send(flags.whisper, flags.response, packets[1], packets[2], val.value)
                return True

    def __handle_store(self, msg, handler):
        """This callback is used to deal with data storage signals. Its two primary jobs are:
             - store data in keys you're responsible for
             - if you aren't responsible, make a request with your closest peer to that key
             Args:
                msg:        A :py:class:`~py2p.base.message`
                handler:    A :py:class:`~py2p.chord.chord_connection`
             Returns:
                Either ``True`` or ``None``
        """
        packets = msg.packets
        if packets[0] == flags.store:
            method = packets[1]
            key = from_base_58(packets[2])
            self.__store(method, key, packets[3])
            return True

    def dump_data(self, start, end=None):
        """Args:
            start:  An :py:class:`int` which indicates the start of the desired key range.
                        ``0`` will get all data.
            end:    An :py:class:`int` which indicates the end of the desired key range.
                        ``None`` will get all data. (default: ``None``)
        Returns:
            A nested :py:class:`dict` containing your data from start to end
        """
        i = start
        ret = dict(((method, {}) for method in hashes))
        for method in self.data:
            for key in self.data[method]:
                if key >= start % self.limit and (not end or key < end % self.limit):
                    print(method, key, self.data)
                    ret[method].update({key: self.data[method][key]})
            return ret

    def __lookup(self, method, key, handler=None):
        if self.routing_table:
            node = self.find(key)
        else:
            node = random.choice(self.awaiting_ids)
        if node in (self, None):
            return awaiting_value(self.data[method].get(key, ''))
        else:
            node.send(flags.whisper, flags.retrieve, method, to_base_58(key))
            ret = awaiting_value()
            if handler:
                ret.callback = handler
            self.requests.update({(method, to_base_58(key)): ret})
            return ret

    def lookup(self, key):
        """Looks up the value at a given key.
        Under the covers, this actually checks five different hash tables, and
        returns the most common value given.
        Args:
            key: The key that you wish to check. Must be a :py:class:`str` or
                    :py:class:`bytes`-like object
        Returns:
            The value at said key
        Raises:
            socket.timeout: If the request goes partly-unanswered for >=10 seconds
            KeyError:       If the request is made for a key with no agreed-upon value
        """
        if not isinstance(key, (bytes, bytearray)):
            key = str(key).encode()
        keys = [int(hashlib.new(algo.decode(), key).hexdigest(), 16) for algo in hashes]
        vals = [self.__lookup(method, x) for method, x in zip(hashes, keys)]
        common, count = most_common(vals)
        iters = 0
        limit = 100
        while common == -1 and iters < limit:
            time.sleep(0.1)
            iters += 1
            common, count = most_common(vals)
        if common not in (None, '') and count > len(hashes) // 2:
            return common
        elif iters == limit:
            raise socket.timeout()
        raise KeyError("This key does not have an agreed-upon value", vals)

    def __getitem__(self, key):
        return self.lookup(key)

    def get(self, key):
        return self.__getitem__(key)

    def __store(self, method, key, value):
        node = self.find(key)
        if self.leeching and node is self:
            node = random.choice(self.awaiting_ids)
        if node in (self, None):
            self.data[method].update({key: value})
        else:
            node.send(flags.whisper, flags.store, method, to_base_58(key), value)

    def store(self, key, value):
        """Updates the value at a given key.
        Under the covers, this actually uses five different hash tables, and
        updates the value in all of them.
        Args:
            key:    The key that you wish to update. Must be a :py:class:`str` or
                        :py:class:`bytes`-like object
            value:  The value you wish to put at this key. Must be a :py:class:`str`
                        or :py:class:`bytes`-like object
        """
        if not isinstance(key, (bytes, bytearray)):
            key = str(key).encode()
        keys = [int(hashlib.new(algo.decode(), key).hexdigest(), 16) for algo in hashes]
        for method, x in zip(hashes, keys):
            self.__store(method, x, value)

    def __setitem__(self, key, value):
        return self.store(key, value)

    def set(self, key, value):
        return self.__setitem__(key, value)

    def update(self, update_dict):
        """Equivalent to :py:meth:`dict.update`
        This calls :py:meth:`.chord_socket.store` for each key/value pair in the
        given dictionary.
        Args:
            update_dict: A :py:class:`dict`-like object to extract key/value pairs from.
                            Key and value be a :py:class:`str` or :py:class:`bytes`-like
                            object
        """
        for key, value in update_dict.items():
            self.__setitem__(key, value)

    def find(self, key):
        ret = self
        gap = distance(self.id_10, key)
        for handler in self.data_storing:
            if distance(handler.id_10, key) < gap:
                ret = handler
        return ret

    def find_prev(self, key):
        ret = self
        gap = distance(key, self.id_10)
        for handler in self.data_storing:
            if distance(key, handler.id_10) < gap:
                ret = handler
        return ret

    @property
    def next(self):
        return self.find(self.id_10 - 1)

    @property
    def prev(self):
        return self.find_prev(self.id_10 + 1)

    def connect(self, addr, port, id=None):
        """This function connects you to a specific node in the overall network.
        Connecting to one node *should* connect you to the rest of the network,
        however if you connect to the wrong subnet, the handshake failure involved
        is silent. You can check this by looking at the truthiness of this objects
        routing table. Example:

        .. code:: python

           >>> conn = chord.chord_socket('localhost', 4444)
           >>> conn.connect('localhost', 5555)
           >>> conn.join()
           >>> # do some other setup for your program
           >>> if (!conn.routing_table):
           ...     conn.connect('localhost', 6666)  # any fallback address
           ...     conn.join()

        Args:
           addr: A string address
           port: A positive, integral port
           id:   A string-like object which represents the expected ID of this node
        """
        self.__print__("Attempting connection to %s:%s with id %s" %
                       (addr, port, repr(id)), level=1)
        if (socket.getaddrinfo(addr, port)[0] ==
                socket.getaddrinfo(*self.out_addr)[0] or
                id in self.routing_table):
            self.__print__("Connection already established", level=1)
            return False
        conn = get_socket(self.protocol, False)
        conn.settimeout(1)
        conn.connect((addr, port))
        handler = chord_connection(conn, self, outgoing=True)
        self.awaiting_ids.append(handler)
        return handler

    def _send_handshake(self, handler):
        """Shortcut method for sending a handshake to a given handler

        Args:
            handler: A :py:class:`~py2p.chord.chord_connection`
        """
        json_out_addr = '["{}", {}]'.format(*self.out_addr)
        handler.send(flags.whisper, flags.handshake, self.id, \
                     self.protocol.id, json_out_addr, json_compressions)

    def _send_meta(self, handler):
        """Shortcut method for sending a chord-specific data to a given handler

        Args:
            handler: A :py:class:`~py2p.chord.chord_connection`
        """
        handler.send(flags.whisper, flags.notify, str(int(self.leeching)))

    def __connect(self, addr, port):
        """Private API method for connecting and handshaking

        Args:
            addr: the address you want to connect to/handshake
            port: the port you want to connect to/handshake
        """
        try:
            handler = self.connect(addr, port)
            if handler and not self.leeching:
                self._send_handshake(handler)
                self._send_meta(handler)
        except:
            pass

    def join(self):
        """Tells the node to start seeding the chord table"""
        # for handler in self.awaiting_ids:
        self.leeching = False
        handler = random.choice(
                tuple(self.data_storing) or \
                tuple(self.routing_table.values()) or \
                self.awaiting_ids)
        self._send_handshake(handler)
        self._send_meta(handler)

    def update(self, update_dict):
        """Equivalent to :py:meth:`dict.update`

        This calls :py:meth:`.chord_socket.store` for each key/value pair in the
        given dictionary.

        Args:
            update_dict: A :py:class:`dict`-like object to extract key/value pairs from.
                            Key and value be a :py:class:`str` or :py:class:`bytes`-like
                            object
        """
        for key, value in update_dict.items():
            self.__setitem__(key, value)

    def disconnect(self, handler):
        """Closes a given connection, and removes it from your routing tables

        Args:
            handler: the connection you would like to close
        """
        node_id = handler.id
        if not node_id:
            node_id = repr(handler)
        self.__print__("Connection to node %s has been closed" % node_id, level=1)
        if handler in self.awaiting_ids:
            self.awaiting_ids.remove(handler)
        elif handler in self.routing_table.values():
            for key, value in tuple(self.routing_table.items()):
                if value is handler:
                    self.routing_table.pop(key)
        try:
            handler.sock.shutdown(socket.SHUT_RDWR)
        except:
            pass
