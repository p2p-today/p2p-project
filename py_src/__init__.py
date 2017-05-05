"""A collection of tools for peer-to-peer networking

In this module:

    Constants

      * __version__:         A string containing the major, minor, and patch
                                 release number.
      * version_info:        A tuple version of the above
      * protocol_version:    A string containing the major and minor release
                                 number. This refers to the underlying protocol
      * node_policy_version: A string containing the build number associated
                                 with this version. This refers to the node
                                 and its policies.

    Classes

      * MeshSocket(addr, port, out_addr=None, debug_level=0,
                    prot=py2p.mesh.default_protocol):
          -  addr:        The address you'd like to bind to
          -  port:        The port you'd like to bind to
          -  out_addr:    Your outward-facing address, if that is different
                              from (addr, port)
          -  prot:        The py2p.base.Protocol object you'd like to use
          -  debug_level: The verbosity at which this and its associated
                              py2p.mesh.MeshDaemon prints debug information

Submodules:

    * base:        A library of common functions and classes to enable mesh
                       and the planned chord
    * mesh:        A library to deal with mesh networking
    * chord:       A planned library to deal with distributed hash tables
    * ssl_wrapper: A shortcut library to generate peer-to-peer ssl.SSLSockets
    * test:        Unit tests for this library
"""
from os import path
from random import (shuffle, randint)
from time import sleep
from warnings import warn

from typing import (Any, Callable, cast, Dict, List, Tuple, Union)
from umsgpack import (pack, unpack)

from .base import (Protocol, version, protocol_version, node_policy_version,
                   BaseConnection)
from .mesh import MeshSocket
from .sync import SyncSocket
from .chord import ChordSocket
# from .kademlia import kademlia_socket

DHTSocket = ChordSocket

__version__ = version  # type: str
version_info = tuple(map(int, __version__.split(".")))  # type: Tuple[int, ...]

__all__ = ["mesh", "chord", "kademlia", "base", "ssl_wrapper",
           "__main__"]  # type: List[str]

try:
    import cbase
    Protocol = cbase.protocol  # type: ignore
    __all__.append("cbase")
except ImportError:
    pass

_datafile = path.join(path.split(__file__)[0], 'seeders.msgpack')


def _get_database():
    # type: () -> Dict[str, Dict[bytes, List[Union[str, int]]]]
    with open(_datafile, 'rb') as database:
        database.seek(0)
        return unpack(database)


def _set_database(
        dict_,  # type: Dict[str, Dict[bytes, List[Union[str, int]]]]
        routing_table,  # type: Dict[bytes, BaseConnection]
        proto  # type: Protocol
):  # type: (...) -> None
    for id_, node in routing_table.items():
        if id_ not in dict_[proto.encryption]:
            dict_[proto.encryption][id_] = list(node.addr)

    with open(_datafile, 'wb') as database:
        database.seek(0)
        pack(dict_, database)


def bootstrap(
        socket_type,  # type: Callable
        proto,  # type: Protocol
        addr,  # type: str
        port,  # type: int
        *args,  # type: Any
        **kargs  # type: Any
):  # type: (...) -> Union[MeshSocket, SyncSocket, ChordSocket]
    ret = socket_type(
        addr, port, *args, prot=proto,
        **kargs)  # type: Union[MeshSocket, SyncSocket, ChordSocket]
    seed_protocol = Protocol('bootstrap', proto.encryption)
    if ret.protocol == seed_protocol and socket_type == DHTSocket:
        seed = cast(DHTSocket, ret)  # type: DHTSocket
    else:
        seed = DHTSocket(addr, randint(32768, 65535), prot=seed_protocol)

    dict_ = _get_database()

    @seed.once('connect')
    def on_connect(_):
        # type: (DHTSocket) -> None
        request = seed.apply_delta(
            cast(bytes, ret.protocol.id), {ret.id: ret.out_addr})
        request.catch(warn)

        @request.then
        def on_request_finished(dct):
            # type: (Any) -> None
            conns = list(dct.values())
            shuffle(conns)
            for info in conns:
                if len(ret.routing_table) > 4:
                    break
                else:
                    try:
                        ret.connect(*info)
                    except Exception:
                        continue
            if ret is not seed:
                seed.close()

        _set_database(dict_, seed.routing_table, ret.protocol)

    for seeder in dict_[ret.protocol.encryption].values():
        try:
            seed.connect(*seeder)
        except Exception:
            continue

    return ret


if __name__ == '__main__':
    from .__main__ import main
    main()
