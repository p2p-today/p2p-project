"""A library to store common functions and protocol definitions"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import with_statement

import inspect

from hashlib import (sha256, sha384)
from itertools import chain
from logging import (getLogger, DEBUG)
from socket import (SHUT_RDWR, error as SocketException, timeout as
                    TimeoutException)
from sys import version_info
from threading import (Lock, Thread, current_thread)
from traceback import format_exc
from uuid import uuid4

from base58 import (b58encode, b58encode_int)
from pyee import EventEmitter
from typing import (cast, Any, Callable, Dict, Iterable, List, NamedTuple,
                    Sequence, Tuple, Union)

from . import flags
from .messages import (compression, InternalMessage, MsgPackable)
from .utils import (getUTC, intersect, get_lan_ip, get_socket, inherit_doc,
                    log_entry, unpack_value)

protocol_version = "0.7"
node_policy_version = "870"

version = '.'.join((protocol_version, node_policy_version))

plock = Lock()

user_salt = str(uuid4()).encode()


class Protocol(
        NamedTuple("_Protocol", [('subnet', str), ('encryption', str)])):
    """Defines service variables so that you can reject connections looking
    for a different service

    Attributes:
        subnet:     The subnet flag this Protocol uses
        encryption: The encryption method this Protocol uses
        id:         The SHA-256 based ID of this Protocol
    """
    __slots__ = ()

    @property
    def id(self):
        # type: (Protocol) -> str
        """The SHA-256-based ID of the Protocol"""
        h = sha256(''.join(str(x) for x in self).encode())
        h.update(protocol_version.encode())
        return b58encode_int(int(h.hexdigest(), 16))


default_protocol = Protocol('', "Plaintext")  # SSL")


class BaseConnection(object):
    """The base class for a connection"""
    __slots__ = ('sock', 'server', 'outgoing', 'buffer', 'id', 'time', 'addr',
                 'compression', 'last_sent', 'expected', 'active')

    @log_entry('py2p.base.BaseConnection.__init__', DEBUG)
    def __init__(self, sock, server, outgoing=False):
        # type: (BaseConnection, Any, BaseSocket, bool) -> None
        """Sets up a connection to another peer-to-peer socket

        Args:
            sock:       The connected socket object
            server:     A reference to your peer-to-peer socket
            outgoing:   Whether this connection is outgoing (default: False)
        """
        self.sock = sock
        self.server = server
        self.outgoing = outgoing
        self.buffer = bytearray()
        self.id = None  # type: Union[None, bytes]
        self.time = getUTC()
        self.addr = None  # type: Union[None, Tuple[str, int]]
        self.compression = []  # type: List[int]
        self.last_sent = ()  # type: Tuple[MsgPackable, ...]
        self.expected = 4
        self.active = False

    def send_InternalMessage(
            self,  # type: BaseConnection
            msg  # type: InternalMessage
    ):  # type: (...) -> Union[InternalMessage, None]
        """Sends a preconstructed message

        Args:
            msg: The :py:class:`~py2p.base.IntenalMessage` you wish to send

        Returns:
            the :py:class:`~py2p.base.IntenalMessage` object you just sent, or
            ``None`` if the sending was unsuccessful
        """
        msg.compression = self.compression  # type: ignore
        if msg.msg_type in (flags.whisper, flags.broadcast):
            self.last_sent = msg.payload
        self.__print__("Sending %s to %s" % (msg.packets, self), level=4)
        if msg.compression_used:
            self.__print__(
                "Compressing with %s" % repr(msg.compression_used), level=4)
        try:
            self.sock.send(msg.string)
            return msg
        except (IOError, SocketException) as e:  # pragma: no cover
            self.server.daemon.exceptions.append(format_exc())
            self.server.disconnect(self)
            return None

    def send(
            self,  # type: BaseConnection
            msg_type,  # type: MsgPackable
            *args,  # type: MsgPackable
            **kargs  # type: Union[bytes, int]
    ):  # type: (...) -> InternalMessage
        """Sends a message through its connection.

        Args:
            msg_type:  Message type, corresponds to the header in a
                           :py:class:`~py2p.base.InternalMessage` object
            *args:     A list of bytes-like objects, which correspond to the
                           packets to send to you
            **kargs:   There are two available keywords:
            id:        The ID this message should appear to be sent from
                           (default: your ID)
            time:      The time this message should appear to be sent from
                           (default: now in UTC)

        Returns:
            the :py:class:`~py2p.base.IntenalMessage` object you just sent, or
            ``None`` if the sending was unsuccessful
        """
        # Latter is returned if key not found
        id = cast(bytes, kargs.get('id', self.server.id))
        time = cast(int, kargs.get('time') or getUTC())
        # Begin real method
        msg = InternalMessage(
            msg_type, id, args, self.compression, timestamp=time)
        return self.send_InternalMessage(msg)

    @property
    def protocol(self):
        # type: (BaseConnection) -> Protocol
        """Returns server.protocol"""
        return self.server.protocol

    def collect_incoming_data(self, data):
        # type: (BaseConnection, Union[bytes, bytearray]) -> bool
        """Collects incoming data

        Args:
            data:   The most recently received :py:class:`bytes`

        Returns:
            ``True`` if the data collection was successful, ``False`` if the
            connection was closed
        """
        if not bool(data):
            try:
                self.sock.shutdown(SHUT_RDWR)
            except:
                pass
            return False
        self.buffer.extend(data)
        self.time = getUTC()
        if not self.active and self.find_terminator():
            self.__print__(
                self.buffer, self.expected, self.find_terminator(), level=4)
            self.expected = unpack_value(bytes(self.buffer[:4])) + 4
            self.active = True
        return True

    def find_terminator(self):
        # type: (BaseConnection) -> bool
        """Returns whether the defined return sequences is found"""
        return len(self.buffer) >= self.expected

    def found_terminator(self):
        # type: (BaseConnection) -> InternalMessage
        """Processes received messages"""
        raw_msg, self.buffer = bytes(
            self.buffer[:self.expected]), self.buffer[self.expected:]
        self.__print__("Received: %s" % repr(raw_msg), level=6)
        self.active = len(self.buffer) > 4
        if self.active:
            self.expected = unpack_value(bytes(self.buffer[:4])) + 4
        else:
            self.expected = 4
        msg = InternalMessage.feed_string(raw_msg, False, self.compression)
        return msg

    def handle_renegotiate(self, packets):
        # type: (BaseConnection, Sequence[MsgPackable]) -> bool
        """The handler for connection renegotiations

        This is to deal with connection maintenance. For instance, it could
        be that a compression method fails to decode on the other end, and a
        node will need to renegotiate which methods it is using. Hence the
        name of the flag associated with it, "renegotiate".

        Args:
            packets:    A :py:class:`tuple` containing the packets received
                            in this message

        Returns:
            ``True`` if an action was taken, ``False`` if not
        """
        if packets[0] == flags.renegotiate:
            if packets[3] == flags.compression:
                encoded_methods = packets[4]
                respond = (self.compression != encoded_methods)
                self.compression = list(cast(Iterable[int], encoded_methods))
                self.__print__(
                    "Compression methods changed to: %s" %
                    repr(self.compression),
                    level=2)
                if respond:
                    self.send(flags.renegotiate, flags.compression,
                              cast(Tuple[int, ...],
                                   intersect(compression, self.compression)))
                return True
            elif packets[3] == flags.resend:
                self.send(*self.last_sent)
                return True
        return False

    def fileno(self):
        # type: (BaseConnection) -> int
        """Mirror for the fileno() method of the connection's
        underlying socket
        """
        return self.sock.fileno()

    def __print__(self, *args, **kargs):
        # type: (BaseConnection, *Any, **int) -> None
        """Private method to print if level is <= self.server.debug_level

        Args:
            *args:   Each argument you wish to feed to the print method
            **kargs: One keyword is used here: level, which defines the
                         lowest value of self.server.debug_level at which
                         the message will be printed
        """
        self.server.__print__(*args, **kargs)


class BaseDaemon(object):
    """The base class for a daemon"""
    __slots__ = ('server', 'sock', 'exceptions', 'alive', '_logger',
                 'main_thread', 'daemon', 'conn_type')

    @log_entry('py2p.base.BaseDaemon.__init__', DEBUG)
    def __init__(self, addr, port, server):
        # type: (Any, str, int, BaseSocket) -> None
        """Sets up a daemon process for your peer-to-peer socket

        Args:
            addr:   The address you wish to bind to
            port:   The port you wish to bind to
            server: A reference to the peer-to-peer socket

        Raises:
            socket.error: The address you wanted is already in use
            ValueError:   If your peer-to-peer socket is set up with an
                              unknown encryption method
        """
        self.server = server
        self.sock = get_socket(self.protocol, True)
        self.sock.bind((addr, port))
        self.sock.listen(5)
        self.sock.settimeout(0.1)
        self.exceptions = []  # type: List[str]
        self.alive = True
        self._logger = getLogger(
            '{}.{}.{}'.format(self.__class__.__module__,
                              self.__class__.__name__, self.server.id))
        self.main_thread = current_thread()
        self.daemon = Thread(target=self.mainloop)
        self.daemon.start()

    @property
    def protocol(self):
        # type: (BaseDaemon) -> Protocol
        """Returns server.protocol"""
        return self.server.protocol

    def kill_old_nodes(self, handler):
        # type: (BaseDaemon, BaseConnection) -> None
        """Cleans out connections which never finish a message"""
        if handler.active and handler.time < getUTC() - 60:
            self.server.disconnect(handler)

    def process_data(self, handler):
        # type: (BaseDaemon, BaseConnection) -> None
        """Collects incoming data from nodes"""
        try:
            while not handler.find_terminator():
                if not handler.collect_incoming_data(handler.sock.recv(1024)):
                    self.__print__(
                        "disconnecting node %s while in loop" % handler.id,
                        level=6)
                    self.server.disconnect(handler)
                    self.server.request_peers()
                    return
            while handler.find_terminator():
                handler.found_terminator()
        except TimeoutException:  # pragma: no cover
            return  # Shouldn't happen with select, but if it does...
        except Exception as e:
            if (isinstance(e, SocketException) and
                    e.args[0] in (9, 104, 10053, 10054, 10058)):
                node_id = repr(handler.id or handler)
                self.__print__(
                    "Node %s has disconnected from the network" % node_id,
                    level=1)
            else:
                self.__print__(
                    "There was an unhandled exception with peer id %s. This "
                    "peer is being disconnected, and the relevant exception "
                    "is added to the debug queue. If you'd like to report "
                    "this, please post a copy of your MeshSocket.status to "
                    "git.p2p.today/issues." % handler.id,
                    level=0)
                self.__print__("This exception was: {}".format(e), level=1)
                self.exceptions.append(format_exc())
            self.server.disconnect(handler)
            self.server.request_peers()

    def __del__(self):
        # type: (BaseDaemon) -> None
        self.alive = False
        try:
            self.sock.shutdown(SHUT_RDWR)
        except:  # pragma: no cover
            pass

    @inherit_doc(BaseConnection.__print__)
    def __print__(self, *args, **kargs):
        # type: (BaseDaemon, *Any, **int) -> None
        self.server.__print__(*args, **kargs)


class BaseSocket(EventEmitter, object):
    """
    The base class for a peer-to-peer socket abstractor

    .. inheritance-diagram:: py2p.base.BaseSocket
    """
    __slots__ = ('protocol', 'debug_level', 'routing_table', 'awaiting_ids',
                 'out_addr', 'id', '_logger', '__handlers', '__closed')

    @log_entry('py2p.base.BaseSocket.__init__', DEBUG)
    def __init__(
            self,  # type: Any
            addr,  # type: str
            port,  # type: int
            prot=default_protocol,  # type: Protocol
            out_addr=None,  # type: Union[None, Tuple[str, int]]
            debug_level=0  # type: int
    ):  # type: (...) -> None
        """Initializes a peer to peer socket

        Args:
            addr:        The address you wish to bind to (ie: "192.168.1.1")
            port:        The port you wish to bind to (ie: 44565)
            prot:        The protocol you wish to operate over, defined by a
                             :py:class:`py2p.base.Protocol` object
            out_addr:    Your outward facing address. Only needed if you're
                             connecting over the internet. If you use '0.0.0.0'
                             for the addr argument, this will automatically be
                             set to your LAN address.
            debug_level: The verbosity you want this socket to use when
                             printing event data

        Raises:
            socket.error: The address you wanted could not be bound, or is
            otherwise used
        """
        object.__init__(self)
        EventEmitter.__init__(self)
        self.protocol = prot
        self.debug_level = debug_level
        self.routing_table = {}  # type: Dict[bytes, BaseConnection]
        # In format {ID: handler}
        self.awaiting_ids = []  # type: List[BaseConnection]
        # Connected, but not handshook yet
        if out_addr:  # Outward facing address, if you're port forwarding
            self.out_addr = out_addr
        elif addr == '0.0.0.0':
            self.out_addr = get_lan_ip(), port
        else:
            self.out_addr = addr, port
        info = (str(self.out_addr).encode(), prot.id.encode(), user_salt)
        h = sha384(b''.join(info))
        self.id = b58encode_int(int(h.hexdigest(), 16)).encode()  # type: bytes
        self._logger = getLogger('{}.{}.{}'.format(
            self.__class__.__module__, self.__class__.__name__, self.id))
        self.__handlers = [
        ]  # type: List[Callable[[Message, BaseConnection], Union[bool, None]]]
        self.__closed = False

    def close(self):
        # type: (BaseSocket) -> None
        """If the socket is not closed, close the socket

        Raises:
            RuntimeError:   The socket was already closed
        """
        if self.__closed:
            raise RuntimeError("Already closed")
        else:
            self.daemon.alive = False
            self.daemon.daemon.join()
            self.debug_level = 0
            try:
                self.daemon.sock.shutdown(SHUT_RDWR)
            except:
                pass
            for conn in chain(
                    tuple(self.routing_table.values()), self.awaiting_ids):
                self.disconnect(conn)
            self.__closed = True

    if version_info >= (3, ):

        def register_handler(
                self,  # type: BaseSocket
                method  # type: Callable[..., Union[bool, None]]
        ):  # type: (...) -> None
            """Register a handler for incoming method.

            Args:
                method: A function with two given arguments. Its signature
                            should be of the form ``handler(msg, handler)``,
                            where msg is a :py:class:`py2p.base.Message`
                            object, and handler is a
                            :py:class:`py2p.base.BaseConnection` object. It
                            should return ``True`` if it performed an action,
                            to reduce the number of handlers checked.

            Raises:
                ValueError: If the method signature doesn't parse correctly
            """
            args = inspect.signature(method)
            if (len(args.parameters) !=
                (3 if args.parameters.get('self') else 2)):
                raise ValueError(
                    "This method must contain exactly two arguments "
                    "(or three if first is self)")
            self.__handlers.append(method)

    else:

        def register_handler(
                self,  # type: BaseSocket
                method  # type: Callable[..., Union[bool, None]]
        ):  # type: (...) -> None
            """Register a handler for incoming method.

            Args:
                method: A function with two given arguments. Its signature
                            should be of the form ``handler(msg, handler)``,
                            where msg is a :py:class:`py2p.base.Message`
                            object, and handler is a
                            :py:class:`py2p.base.BaseConnection` object. It
                            should return ``True`` if it performed an action,
                            to reduce the number of handlers checked.

            Raises:
                ValueError: If the method signature doesn't parse correctly
            """
            args = inspect.getargspec(method)
            if (args[1:] != (None, None, None) or
                    len(args[0]) != (3 if args[0][0] == 'self' else 2)):
                raise ValueError(
                    "This method must contain exactly two arguments "
                    "(or three if first is self)")
            self.__handlers.append(method)

    def handle_msg(self, msg, conn):
        # type: (BaseSocket, Message, BaseConnection) -> Union[bool, None]
        """Decides how to handle various message types, allowing some to be
        handled automatically

        Args:
            msg:    A :py:class:`py2p.base.Message` object
            conn:   A :py:class:`py2p.base.BaseConnection` object

        Returns:
            True if an action was taken, None if not.
        """
        for handler in self.__handlers:
            self.__print__("Checking handler: %s" % handler.__name__, level=4)
            if handler(msg, conn):
                self.__print__(
                    "Breaking from handler: %s" % handler.__name__, level=4)
                return True
        return None

    @property
    def status(self):
        # type: (BaseSocket) -> Union[str, List[str]]
        """The status of the socket.

        Returns:
            ``"Nominal"`` if all is going well, or a list of unexpected
            (Exception, traceback) tuples if not
        """
        return self.daemon.exceptions or "Nominal"

    @property
    def outgoing(self):
        # type: (BaseSocket) -> Iterable[bytes]
        """IDs of outgoing connections"""
        return (handler.id for handler in self.routing_table.values()
                if handler.outgoing)

    @property
    def incoming(self):
        # type: (BaseSocket) -> Iterable[bytes]
        """IDs of incoming connections"""
        return (handler.id for handler in self.routing_table.values()
                if not handler.outgoing)

    def __print__(self, *args, **kargs):
        # type: (BaseSocket, *Any, **int) -> None
        """Private method to print if level is <= self.debug_level

        Args:
            *args:   Each argument you wish to feed to the print method
            **kargs: One keyword is used here: level, which defines the
                         lowest value of self.debug_level at which the message
                         will be printed
        """
        if kargs.get('level', 0) <= self.debug_level:
            with plock:
                print(self.out_addr[1], *args)

    def __del__(self):
        # type: (BaseSocket) -> None
        if not self.__closed:
            self.close()


class Message(object):
    """An object which gets returned to a user, containing all necessary
    information to parse and reply to a message
    """
    __slots__ = ('msg', 'server')

    def __init__(self, msg, server):
        # type: (Message, InternalMessage, BaseSocket) -> None
        """Initializes a Message object

        Args:
            msg:    A :py:class:`py2p.base.InternalMessage` object
            server: A :py:class:`py2p.base.BaseSocket` object
        """
        self.msg = msg
        self.server = server

    @property
    def time(self):
        # type: (Message) -> int
        """The time this Message was sent at"""
        return self.msg.time

    @property  # type: ignore
    @inherit_doc(InternalMessage.time_58)
    def time_58(self):
        # type: (Message) -> bytes
        return self.msg.time_58

    @property
    def sender(self):
        # type: (Message) -> bytes
        """The ID of this Message's sender"""
        return self.msg.sender

    @property  # type: ignore
    @inherit_doc(InternalMessage.id)
    def id(self):
        # type: (Message) -> bytes
        return self.msg.id

    @property  # type: ignore
    @inherit_doc(InternalMessage.payload)
    def packets(self):
        # type: (Message) -> Tuple[MsgPackable, ...]
        return self.msg.payload

    @inherit_doc(InternalMessage.__len__)
    def __len__(self):
        # type: (Message) -> int
        return self.msg.__len__()

    def __repr__(self):
        # type: (Message) -> str
        packets = self.packets
        return "Message(type={}, packets={}, sender={})".format(
            packets[0], packets[1:], self.sender)

    def reply(self, *args):
        # type: (Message, *MsgPackable) -> None
        """Replies to the sender if you're directly connected. Tries to make
        a connection otherwise

        Args:
            *args: Each argument given is a packet you wish to send. This is
                       prefixed with base.flags.whisper, so the other end will
                       receive ``[base.flags.whisper, *args]``
        """
        self.server._logger.debug(
            'Initiating a direct reply to Message ID {}'.format(self.id))
        if self.server.routing_table.get(self.sender):
            self.server.routing_table.get(self.sender).send(
                flags.whisper, flags.whisper, *args)
        else:
            self.server._logger.debug('Requesting connection for direct reply'
                                      ' to Message ID {}'.format(self.id))
            request_hash = sha384(
                self.sender + b58encode_int(getUTC()).decode()).hexdigest()
            request_id = b58encode_int(int(request_hash, 16)).decode()
            self.server.send(request_id, self.sender, type=flags.request)
            to_send = (flags.whisper,
                       flags.whisper)  # type: Tuple[MsgPackable, ...]
            self.server.requests[request_id] = to_send + args
            self.server._logger.critical(
                "You aren't connected to the original sender. This reply is "
                "not guarunteed, but we're trying to make a connection and "
                "put the message through.")
