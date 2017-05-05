from __future__ import print_function
from __future__ import absolute_import

import sys

from collections import deque
from platform import system
from itertools import chain
from logging import DEBUG
from random import shuffle
from select import select
from socket import (getaddrinfo, SHUT_RDWR, error as SocketException)
from struct import error as StructException
from traceback import format_exc

from base58 import b58decode_int
from typing import (cast, Any, Dict, List, Sequence, Set, Tuple, Union)
# from _collections import deque as DequeType

try:
    from .cbase import protocol as Protocol
except:
    from .base import Protocol

from . import flags
from .base import (BaseConnection, BaseDaemon, BaseSocket, Message)
from .messages import (compression, InternalMessage, MsgPackable)
from .utils import (getUTC, get_socket, intersect, inherit_doc, log_entry,
                    awaiting_value)

max_outgoing = 4
default_protocol = Protocol('mesh', "Plaintext")  # SSL")


class MeshConnection(BaseConnection):
    """The class for mesh connection abstraction.
    This inherits from :py:class:`py2p.base.BaseConnection`

    .. inheritance-diagram:: py2p.mesh.MeshConnection
    """

    @inherit_doc(BaseConnection.send)
    def send(
        self,  # type: MeshConnection
        msg_type,  # type: MsgPackable
        *args,  # type: MsgPackable
        **kargs  # type: Union[bytes, int]
    ):  # type: (...) -> InternalMessage
        msg = super(MeshConnection, self).send(msg_type, *args, **kargs)
        if msg and (msg.id, msg.time) not in self.server.waterfalls:
            self.server.waterfalls.add((msg.id, msg.time))
        return msg

    @inherit_doc(BaseConnection.found_terminator)
    def found_terminator(self):
        # type: (MeshConnection) -> Union[InternalMessage, None]
        try:
            msg = super(MeshConnection, self).found_terminator()
            packets = msg.packets
            self.__print__("Message received: {}".format(packets), level=1)
            if self.handle_renegotiate(packets):
                return msg
            elif self.handle_waterfall(msg, packets):
                return msg
            self.server.handle_msg(Message(msg, self.server), self)
            return msg
        except (IndexError, StructException) as e:
            self.__print__(
                "Failed to decode message. Expected first compression "
                "of: {}. Exception: {}".format(
                    intersect(compression, self.compression), e),
                level=1)
            self.send(flags.renegotiate, flags.compression, [])
            self.send(flags.renegotiate, flags.resend)
            return None

    def handle_waterfall(
        self,  # type: MeshConnection
        msg,  # type: InternalMessage
        packets  # type: Tuple[MsgPackable, ...]
    ):  # type: (...) -> bool
        """This method determines whether this message has been previously
        received or not.

        If it has been previously received, this method returns ``True``.

        If it is older than a preset limit, this method returns ``True``.

        Otherwise this method returns ``False``, and forwards the message
        appropriately.

        Args:
            msg:        The message in question
            packets:    The message's packets

        Returns:
            Either ``True`` or ``False``
        """
        if packets[0] == flags.broadcast:
            if msg.time < getUTC() - 60:
                self.__print__("Waterfall expired", level=2)
                return True
            elif not self.server.waterfall(Message(msg, self.server)):
                self.__print__("Waterfall already captured", level=2)
                return True
            self.__print__(
                "New waterfall received. Proceeding as normal", level=2)
        return False


class MeshDaemon(BaseDaemon):
    """The class for mesh daemon.
    This inherits from :py:class:`py2p.base.BaseDaemon`

    .. inheritance-diagram:: py2p.mesh.MeshDaemon
    """

    @log_entry('py2p.mesh.MeshDaemon', DEBUG)
    @inherit_doc(BaseDaemon.__init__)
    def __init__(self, *args, **kwargs):
        # type: (Any, *Any, **Any) -> None
        super(MeshDaemon, self).__init__(*args, **kwargs)
        self.conn_type = MeshConnection

    def mainloop(self):
        # type: (MeshDaemon) -> None
        """Daemon thread which handles all incoming data and connections"""
        while self.main_thread.is_alive() and self.alive:
            conns = chain(self.server.routing_table.values(),
                          self.server.awaiting_ids, (self.sock, ))
            for handler in select(cast(Sequence, conns), [], [], 0.01)[0]:
                if handler == self.sock:
                    self.handle_accept()
                else:
                    self.process_data(handler)
            for handler in chain(
                    tuple(self.server.routing_table.values()),
                    self.server.awaiting_ids):
                self.kill_old_nodes(handler)

    def handle_accept(self):
        # type: (MeshDaemon) -> Union[None, MeshConnection]
        """Handle an incoming connection"""
        if sys.version_info >= (3, 3):
            exceptions = (SocketException, ConnectionError)
        else:
            exceptions = (SocketException, )
        try:
            conn, addr = self.sock.accept()
            self.__print__('Incoming connection from %s' % repr(addr), level=1)
            handler = self.conn_type(conn, self.server)
            self.server._send_handshake(handler)
            handler.sock.settimeout(1)
            self.server.awaiting_ids.append(handler)
            return handler
        except exceptions:
            return None


class MeshSocket(BaseSocket):
    """The class for mesh socket abstraction.
    This inherits from :py:class:`py2p.base.BaseSocket`

    .. inheritance-diagram:: py2p.mesh.MeshSocket

    Added Events:

    .. raw:: html

        <div id="MeshSocket.Event 'connect'"></div>

    .. py:function:: Event 'connect'(conn)

        This event is called whenever you have a *new* connection to the
        service network. In other words, whenever the length of your routing
        table is increased from zero to one.

        If you call ``on('connect')``, that will be executed on every
        connection to the network. So if you are suddenly disconnected, and
        manage to recover, that function will execute again.

        To avoid this, call ``once('connect')``. That will usually be more
        correct.

        :param py2p.mesh.MeshSocket conn: A reference to this abstract socket

    .. raw:: html

        <div id="MeshSocket.Event 'message'"></div>

    .. py:function:: Event 'message'(conn)

        This event is called whenever you receive a new message. A reference
        to the message is *not* passed to you. This is to prevent potential
        memory leaks.

        If you want to register a "privileged" handler which *does* get a
        reference to the message, see
        :py:func:`~py2p.mesh.MeshSocket.register_handler`

        :param py2p.mesh.MeshSocket conn: A reference to this abstract socket
    """
    __slots__ = ('requests', 'waterfalls', 'queue', 'daemon')

    @log_entry('py2p.mesh.MeshSocket', DEBUG)
    def __init__(
            self,  # type: Any
            addr,  # type: str
            port,  # type: int
            prot=default_protocol,  # type: Protocol
            out_addr=None,  # type: Union[None, Tuple[str, int]]
            debug_level=0  # type: int
    ):  # type: (...) -> None
        """Initializes a mesh socket

        Args:
            addr:           The address you wish to bind to (ie: "192.168.1.1")
            port:           The port you wish to bind to (ie: 44565)
            prot:           The Protocol you wish to operate over, defined by
                                a :py:class:`py2p.base.Protocol` object
            out_addr:       Your outward facing address. Only needed if you're
                                connecting over the internet. If you use
                                '0.0.0.0' for the addr argument, this will
                                automatically be set to your LAN address.
            debug_level:    The verbosity you want this socket to use when
                                printing event data

        Raises:
            SocketException:   The address you wanted could not be bound, or is
                                otherwise used
        """
        if not hasattr(self, 'daemon'):
            self.daemon = 'mesh reserved'
        super(MeshSocket, self).__init__(addr, port, prot, out_addr,
                                         debug_level)
        # Metadata about msg replies where you aren't connected to the sender
        self.requests = {
        }  # type: Dict[Union[bytes, Tuple[bytes, bytes]], Union[Tuple[MsgPackable, ...], awaiting_value]]
        # Metadata of messages to waterfall
        self.waterfalls = set()  # type: Set[Tuple[bytes, int]]
        # Queue of received messages. Access through recv()
        self.queue = deque()  # type: deque
        if self.daemon == 'mesh reserved':
            self.daemon = MeshDaemon(addr, port, self)
        self.register_handler(self.__handle_handshake)
        self.register_handler(self._handle_peers)
        self.register_handler(self.__handle_response)
        self.register_handler(self.__handle_request)

    @inherit_doc(BaseSocket.handle_msg)
    def handle_msg(self, msg, conn):
        # type: (MeshSocket, Message, BaseConnection) -> Union[bool, None]
        if not super(MeshSocket, self).handle_msg(msg, conn):
            if msg.packets[0] in (flags.whisper, flags.broadcast):
                self.queue.appendleft(msg)
                self.emit('message', self)
            else:
                self.__print__(
                    "Ignoring message with invalid subflag", level=4)
            return True
        return None

    def _get_peer_list(self):
        # type: (MeshSocket) -> List[Tuple[Tuple[str, int], bytes]]
        """This function is used to generate a list-formatted group of your
        peers. It goes in format ``[ ((addr, port), ID), ...]``
        """
        peer_list = [(node.addr, key)
                     for key, node in self.routing_table.items() if node.addr]
        shuffle(peer_list)
        return peer_list

    def _send_handshake(self, handler):
        # type: (MeshSocket, MeshConnection) -> None
        """Shortcut method for sending a handshake to a given handler

        Args:
            handler: A :py:class:`~py2p.mesh.MeshConnection`
        """
        tmp_compress = handler.compression
        handler.compression = []
        handler.send(flags.whisper, flags.handshake, self.id, self.protocol.id,
                     self.out_addr, compression)
        handler.compression = tmp_compress

    def __resolve_connection_conflict(self, handler, h_id):
        # type: (MeshSocket, BaseConnection, bytes) -> None
        """Sometimes in trying to recover a network a race condition is
        created. This function applies a heuristic to try and organize the
        fallout from that race condition. While it isn't perfect, it seems to
        have increased connection recovery rate from ~20% to ~75%. This
        statistic is from memory on past tests. Much improvement can be made
        here, but this statistic can likely never be brought to 100%.

        In the failure condition, the overall network is unaffected *for large
        networks*. In small networks this failure condition causes a fork,
        usually where an individual node is kicked out.

        Args:
            handler: The handler with whom you have a connection conflict
            h_id:    The id of this handler
        """
        self.__print__(
            "Resolving peer conflict on id %s" % repr(h_id), level=1)
        to_kill = to_keep = None  # type: Union[None, BaseConnection]
        if (bool(b58decode_int(self.id) > b58decode_int(h_id)) ^
                bool(handler.outgoing)):  # logical xor
            self.__print__("Closing outgoing connection", level=1)
            to_keep, to_kill = self.routing_table[h_id], handler
            self.__print__(to_keep.outgoing, level=1)
        else:
            self.__print__("Closing incoming connection", level=1)
            to_keep, to_kill = handler, self.routing_table[h_id]
            self.__print__(not to_keep.outgoing, level=1)
        self.disconnect(cast(MeshConnection, to_kill))
        self.routing_table.update({h_id: to_keep})

    def _send_peers(self, handler):
        # type: (MeshSocket, BaseConnection) -> None
        """Shortcut method to send a handshake response. This method is
        extracted from :py:meth:`.__handle_handshake` in order to allow
        cleaner inheritence from :py:class:`py2p.sync.SyncSocket`
        """
        handler.send(flags.whisper, flags.peers,
                     cast(MsgPackable, self._get_peer_list()))

    def __handle_handshake(self, msg, handler):
        # type: (MeshSocket, Message, BaseConnection) -> Union[bool, None]
        """This callback is used to deal with handshake signals. Its three
        primary jobs are:

        - reject connections seeking a different network
        - set connection state
        - deal with connection conflicts

        Args:
            msg:        A :py:class:`~py2p.base.Message`
            handler:    A :py:class:`~py2p.mesh.MeshConnection`

        Returns:
            Either ``True`` or ``None``
        """
        packets = msg.packets
        if packets[0] == flags.handshake and len(packets) == 5:
            if packets[2] != self.protocol.id:
                self.__print__(
                    "Connected to peer on wrong subnet. ID: %s" % packets[2],
                    level=2)
                self.disconnect(cast(MeshConnection, handler))
                return True
            elif not handler.addr and len(self.routing_table) == 0:
                self.emit('connect', self)
            elif handler is not self.routing_table.get(packets[1], handler):
                self.__print__(
                    "Connection conflict detected. Trying to resolve", level=2)
                self.__resolve_connection_conflict(handler, packets[1])
            handler.id = packets[1]
            handler.addr = packets[3]
            handler.compression = packets[4]
            self.__print__(
                "Compression methods changed to %s" %
                repr(handler.compression),
                level=4)
            if handler in self.awaiting_ids:
                self.awaiting_ids.remove(handler)
            self.routing_table.update({packets[1]: handler})
            self._send_peers(handler)
            return True
        return None

    def _handle_peers(self, msg, handler):
        # type: (MeshSocket, Message, BaseConnection) -> Union[bool, None]
        """This callback is used to deal with peer signals. Its primary jobs
        is to connect to the given peers, if this does not exceed
        :py:const:`py2p.mesh.max_outgoing`

        Args:
            msg:        A :py:class:`~py2p.base.Message`
            handler:    A :py:class:`~py2p.mesh.MeshConnection`

        Returns:
            Either ``True`` or ``None``
        """
        packets = msg.packets
        if packets[0] == flags.peers:
            new_peers = packets[1]
            for addr, id in new_peers:
                if len(tuple(self.outgoing)) < max_outgoing:
                    try:
                        self.connect(addr[0], addr[1], id)
                    except:  # pragma: no cover
                        self.__print__(
                            "Could not connect to %s because\n%s" %
                            (addr, format_exc()),
                            level=1)
                        continue
            return True
        return None

    def __handle_response(self, msg, handler):
        # type: (MeshSocket, Message, BaseConnection) -> Union[bool, None]
        """This callback is used to deal with response signals. Its two
        primary jobs are:

        - if it was your request, send the deferred message
        - if it was someone else's request, relay the information

        Args:
            msg:        A :py:class:`~py2p.base.Message`
            handler:    A :py:class:`~py2p.mesh.MeshConnection`

        Returns:
            Either ``True`` or ``None``
        """
        packets = msg.packets
        if packets[0] == flags.response:
            self.__print__(
                "Response received for request id %s" % packets[1], level=1)
            if self.requests.get(packets[1]):
                addr = packets[2]
                if addr:
                    _msg = cast(Tuple[MsgPackable, ...],
                                self.requests.get(packets[1]))
                    self.requests.pop(packets[1])
                    self.connect(addr[0][0], addr[0][1], addr[1])
                    self.routing_table[addr[1]].send(*_msg)
            return True
        return None

    def __handle_request(self, msg, handler):
        # type: (MeshSocket, Message, BaseConnection) -> Union[bool, None]
        """This callback is used to deal with request signals. Its three
        primary jobs are:

        - respond with a peers signal if packets[1] is ``'*'``
        - if you know the ID requested, respond to it
        - if you don't, make a request with your peers

        Args:
            msg:        A :py:class:`~py2p.base.Message`
            handler:    A :py:class:`~py2p.mesh.MeshConnection`

        Returns:
            Either ``True`` or ``None``
        """
        packets = msg.packets
        if packets[0] == flags.request:
            if packets[1] == b'*':
                handler.send(flags.whisper, flags.peers,
                             cast(MsgPackable, self._get_peer_list()))
            elif self.routing_table.get(packets[2]):
                handler.send(flags.broadcast, flags.response, packets[1], [
                    self.routing_table.get(packets[2]).addr, packets[2]
                ])
            return True
        return None

    def send(self, *args, **kargs):
        # type: (MeshSocket, *MsgPackable, **MsgPackable) -> None
        """This sends a message to all of your peers. If you use default
        values it will send it to everyone on the network

        Args:
            *args:      A list of objects you want your peers to receive
            **kargs:    There are two keywords available:
            flag:       A string or bytes-like object which defines your flag.
                            In other words, this defines packet 0.
            type:       A string or bytes-like object which defines your
                            message type. Changing this from default can have
                            adverse effects.

        Raises:

            TypeError: If any of the arguments are not serializable. This
                        means your objects must be one of the following:

                        - :py:class:`bool`
                        - :py:class:`float`
                        - :py:class:`int` (if ``2**64 > x > -2**63``)
                        - :py:class:`str`
                        - :py:class:`bytes`
                        - :py:class:`unicode`
                        - :py:class:`tuple`
                        - :py:class:`list`
                        - :py:class:`dict` (if all keys are
                            :py:class:`unicode`)

        Warning:

            If you change the type attribute from default values, bad things
            could happen. It **MUST** be a value from
            :py:data:`py2p.base.flags`, and more specifically, it **MUST** be
            either ``broadcast`` or ``whisper``. The only other valid flags
            are ``waterfall`` and ``renegotiate``, but these are **RESERVED**
            and must **NOT** be used.
        """
        send_type = kargs.pop('type', flags.broadcast)
        main_flag = kargs.pop('flag', flags.broadcast)
        # map(methodcaller('send', 'broadcast', 'broadcast', *args),
        #     self.routing_table.values())
        handlers = list(self.routing_table.values())
        for handler in handlers:
            handler.send(main_flag, send_type, *args)

    def __clean_waterfalls(self):
        # type: (MeshSocket) -> None
        """This function cleans the :py:class:`set` of recently relayed
        messages based on the following heuristics:

        * Delete all older than 60 seconds
        """
        self.waterfalls = {i for i in self.waterfalls if i[1] > getUTC() - 60}

    def waterfall(self, msg):
        # type: (MeshSocket, Message) -> bool
        """This function handles message relays. Its return value is based on
        whether it took an action or not.

        Args:
            msg: The :py:class:`~py2p.base.Message` in question

        Returns:
            ``True`` if the message was then forwarded. ``False`` if not.
        """
        if (msg.id, msg.time) not in self.waterfalls:
            self.waterfalls.add((msg.id, msg.time))
            for handler in tuple(self.routing_table.values()):
                if handler.id != msg.sender:
                    handler.send_InternalMessage(msg.msg)
            self.__clean_waterfalls()
            return True
        else:
            self.__print__("Not rebroadcasting", level=3)
            return False

    def connect(self, addr, port, id=None, conn_type=MeshConnection):
        # type: (MeshSocket, str, int, bytes, Any) -> Union[None, bool]
        """This function connects you to a specific node in the overall
        network. Connecting to one node *should* connect you to the rest of
        the network, however if you connect to the wrong subnet, the handshake
        failure involved is silent. You can check this by looking at the
        truthiness of this objects routing table. Example:

        .. code:: python

           >>> conn = mesh.MeshSocket('localhost', 4444)
           >>> conn.connect('localhost', 5555)
           >>> # do some other setup for your program
           >>> if not conn.routing_table:
           ...     conn.connect('localhost', 6666)  # any fallback address

        Args:
           addr: A string address
           port: A positive, integral port
           id:   A string-like object which represents the expected ID of
                    this node
        """
        self.__print__(
            "Attempting connection to {}:{} with id {}".format(addr, port, id),
            level=1)
        if (getaddrinfo(addr, port)[0] == getaddrinfo(*self.out_addr)[0] or
                id in self.routing_table):
            self.__print__("Connection already established", level=1)
            return False
        conn = get_socket(self.protocol, False)
        conn.settimeout(1)
        conn.connect((addr, port))
        handler = conn_type(conn, self, outgoing=True)
        self._send_handshake(handler)
        if id:
            self.routing_table.update({id: handler})
        else:
            self.awaiting_ids.append(handler)
        return None

    def disconnect(self, handler):
        # type: (MeshSocket, MeshConnection) -> None
        """Closes a given connection, and removes it from your routing tables

        Args:
            handler: the connection you would like to close
        """
        node_id = handler.id  # type: Union[bytes, str]
        if not node_id:
            node_id = repr(handler)
        self.__print__(
            "Connection to node %s has been closed" % node_id, level=1)
        if handler in self.awaiting_ids:
            self.awaiting_ids.remove(handler)
        elif self.routing_table.get(handler.id) is handler:
            self.routing_table.pop(handler.id)
        try:
            handler.sock.shutdown(SHUT_RDWR)
        except:
            pass

    def request_peers(self):
        # type: (MeshSocket) -> None
        """Requests your peers' routing tables"""
        self.send('*', type=flags.request, flag=flags.whisper)

    def recv(self, quantity=1):
        # type: (MeshSocket, int) -> Union[None, Message, List[Message]]
        """This function has two behaviors depending on whether quantity is
        left as default.

        If quantity is given, it will return a list of
        :py:class:`~py2p.base.Message` objects up to length quantity.

        If quantity is left alone, it will return either a single
        :py:class:`~py2p.base.Message` object, or ``None``

        Args:
            quantity:   The maximum number of :py:class:`~py2p.base.Message` s
                            you would like to pull (default: 1)

        Returns:
            A list of :py:class:`~py2p.base.Message` s, an empty list, a
            single :py:class:`~py2p.base.Message` , or ``None``
        """
        if quantity != 1:
            ret_list = []
            while len(self.queue) and quantity > 0:
                ret_list.append(self.queue.pop())
                quantity -= 1
            return ret_list
        elif len(self.queue):
            return self.queue.pop()
        else:
            return None
