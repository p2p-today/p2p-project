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

from itertools import chain

try:
    from .cbase import protocol
except:
    from .base import protocol

from .base import (
    flags, compression, to_base_58, from_base_58, base_connection, message,
    base_daemon, base_socket, InternalMessage, json_compressions)
from .mesh import (
    mesh_connection, mesh_daemon, mesh_socket)
from .utils import (
    inherit_doc, getUTC, get_socket, intersect, awaiting_value, most_common)

max_outgoing = 4
default_protocol = protocol('chord', "Plaintext")  # SSL")
hashes = [b'sha1', b'sha224', b'sha256', b'sha384', b'sha512']

if sys.version_info >= (3,):
    xrange = range


def distance(a, b, limit=None):
    """This is a clockwise ring distance function. It depends on a globally
    defined k, the key size. The largest possible node id is limit (or
    ``2**384``).
    """
    return (b - a) % (limit or \
        0x1000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000)


def get_hashes(key):
    """Returns the (adjusted) hashes for a given key. This is in the order of:

    - SHA1 (shifted 224 bits left)
    - SHA224 (shifted 160 bits left)
    - SHA256 (shifted 128 bits left)
    - SHA384 (unadjusted)
    - SHA512 (unadjusted)

    The adjustment is made to allow better load balancing between nodes, which
    assign responisbility for a value based on their SHA384-assigned ID.
    """
    return (
        int(hashlib.sha1(key).hexdigest(), 16) << 224,  # 384 - 160
        int(hashlib.sha224(key).hexdigest(), 16) << 160,  # 384 - 224
        int(hashlib.sha256(key).hexdigest(), 16) << 128,  # 384 - 256
        int(hashlib.sha384(key).hexdigest(), 16),
        int(hashlib.sha512(key).hexdigest(), 16)
    )


class chord_connection(mesh_connection):
    """The class for chord connection abstraction. This inherits from
    :py:class:`py2p.mesh.mesh_connection`
    """
    @inherit_doc(mesh_connection.__init__)
    def __init__(self, *args, **kwargs):
        super(chord_connection, self).__init__(*args, **kwargs)
        self.leeching = True
        self.__id_10 = -1

    @property
    def id_10(self):
        """Returns the nodes ID as an integer"""
        if self.__id_10 == -1:
            self.__id_10 = from_base_58(self.id)
        return self.__id_10

    def __hash__(self):
        return self.id_10 or id(self)


class chord_daemon(mesh_daemon):
    """The class for chord daemon.
    This inherits from :py:class:`py2p.mesh.mesh_daemon`
    """
    @inherit_doc(mesh_daemon.__init__)
    def __init__(self, *args, **kwargs):
        super(chord_daemon, self).__init__(*args, **kwargs)
        self.conn_type = chord_connection

    @inherit_doc(mesh_daemon.handle_accept)
    def handle_accept(self):
        handler = super(chord_daemon, self).handle_accept()
        self.server._send_meta(handler)
        return handler


class chord_socket(mesh_socket):
    """The class for chord socket abstraction. This inherits from :py:class:`py2p.mesh.mesh_socket`"""
    @inherit_doc(mesh_socket.__init__)
    def __init__(self, addr, port, prot=default_protocol, out_addr=None, debug_level=0):
        if not hasattr(self, 'daemon'):
            self.daemon = 'chord reserved'
        super(chord_socket, self).__init__(addr, port, prot, out_addr, debug_level)
        if self.daemon == 'chord reserved':
            self.daemon = chord_daemon(addr, port, self)
        self.id_10 = from_base_58(self.id)
        self.data = dict(((method, {}) for method in hashes))
        self.__keys = set()
        self.leeching = True
        # self.register_handler(self._handle_peers)
        self.register_handler(self.__handle_meta)
        self.register_handler(self.__handle_key)
        self.register_handler(self.__handle_retrieved)
        self.register_handler(self.__handle_request)
        self.register_handler(self.__handle_retrieve)
        self.register_handler(self.__handle_store)

    @property
    def addr(self):
        """An alternate binding for ``self.out_addr``, in order to better handle self-references in pathfinding"""
        return self.out_addr

    @property
    def data_storing(self):
        return (node for node in self.routing_table.values() if not node.leeching)

    def disconnect_least_efficient(self):
        """Disconnects the node which provides the least value.

        This is determined by finding the node which is the closest to
        its neighbors, using the modulus distance metric

        Returns:
            A :py:class:`bool` that describes whether a node was disconnected
        """
        @inherit_doc(chord_connection.id_10)
        def get_id(o):
            return o.id_10

        def smallest_gap(lst):
            coll = sorted(lst, key=get_id)
            coll_len = len(coll)
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

    def __handle_meta(self, msg, handler):
        """This callback is used to deal with chord specific metadata.
        Its primary job is:

        - set connection state

        Args:
            msg:        A :py:class:`~py2p.base.message`
            handler:    A :py:class:`~py2p.chord.chord_connection`

        Returns:
            Either ``True`` or ``None``
        """
        packets = msg.packets
        if packets[0] == flags.handshake and len(packets) == 2:
            new_meta = bool(int(packets[1]))
            if new_meta != handler.leeching:
                self._send_meta(handler)
                handler.leeching = new_meta
                if not self.leeching and not handler.leeching:
                    handler.send(flags.whisper, flags.peers, json.dumps(self._get_peer_list()))
                    update = self.dump_data(handler.id_10, self.id_10)
                    for method, table in update.items():
                        for key, value in table.items():
                            self.__print__(method, key, value, level=5)
                            self.__store(method, key, value)
                if len(tuple(self.outgoing)) > max_outgoing:
                    self.disconnect_least_efficient()
            return True

    def __handle_key(self, msg, handler):
        """This callback is used to deal with new key entries. Its primary
        job is:

        - Ensure keylist syncronization

        Args:
            msg:        A :py:class:`~py2p.base.message`
            handler:    A :py:class:`~py2p.chord.chord_connection`

        Returns:
            Either ``True`` or ``None``
        """
        packets = msg.packets
        if packets[0] == flags.notify:
            if len(packets) == 3:
                if key in self.__keys:
                    self.__keys.remove(packets[1])
            else:
                self.__keys.add(packets[1])
            return True

    def _handle_peers(self, msg, handler):
        """This callback is used to deal with peer signals. Its primary jobs
        is to connect to the given peers, if this does not exceed
        :py:const:`py2p.chord.max_outgoing`

        Args:
            msg:        A :py:class:`~py2p.base.message`
            handler:    A :py:class:`~py2p.chord.chord_connection`

        Returns:
            Either ``True`` or ``None``
        """
        packets = msg.packets
        if packets[0] == flags.peers:
            new_peers = json.loads(packets[1].decode())

            def is_prev(id):
                return distance(from_base_58(id), self.id_10) <= distance(self.prev.id_10, self.id_10)

            def is_next(id):
                return distance(self.id_10, from_base_58(id)) <= distance(self.id_10, self.next.id_10)

            for addr, id in new_peers:
                if len(tuple(self.outgoing)) < max_outgoing or is_prev(id) or is_next(id):
                    try:
                        self.__connect(addr[0], addr[1], id.encode())
                    except:  # pragma: no cover
                        self.__print__("Could not connect to %s because\n%s" %
                                       (addr, traceback.format_exc()), level=1)
                        continue
            return True

    def __handle_retrieved(self, msg, handler):
        """This callback is used to deal with response signals. Its two
        primary jobs are:

        - if it was your request, send the deferred message
        - if it was someone else's request, relay the information

        Args:
            msg:        A :py:class:`~py2p.base.message`
            handler:    A :py:class:`~py2p.chord.chord_connection`

        Returns:
            Either ``True`` or ``None``
        """
        packets = msg.packets
        if packets[0] == flags.retrieved:
            self.__print__("Response received for request id %s" % packets[1],
                           level=1)
            if self.requests.get((packets[1], packets[2])):
                value = self.requests.get((packets[1], packets[2]))
                value.value = packets[3]
                if value.callback:
                    value.callback_method(packets[1], packets[2])
            return True

    def __handle_request(self, msg, handler):
        """This callback is used to deal with request signals. Its two
        primary jobs are:

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
            goal = from_base_58(packets[1])
            node = self.find(goal)
            if node is not self:
                node.send(flags.whisper, flags.request, packets[1], msg.id)
                ret = awaiting_value()
                ret.callback = handler
                self.requests[(packets[1], msg.id)] = ret
            else:
                handler.send(flags.whisper, flags.retrieved, packets[1], packets[2], self.out_addr)
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
                if isinstance(val.value, (str, bytes, bytearray)):
                    self.__print__(val.value, level=1)
                    handler.send(flags.whisper, flags.retrieved, packets[1], packets[2], val.value)
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

    def dump_data(self, start, end):
        """Args:
            start:  An :py:class:`int` which indicates the start of the desired key range.
                        ``0`` will get all data.
            end:    An :py:class:`int` which indicates the end of the desired key range.
                        ``None`` will get all data.

        Returns:
            A nested :py:class:`dict` containing your data from start to end
        """
        ret = dict(((method, {}) for method in hashes))
        self.__print__("Entering dump_data", level=1)
        for method, table in self.data.items():
            for key, value in table.items():
                if distance(start, key) < distance(end, key):
                    self.__print__(method, key, level=6)
                    ret[method][key] = value
        return ret

    def __lookup(self, method, key, handler=None):
        """Looks up the value at a given hash function and key. This method
        deals with just *one* of the underlying hash tables.

        Args:
            method: The hash table that you wish to check. Must be a
                        :py:class:`str` or :py:class:`bytes`-like object
            key:    The key that you wish to check. Must be a :py:class:`int` or
                        :py:class:`long`

        Returns:
            The value at said key, or an :py:class:`py2p.utils.awaiting_value`
            object, which will eventually contain its result
        """
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
            self.requests[method, to_base_58(key)] = ret
            return ret

    def __getitem__(self, key, timeout=10):
        """Looks up the value at a given key.
        Under the covers, this actually checks five different hash tables, and
        returns the most common value given.

        Args:
            key:        The key that you wish to check. Must be a :py:class:`str` or
                            :py:class:`bytes`-like object
            timeout:    The longest you would like to await a value (default: 10s)

        Returns:
            The value at said key

        Raises:
            socket.timeout: If the request goes partly-unanswered for >=timeout seconds
            KeyError:       If the request is made for a key with no agreed-upon value
        """
        if not isinstance(key, (bytes, bytearray)):
            key = str(key).encode()
        keys = get_hashes(key)
        vals = [self.__lookup(method, x) for method, x in zip(hashes, keys)]
        common, count = most_common(vals)
        iters = 0
        limit = timeout // 0.1
        fails = {None, b'', -1}
        while common in fails and iters < limit:
            time.sleep(0.1)
            iters += 1
            common, count = most_common(vals)
        if common not in fails and count > len(hashes) // 2:
            return common
        elif iters == limit:
            raise socket.timeout()
        raise KeyError("This key does not have an agreed-upon value. "
            "values={}, count={}, majority={}, most common ={}".format(
                vals,
                count,
                len(hashes) // 2 + 1,
                common))

    def get(self, key, ifError=None, timeout=10):
        """Looks up the value at a given key.
        Under the covers, this actually checks five different hash tables, and
        returns the most common value given.

        Args:
            key:     The key that you wish to check. Must be a :py:class:`str` or
                        :py:class:`bytes`-like object
            ifError: The value you wish to return on exception (default: ``None``)
            timeout: The longest you would like to await a value (default: 10s)

        Returns:
            The value at said key, or the value at ifError if there's an Exception
        """
        try:
            return self.__getitem__(key, timeout=timeout)
        except Exception:
            return ifError

    def __store(self, method, key, value):
        """Updates the value at a given key. This method deals with just *one*
        of the underlying hash tables.

        Args:
            method: The hash table that you wish to check. Must be a
                        :py:class:`str` or :py:class:`bytes`-like object
            key:    The key that you wish to check. Must be a :py:class:`int` or
                        :py:class:`long`
            value:  The value you wish to put at this key. Must be a :py:class:`str`
                        or :py:class:`bytes`-like object
        """
        node = self.find(key)
        if self.leeching and node is self:
            node = random.choice(self.awaiting_ids)
        if node in (self, None):
            if value == b'':
                del self.data[method][key]
            else:
                self.data[method][key] = value
        else:
            node.send(flags.whisper, flags.store, method, to_base_58(key), value)

    def __setitem__(self, key, value):
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
        if not isinstance(value, (bytes, bytearray)):
            value = str(value).encode()
        keys = get_hashes(key)
        for method, x in zip(hashes, keys):
            self.__store(method, x, value)
        if key not in self.__keys and value != b'':
            self.__keys.add(key)
            self.send(key, type=flags.notify)
        elif key in self.__keys and value == b'':
            self.__keys.add(key)
            self.send(key, b'del', type=flags.notify)

    @inherit_doc(__setitem__)
    def set(self, key, value):
        return self.__setitem__(key, value)

    def __delitem__(self, key):
        if not isinstance(key, (bytes, bytearray)):
            key = str(key).encode()
        if key not in self.__keys:
            raise KeyError(key)
        self.set(key, '')

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
        """Finds the node which is responsible for a certain value. This does
        not necessarily mean that they are supposed to store that value, just
        that they are along your path to said node.

        Args:
            key:    The key that you wish to check. Must be a :py:class:`int` or
                        :py:class:`long`

        Returns: A :py:class:`~py2p.chord.chord_connection` or this socket
        """
        if not self.leeching:
            ret = self
            gap = distance(self.id_10, key)
        else:
            ret = None
            gap = 2**384
        for handler in self.data_storing:
            dist = distance(handler.id_10, key)
            if dist < gap:
                ret = handler
                gap = dist
        return ret

    def find_prev(self, key):
        """Finds the node which is farthest from a certain value. This is used
        to find a node's "predecessor"; the node it is supposed to delegate to
        in the event of a disconnections.

        Args:
            key:    The key that you wish to check. Must be a :py:class:`int` or
                        :py:class:`long`

        Returns: A :py:class:`~py2p.chord.chord_connection` or this socket
        """
        if not self.leeching:
            ret = self
            gap = distance(key, self.id_10)
        else:
            ret = None
            gap = 2**384
        for handler in self.data_storing:
            dist = distance(key, handler.id_10)
            if dist < gap:
                ret = handler
                gap = dist
        return ret

    @property
    def next(self):
        """The connection that is your nearest neighbor *ahead* on the
        hash table ring
        """
        return self.find(self.id_10 - 1)

    @property
    def prev(self):
        """The connection that is your nearest neighbor *behind* on the
        hash table ring
        """
        return self.find_prev(self.id_10 + 1)

    def _send_peers(self, handler):
        """Shortcut method for sending a peerlist to a given handler

        Args:
            handler: A :py:class:`~py2p.chord.chord_connection`
        """
        handler.send(flags.whisper, flags.peers,
                     json.dumps(self._get_peer_list()))

    def _send_meta(self, handler):
        """Shortcut method for sending a chord-specific data to a given handler

        Args:
            handler: A :py:class:`~py2p.chord.chord_connection`
        """
        handler.send(flags.whisper, flags.handshake, str(int(self.leeching)))
        for key in self.__keys.copy():
            handler.send(flags.whisper, flags.notify, key)

    def __connect(self, addr, port, id=None):
        """Private API method for connecting and handshaking

        Args:
            addr: the address you want to connect to/handshake
            port: the port you want to connect to/handshake
        """
        try:
            handler = self.connect(addr, port, id)
            if handler and not self.leeching:
                self._send_handshake(handler)
                self._send_meta(handler)
        except:
            pass

    def join(self):
        """Tells the node to start seeding the chord table"""
        # for handler in self.awaiting_ids:
        self.leeching = False
        for handler in tuple(self.routing_table.values()) + tuple(self.awaiting_ids):
            self._send_handshake(handler)
            self._send_peers(handler)
            self._send_meta(handler)

    def unjoin(self):
        """Tells the node to stop seeding the chord table"""
        self.leeching = True
        for handler in tuple(self.routing_table.values()) + tuple(self.awaiting_ids):
            self._send_handshake(handler)
            self._send_peers(handler)
            self._send_meta(handler)
        for method in self.data.keys():
            for key, value in self.data[method].items():
                self.__store(method, key, value)
            self.data[method].clear()

    def __del__(self):
        self.unjoin()
        super(chord_socket, self).__del__()

    @inherit_doc(mesh_socket.connect)
    def connect(self, *args, **kwargs):
        if kwargs.get('conn_type'):
            return super(chord_socket, self).connect(*args, **kwargs)
        return super(chord_socket, self).connect(*args, conn_type=chord_connection, **kwargs)

    def keys(self):
        """Returns an iterator of the underlying :py:class:`dict`'s keys"""
        return (key for key in self.__keys if key in self.__keys)

    @inherit_doc(keys)
    def __iter__(self):
        return self.keys()

    def values(self):
        """Returns:
            an iterator of the underlying :py:class:`dict`'s values

        Raises:
            KeyError:       If the key does not have a majority-recognized
                                value
            socket.timeout: See KeyError
        """
        return (self[key] for key in self.keys())

    def items(self):
        """Returns:
            an iterator of the underlying :py:class:`dict`'s items

        Raises:
            KeyError:       If the key does not have a majority-recognized
                                value
            socket.timeout: See KeyError
        """
        return ((key, self[key]) for key in self.keys())

    def pop(self, key, *args):
        """Returns a value, with the side effect of deleting that association

        Args:
            Key:        The key you wish to look up. Must be a :py:class:`str`
                            or :py:class:`bytes`-like object
            ifError:    The value you wish to return on Exception
                            (default: raise an Exception)

        Returns:
            The value of the supplied key, or ``ifError``

        Raises:
            KeyError:       If the key does not have a majority-recognized
                                value
            socket.timeout: See KeyError
        """
        if len(args):
            ret = self.get(key, args[0])
            if ret != args[0]:
                del self[key]
        else:
            ret = self[key]
            del self[key]
        return ret

    def popitem(self):
        """Returns an association, with the side effect of deleting that
        association

        Returns:
            An arbitrary association

        Raises:
            KeyError:       If the key does not have a majority-recognized
                                value
            socket.timeout: See KeyError
        """
        key, value = next(self.items())
        del self[key]
        return (key, value)

    def copy(self):
        """Returns a :py:class:`dict` copy of this DHT

        .. warning::

            This is a *very* slow operation. It's a far better idea to use
            :py:meth:`~py2p.chord.chord_socket.items`, as this produces an
            iterator. That should even out lag times
        """
        return dict(self.items())
