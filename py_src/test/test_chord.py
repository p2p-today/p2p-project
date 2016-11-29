from __future__ import print_function
from __future__ import absolute_import

import random
import sys
import time
import uuid

import pytest

from .. import chord
from .test_mesh import close_all_nodes

if sys.version_info >= (3, ):
    xrange = range


# def protocol_rejection_validation(iters, start_port, encryption, k=4,
#                                   name='test'):
#     for i in xrange(iters):
#         print("----------------------Test start----------------------")
#         f = chord.chord_socket('localhost', start_port + i*2, k=4,
#                                prot=chord.protocol('test', encryption),
#                                debug_level=5)
#         g = chord.chord_socket('localhost', start_port + i*2 + 1, k=k,
#                                prot=chord.protocol(name, encryption),
#                                debug_level=5)
#         print("----------------------Test event----------------------")
#         g.connect('localhost', start_port + i*2)
#         g.join()
#         time.sleep(1)
#         print("----------------------Test ended----------------------")
#         assert (len(f.routing_table) == len(f.awaiting_ids) ==
#                 len(g.routing_table) == len(g.awaiting_ids) == 0)
#         print(f.status)
#         print(g.status)
#         close_all_nodes([f, g])


# def test_protocol_rejection_Plaintext(iters=3):
#     protocol_rejection_validation(iters, 6000, 'Plaintext', name='test2')


# def test_protocol_rejection_SSL(iters=3):
#     protocol_rejection_validation(iters, 6100, 'SSL', name='test2')


# def test_size_rejection_Plaintext(iters=3):
#     protocol_rejection_validation(iters, 6200, 'Plaintext', k=5)


# def test_size_rejection_SSL(iters=3):
#     protocol_rejection_validation(iters, 6300, 'SSL', k=3)


# def gen_connected_list(start_port, encryption, k=2):
#     nodes = [
#         chord.chord_socket('localhost', start_port + x, k=k, debug_level=0)
#         for x in xrange(2**k)]
#
#     for index, node in enumerate(nodes):
#         node.id_10 = index
#         node.id = chord.to_base_58(index)
#         node.connect(*nodes[(index - 1) % len(nodes)].addr)
#         time.sleep(0.1)
#
#     for node in nodes:
#         node.join()
#
#     time.sleep(3 * k)
#
#     for node in nodes:
#         print("%s:" % node.id)
#         print(node.status)
#         for key in node.routing_table:
#             print("entry %i: %s" % (key, node.routing_table[key].id))
#
#     return nodes


# def routing_validation(iters, start_port, encryption, k=3):
#     for i in xrange(iters):
#         nodes = gen_connected_list(start_port + i * 2**k, encryption, k)
#
#         assertion_list = list(
#             map(len, (node.routing_table for node in nodes)))
#         print(assertion_list)
#         close_all_nodes(nodes)
#         assert min(assertion_list) >= 1


# def test_routing_Plaintext(iters=3):
#     routing_validation(iters, 6400, 'Plaintext', k=3)


# def test_routing_SSL(iters=1):
#     routing_validation(iters, 6500, 'SSL', k=3)


# def storage_validation(iters, start_port, encryption, k=2):
#     for i in xrange(iters):
#         nodes = gen_connected_list(start_port + i * 2**k, encryption, k)

#         test_key = str(uuid.uuid4())
#         test_data = str(uuid.uuid4())

#         nodes[0][test_key] = test_data

#         time.sleep(2*k)

#         for meth in chord.hashes:
#             assert any((bool(node.data[meth]) for node in nodes))

#         close_all_nodes(nodes)


# def test_storage_Plaintext(iters=1):
#     storage_validation(iters, 6600, 'Plaintext')


# def test_storage_SSL(iters=1):
#     storage_validation(iters, 6700, 'SSL')


# def retrieval_validation(iters, start_port, encryption, k=2):
#     for i in xrange(iters):
#         nodes = gen_connected_list(start_port + i * 2**k, encryption, k)

#         test_key = str(uuid.uuid4())
#         test_data = str(uuid.uuid4())

#         nodes[0][test_key] = test_data

#         time.sleep(2*k)

#         for node in nodes:
#             assert node[test_key] == test_data
#             with pytest.raises(KeyError):
#                 node[test_data]


# def test_retrieval_Plaintext(iters=1):
#     retrieval_validation(iters, 6800, 'Plaintext')


# def test_retrieval_SSL(iters=1):
#     retrieval_validation(iters, 6900, 'SSL')
