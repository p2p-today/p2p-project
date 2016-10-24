from __future__ import print_function
from __future__ import absolute_import

import sys
import time

import pytest

from .. import sync
from ..base import flags

from .test_mesh import close_all_nodes

if sys.version_info >= (3, ):
    xrange = range


def storage_validation(iters, start_port, num_nodes, encryption):
    for i in xrange(iters):
        print("----------------------Test start----------------------")
        nodes = [sync.sync_socket('localhost', start_port + i*num_nodes,
                                  prot=sync.protocol('', encryption), debug_level=5)]
        nodes[0]['store'] = b"store"
        for j in xrange(1, num_nodes):
            new_node = sync.sync_socket('localhost', start_port + i*num_nodes + j,
                                        prot=sync.protocol('', encryption), debug_level=5)
            nodes[-1].connect('localhost', start_port + i*num_nodes + j)
            nodes.append(new_node)
            time.sleep(0.5)
        print("----------------------Test event----------------------")
        nodes[0]['test'] = b"hello"
        time.sleep(num_nodes)
        print("----------------------Test ended----------------------")
        print(nodes[0].id)
        print([len(n.routing_table) for n in nodes])
        for node in nodes[1:]:
            print(node.status, len(node.routing_table))
            assert b"store" == node['store']
            assert b"hello" == node['test']
            with pytest.raises(KeyError):
                node['test'] = b"This shouldn't work"
            with pytest.raises(KeyError):
                node['test2']

        close_all_nodes(nodes)


def test_storage_Plaintext(iters=3):
    storage_validation(iters, 7100, 3, 'Plaintext')


def test_storage_SSL(iters=3):
    storage_validation(iters, 7200, 3, 'SSL')