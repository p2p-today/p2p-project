"""A collection of tools for peer-to-peer networking

In this module:

    Constants

      * __version__: A string containing the major, minor, and patch release number.
      * version_info: A tuple version of the above
      * protocol_version: A string containing the major and minor release number. This refers to the underlying protocol
      * node_policy_version: A string containing the build number associated with this version. This refers to the node and its policies.

    Classes

      * mesh_socket(addr, port, out_addr=None, prot=py2p.mesh.default_protocol, debug_level=0): 
          -  addr: The address you'd like to bind to
          -  port: The port you'd like to bind to
          -  out_addr: Your outward-facing address, if that is different from (addr, port)
          -  prot: The py2p.base.protocol object you'd like to use
          -  debug_level: The verbosity at which this and its associated
             py2p.mesh.mesh_daemon prints debug information

Submodules:

    * base:        A library of common functions and classes to enable mesh and the planned chord
    * mesh:        A library to deal with mesh networking
    * chord:       A planned library to deal with distributed hash tables
    * ssl_wrapper: A shortcut library to generate peer-to-peer ssl.SSLSockets
    * test:        Unit tests for this library
"""

from .mesh import mesh_socket
# from .chord import chord_socket
from .base import version as __version__
from .base import protocol

version_info = tuple(map(int, __version__.split(".")))

__all__ = ["mesh", "chord", "base", "ssl_wrapper"]
