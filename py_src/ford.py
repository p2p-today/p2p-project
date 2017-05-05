from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import sys

from logging import DEBUG
from random import choice
from socket import timeout as TimeoutException
from time import sleep
from traceback import format_exc

from async_promises import Promise
from typing import (cast, Any, Dict, List, Tuple, Union)

try:
    from .cbase import protocol as Protocol
except:
    from .base import Protocol

from . import flags
from .base import (BaseConnection, Message)
from .mesh import (MeshConnection, MeshDaemon, MeshSocket)
from .messages import MsgPackable
from .utils import (inherit_doc, log_entry)

max_outgoing = 4
default_protocol = Protocol('ford', "Plaintext")  # SSL")


class FordConnection(MeshConnection):
    pass


class FordDaemon(MeshDaemon):
    @log_entry('py2p.ford.FordDaemon.__init__', DEBUG)
    @inherit_doc(MeshDaemon.__init__)
    def __init__(self, *args, **kwargs):
        # type: (Any, *Any, **Any) -> None
        super(FordDaemon, self).__init__(*args, **kwargs)
        self.conn_type = FordConnection

    @inherit_doc(MeshDaemon.handle_accept)
    def handle_accept(self):
        # type: (FordDaemon) -> FordConnection
        handler = super(FordDaemon, self).handle_accept()
        self.server.send_paths(handler)
        return cast(FordConnection, handler)


class FordSocket(MeshSocket):
    __slots__ = ('routes', )

    @log_entry('py2p.ford.FordSocket.__init__', DEBUG)
    @inherit_doc(MeshSocket.__init__)
    def __init__(
            self,  # type: Any
            addr,  # type: str
            port,  # type: int
            prot=default_protocol,  # type: Protocol
            out_addr=None,  # type: Union[None, Tuple[str, int]]
            debug_level=0  # type: int
    ):  # type: (...) -> None
        """Initialize a chord socket"""
        if not hasattr(self, 'daemon'):
            self.daemon = 'ford reserved'
        super(FordSocket, self).__init__(addr, port, prot, out_addr,
                                         debug_level)
        if self.daemon == 'ford reserved':
            self.daemon = FordDaemon(addr, port, self)
        self.routes = {self.id: []}  # type: Dict[bytes, List[bytes]]
        self.register_handler(self.__handle_new_path)
        self.register_handler(self.__handle_del_path)
        self.register_handler(self.__handle_forward)

    @inherit_doc(MeshSocket.disconnect)
    def disconnect(self, handler):
        # type: (MeshSocket, MeshConnection) -> None
        _id = handler.id
        super(FordSocket, self).disconnect(handler)
        if _id in self.routes:
            to_send = cast(MsgPackable, {_id: self.routes[_id]})
            del self.routes[_id]
            for conn in tuple(self.routing_table.values()):
                conn.send(flags.whisper, flags.revoke_paths, to_send)

    def __handle_new_path(self, msg, handler):
        # type: (FordSocket, Message, BaseConnection) -> Union[bool, None]
        """This callback is used to deal with ford paths.
        Its primary job is:

        - Accept incoming path changes

        Args:
            msg:        A :py:class:`~py2p.base.Message`
            handler:    A :py:class:`~py2p.ford.FordConnection`

        Returns:
            Either ``True`` or ``None``
        """
        packets = msg.packets
        if packets[0] == flags.new_paths:
            respond = False
            for dest, route in packets[1].items():
                if dest not in self.routes or len(route) < len(
                        self.routes[dest]):
                    self.routes[dest] = route
                    respond = True
            if respond:
                for handler in self.routing_table.values():
                    self.send_paths(cast(FordConnection, handler))
            return True
        return None

    def __handle_del_path(self, msg, handler):
        # type: (FordSocket, Message, BaseConnection) -> Union[bool, None]
        """This callback is used to deal with ford paths.
        Its primary job is:

        - Accept incoming path changes

        Args:
            msg:        A :py:class:`~py2p.base.Message`
            handler:    A :py:class:`~py2p.ford.FordConnection`

        Returns:
            Either ``True`` or ``None``
        """
        packets = msg.packets
        if packets[0] == flags.revoke_paths:
            respond = False
            for dest, route in packets[1].items():
                if dest in self.routes and route == self.routes[dest]:
                    del self.routes[dest]
                    respond = True
            if respond:
                for handler in self.routing_table.values():
                    self.send_paths(handler)
            return True
        return None

    def send_paths(self, handler):
        # type: (FordSocket, BaseConnection) -> None
        to_send = cast(MsgPackable,
                       dict((dest, [self.id] + path)
                            for dest, path in self.routes.items()))
        handler.send(flags.whisper, flags.new_paths, to_send)

    def __handle_forward(self, msg, handler):
        # type: (FordSocket, Message, BaseConnection) -> Union[bool, None]
        """This callback is used to deal with ford paths.
        Its primary job is:

        - Accept incoming path changes

        Args:
            msg:        A :py:class:`~py2p.base.Message`
            handler:    A :py:class:`~py2p.ford.FordConnection`

        Returns:
            Either ``True`` or ``None``
        """
        packets = msg.packets
        if packets[0] == flags.forward:
            dest = packets[1]
            if dest in self.routes:
                path = self.routes[dest]
                imsg = msg.msg
                if path[0] == dest:
                    imsg.payload = packets[2:]
                self.routing_table[path[0]].send_InternalMessage(imsg)
            return True
        return None

    def sendTo(self, dest, *args, **kargs):
        # type: (MeshSocket, bytes, *MsgPackable, **MsgPackable) -> None
        """This sends a message to all of your peers. If you use default
        values it will send it to everyone on the network

        Args:
            dest:       The node ID you wish to send to
            *args:      A list of objects you want your peers to receive
            **kargs:    There are two keywords available:
            flag:       A string or bytes-like object which defines your flag.
                            In other words, this defines packet 0.
            type:       A string or bytes-like object which defines your
                            message type. Changing this from default can have
                            adverse effects.

        Raises:

            KeyError:  If a path cannot be found to your desired destination

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
        send_type = kargs.pop('type', flags.whisper)
        main_flag = kargs.pop('flag', flags.whisper)
        path = self.routes[dest]
        if path[0] != dest:
            self.routing_table[path[0]].send(main_flag, flags.forward, dest,
                                             send_type, *args)
        else:
            self.routing_table[path[0]].send(main_flag, send_type, *args)
