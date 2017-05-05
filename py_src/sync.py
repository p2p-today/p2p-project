from __future__ import print_function
from __future__ import absolute_import

from base58 import (b58encode_int, b58decode_int)

from . import flags
from .base import (Message, BaseConnection)
from .mesh import MeshSocket
from .messages import MsgPackable
from .utils import (inherit_doc, getUTC, sanitize_packet, log_entry)

try:
    from .cbase import protocol as Protocol
except:
    from .base import Protocol

from logging import DEBUG

from typing import (cast, Any, Dict, Iterator, NamedTuple, Tuple, Union)

default_protocol = Protocol('sync', "Plaintext")  # SSL")


class metatuple(NamedTuple('meta', [('owner', bytes), ('timestamp', int)])):
    """This class is used to store metadata for a particular key"""
    __slots__ = ()


class SyncSocket(MeshSocket):
    """This class is used to sync dictionaries between programs. It extends
    :py:class:`py2p.mesh.MeshSocket`

    .. inheritance-diagram:: py2p.sync.SyncSocket

    Because of this inheritance, this can also be used as an alert network

    This also implements and optional leasing system by default. This leasing
    system means that if node A sets a key, node B cannot overwrite the value
    at that key for an hour.

    This may be turned off by adding ``leasing=False`` to the constructor.

    Added Events:

    .. raw:: html

        <div id="SyncSocket.Event 'update'"></div>

    .. py:function:: Event 'update'(conn, key, data, new_meta)

        This event is triggered when a key is updated in your synchronized
        dictionary. ``new_meta`` will be an object containing metadata of this
        change, including the time of change, and who initiated the change.

        :param py2p.sync.SyncSocket conn: A reference to this abstract socket
        :param bytes key: The key which has a new value
        :param new_data: The new value at that key
        :param py2p.sync.metatuple new_meta: Metadata on the key changer

    .. raw:: html

        <div id="SyncSocket.Event 'delete'"></div>

    .. py:function:: Event 'delete'(conn, key)

        This event is triggered when a key is deleted from your synchronized
        dictionary.

        :param py2p.sync.SyncSocket conn: A reference to this abstract socket
        :param bytes key: The key which has a new value
    """
    __slots__ = ('__leasing', 'data', 'metadata')

    @log_entry('py2p.sync.SyncSocket.__init__', DEBUG)
    @inherit_doc(MeshSocket.__init__)
    def __init__(
            self,  # type: Any
            addr,  # type: str
            port,  # type: int
            prot=default_protocol,  # type: Protocol
            out_addr=None,  # type: Union[None, Tuple[str, int]]
            debug_level=0,  # type: int
            leasing=True  # type: bool
    ):  # type: (...) -> None
        """Initialize a chord socket"""
        protocol_used = Protocol(prot[0] + str(int(leasing)), prot[1])
        self.__leasing = leasing  # type: bool
        super(SyncSocket, self).__init__(addr, port, protocol_used, out_addr,
                                         debug_level)
        self.data = cast(Dict[bytes, MsgPackable],
                         {})  # type: Dict[bytes, MsgPackable]
        self.metadata = {}  # type: Dict[bytes, metatuple]
        self.register_handler(self.__handle_store)
        self.register_handler(self.__handle_delta)

    def __check_lease(self, key, new_data, new_meta, delta=False):
        # type: (SyncSocket, bytes, MsgPackable, metatuple, bool) -> bool
        meta = self.metadata.get(key, None)
        return ((meta is None) or (meta.owner == new_meta.owner) or
                (delta and not self.__leasing) or
                (meta.timestamp < getUTC() - 3600) or
                (meta.timestamp == new_meta.timestamp and
                 meta.owner > new_meta.owner) or
                (meta.timestamp < new_meta.timestamp and not self.__leasing))

    def __store(self, key, new_data, new_meta, error=True):
        # type: (SyncSocket, bytes, MsgPackable, metatuple, bool) -> None
        """Private API method for storing data. You have permission to store
        something if:

        - The network is not enforcing leases, or
        - There is no value at that key, or
        - The lease on that key has lapsed (not been set in the last hour), or
        - You are the owner of that key

        Args:
            key:        The key you wish to store data at
            new_data:   The data you wish to store in said key
            new_meta:   The metadata associated with this storage
            error:      A boolean which says whether to raise a
                            :py:class:`KeyError` if you can't store there

        Raises:
            KeyError: If someone else has a lease at this value, and ``error``
                          is ``True``
        """
        if self.__check_lease(key, new_data, new_meta):
            if new_data is None:
                del self.data[key]
                del self.metadata[key]
                self.emit('delete', self, key)
            else:
                self.metadata[key] = new_meta
                self.data[key] = new_data
                self.emit('update', self, key, new_data, new_meta)
        elif error:
            raise KeyError("You don't have permission to change this yet")

    @inherit_doc(MeshSocket._send_peers)
    def _send_peers(self, handler):
        # type: (SyncSocket, BaseConnection) -> None
        super(SyncSocket, self)._send_peers(handler)
        for key in self:
            meta = self.metadata[key]
            handler.send(flags.whisper, flags.store, key, self[key],
                         meta.owner, meta.timestamp)

    def __handle_store(self, msg, handler):
        # type: (SyncSocket, Message, BaseConnection) -> Union[bool, None]
        """This callback is used to deal with data storage signals. Its two
        primary jobs are:

             - store data in a given key
             - delete data in a given key

             Args:
                msg:        A :py:class:`~py2p.base.Message`
                handler:    A :py:class:`~py2p.mesh.MeshConnection`

             Returns:
                Either ``True`` or ``None``
        """
        packets = msg.packets
        if packets[0] == flags.store:
            meta = metatuple(msg.sender, msg.time)
            if len(packets) == 5:
                if self.data.get(packets[1]):
                    return None
                meta = metatuple(packets[3], packets[4])
            self.__store(packets[1], packets[2], meta, error=False)
            return True
        return None

    def __setitem__(self, key, data):
        # type: (SyncSocket, bytes, MsgPackable) -> None
        """Updates the value at a given key.

        Args:
            key:    The key that you wish to update. Must be a :py:class:`str`
                        or :py:class:`bytes`-like object
            value:  The value you wish to put at this key.

        Raises:
            KeyError: If you do not have the lease for this slot. Lease is
                          given automatically for one hour if the slot is open.

            TypeError: If your key is not :py:class:`bytes` -like OR if your
                        value is not serializable. This means your value must
                        be one of the following:

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
        """
        new_meta = metatuple(self.id, getUTC())
        key = sanitize_packet(key)
        self.__store(key, data, new_meta)
        self.send(key, data, type=flags.store)

    @inherit_doc(__setitem__)
    def set(self, key, data):
        # type: (SyncSocket, bytes, MsgPackable) -> None
        self.__setitem__(key, data)

    def update(self, update_dict):
        # type: (SyncSocket, Dict[bytes, MsgPackable]) -> None
        """Equivalent to :py:meth:`dict.update`

        This calls :py:meth:`.SyncSocket.__setitem__` for each key/value
        pair in the given dictionary.

        Args:
            update_dict: A :py:class:`dict`-like object to extract key/value
                             pairs from. Key and value be a :py:class:`str`
                             or :py:class:`bytes`-like object

        Raises:
            KeyError: If you do not have the lease for this slot. Lease is
                          given automatically for one hour if the slot is open.
        """
        for key, value in update_dict.items():
            self.__setitem__(key, value)

    def __getitem__(self, key):
        # type: (SyncSocket, bytes) -> MsgPackable
        """Looks up the value at a given key.

        Args:
            key: The key that you wish to check. Must be a :py:class:`str` or
                    :py:class:`bytes`-like object

        Returns:
            The value at said key

        Raises:
            KeyError: If there is no value assigned at that key
        """
        key = sanitize_packet(key)
        return self.data[key]

    def get(self, key, ifError=None):
        # type: (SyncSocket, bytes, Any) -> MsgPackable
        """Retrieves the value at a given key.

        Args:
            key:     The key that you wish to check. Must be a :py:class:`str`
                        or :py:class:`bytes`-like object
            ifError: The value you wish to return on exception (default:
                        ``None``)

        Returns:
            The value at said key, or the value at ifError if there's an
            :py:class:`Exception`
        """
        key = sanitize_packet(key)
        return self.data.get(key, ifError)

    def __delta(self, key, delta, new_meta, error=True):
        # type: (SyncSocket, bytes, MsgPackable, metatuple, bool) -> None
        """Updates a stored mapping with the given delta. This allows for more
        graceful handling of conflicting changes

        Args:
            key:    The key you wish to apply a delta to. Must be a
                        :py:class:`str` or :py:class:`bytes`-like object
            delta:  A mapping which contains the keys you wish to update, and
                        the values you wish to store
        """
        if self.__check_lease(key, delta, new_meta, delta=True):
            self.metadata[key] = new_meta
            self.__print__(5, 'Applying a delta of {} to {}'.format(
                delta, key))
            if key not in self.data:
                self.data[key] = {}
            self.data[key].update(delta)  # type: ignore
            self.emit('update', self, key, self.data[key], new_meta)
            return
        elif error:
            raise KeyError("You don't have permission to change this yet")
        self.__print__("Did not apply a delta of {} to {}".format(delta, key))

    def apply_delta(self, key, delta):
        # type: (SyncSocket, bytes, MsgPackable) -> None
        """Updates a stored mapping with the given delta. This allows for more
        graceful handling of conflicting changes

        Args:
            key:    The key you wish to apply a delta to. Must be a
                        :py:class:`str` or :py:class:`bytes`-like object
            delta:  A mapping which contains the keys you wish to update, and
                        the values you wish to store

        Raises:
            TypeError: If the updated key does not store a mapping already
        """
        prev = self.get(key, None)
        if not isinstance(prev, dict) and prev is not None:
            raise TypeError("Cannot apply delta to a non-mapping")
        else:
            new_meta = metatuple(self.id, getUTC())
            key = sanitize_packet(key)
            self.__delta(key, delta, new_meta)
            self.send(key, delta, type=flags.delta)

    def __handle_delta(self, msg, handler):
        # type: (SyncSocket, Message, BaseConnection) -> Union[bool, None]
        """This callback is used to deal with delta storage signals. Its
        primary job is:

             - update the mapping in a given key

             Args:
                msg:        A :py:class:`~py2p.base.Message`
                handler:    A :py:class:`~py2p.mesh.MeshConnection`

             Returns:
                Either ``True`` or ``None``
        """
        packets = msg.packets
        if packets[0] == flags.delta:
            meta = metatuple(msg.sender, msg.time)
            self.__delta(packets[1], packets[2], meta, error=False)
            return True
        return None

    def __len__(self):
        # type: (SyncSocket) -> int
        return len(self.data)

    def __delitem__(self, key):
        # type: (SyncSocket, bytes) -> None
        self[key] = None

    def keys(self):
        # type: (SyncSocket) -> Iterator[bytes]
        """
        Returns:
            an iterator of the underlying :py:class:`dict` s keys
        """
        return iter(self.data)

    @inherit_doc(keys)
    def __iter__(self):
        # type: (SyncSocket) -> Iterator[bytes]
        return self.keys()

    def values(self):
        # type: (SyncSocket) -> Iterator[MsgPackable]
        """
        Returns:
            an iterator of the underlying :py:class:`dict` s values
        """
        return (self[key] for key in self.keys())

    def items(self):
        # type: (SyncSocket) -> Iterator[Tuple[bytes, MsgPackable]]
        """
        Returns:
            an iterator of the underlying :py:class:`dict` s items
        """
        return ((key, self[key]) for key in self.keys())

    def pop(self, key, *args):
        # type: (SyncSocket, bytes, *Any) -> MsgPackable
        """Returns a value, with the side effect of deleting that association

        Args:
            Key:        The key you wish to look up. Must be a :py:class:`str`
                            or :py:class:`bytes`-like object
            ifError:    The value you wish to return on Exception
                            (default: raise an Exception)

        Returns:
            The value of the supplied key, or ``ifError``

        Raises:
            KeyError:       If the key does not have an associated value
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
        # type: (SyncSocket) -> Tuple[bytes, MsgPackable]
        """Returns an association, with the side effect of deleting that
        association

        Returns:
            An arbitrary association
        """
        key = next(self.keys())
        return (key, self.pop(key))

    def copy(self):
        # type: (SyncSocket) -> Dict[bytes, MsgPackable]
        """Returns a :py:class:`dict` copy of this synchronized hash table"""
        return self.data.copy()
