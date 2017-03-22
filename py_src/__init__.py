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

from typing import (Any, Callable, cast, Dict, List, Tuple, Union)

from .base import (Protocol, version, protocol_version, node_policy_version)
from .mesh import MeshSocket
from .sync import SyncSocket
from .chord import ChordSocket
# from .kademlia import kademlia_socket

DHTSocket = ChordSocket

__version__ = version  #type: str
version_info = tuple(map(int, __version__.split(".")))  #type: Tuple[int, ...]


__all__ = ["mesh", "chord", "kademlia", "base",
           "ssl_wrapper", "__main__"]  #type: List[str]

try:
    import cbase
    Protocol = cbase.protocol  #type: ignore
    __all__.append("cbase")
except ImportError:
    pass


def bootstrap(socket_type, proto, addr, port, *args, **kargs):
    #type: (Callable, Protocol, str, int, *Any, **Any) -> Union[MeshSocket, SyncSocket, ChordSocket]
    from os import path
    from time import sleep
    from random import (shuffle, randint)
    from warnings import warn
    from umsgpack import (pack, packb, unpack, unpackb)

    ret = socket_type(addr, port, *args, prot=proto, **kargs)  #type: Union[MeshSocket, SyncSocket, ChordSocket]
    datafile = path.join(path.split(__file__)[0], 'seeders.msgpack')
    dict_ = {}  #type: Dict[str, Dict[bytes, List[Union[str, int]]]]
    seed_protocol = Protocol('bootstrap', proto.encryption)
    if proto == seed_protocol and socket_type == DHTSocket:
        seed = cast(DHTSocket, ret)  #type: ChordSocket
    else:
        seed = DHTSocket(addr, randint(32768, 65535), prot=seed_protocol)

    with open(datafile, 'rb') as database:
        database.seek(0)
        dict_ = unpack(database)

    for seeder in dict_[proto.encryption].values():
        try:
            seed.connect(*seeder)
        except Exception:
            continue

    sleep(1)
    conn_list = seed.get(proto.id)
    for id_, node in seed.routing_table.items():
        if id_ not in dict_[proto.encryption]:
            dict_[proto.encryption][id_] = list(node.addr)

    with open(datafile, 'wb') as database:
        pack(dict_, database)


    @conn_list.then
    def then(dct):
        #type: (Dict[bytes, List[Union[str, int]]]) -> None
        conns = list(dct.values()) if isinstance(dct, dict) else []
        shuffle(conns)
        for info in conns:
            if len(ret.routing_table) > 4:
                break
            else:
                try:
                    ret.connect(*info)
                except Exception:
                    continue
        seed.apply_delta(cast(bytes, proto.id), {ret.id: ret.out_addr}).catch(warn)

    watch = then
    then.catch(warn)

    return ret


if __name__ == '__main__':
    from .__main__ import main
    main()
