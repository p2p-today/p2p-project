from __future__ import print_function

import hashlib
import json
import select
import socket
import struct
import sys
import traceback
import warnings

from .base import (
    flags, compression, to_base_58, from_base_58, protocol, base_connection,
    message, base_daemon, base_socket, pathfinding_message, json_compressions)
from .utils import (
    getUTC, get_socket, intersect, file_dict, awaiting_value, most_common)

default_protocol = protocol('chord', "Plaintext")  # SSL")
hashes = ['sha1', 'sha224', 'sha256', 'sha384', 'sha512']

if sys.version_info >= (3,):
    xrange = range


def distance(a, b):
    raise NotImplementedError


class kademlia_connection(base_connection):
    pass


class kademlia_daemon(base_daemon):
    pass


class kademlia_socket(base_socket):
    pass
