# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import absolute_import

from time import sleep
from sys import version_info

from pytest import (mark, raises)

from .. import (flags, sync)

from .test_mesh import close_all_nodes

if version_info >= (3, ):
    xrange = range


def storage_validation(iters, start_port, num_nodes, encryption, leasing):
    # type: (int, int, int, str, bool) -> None
    for i in xrange(iters):
        print("----------------------Test start----------------------")
        nodes = [
            sync.SyncSocket(
                'localhost',
                start_port + i * num_nodes,
                prot=sync.Protocol('', encryption),
                debug_level=5,
                leasing=leasing)
        ]
        nodes[0].set('store', b"store")
        for j in xrange(1, num_nodes):
            new_node = sync.SyncSocket(
                'localhost',
                start_port + i * num_nodes + j,
                prot=sync.Protocol('', encryption),
                debug_level=5,
                leasing=leasing)
            nodes[-1].connect('localhost', start_port + i * num_nodes + j)
            nodes.append(new_node)
            sleep(0.5)
        print("----------------------Test event----------------------")
        nodes[0]['test'] = b"hello"
        nodes[1][u'测试'] = u'成功'
        nodes[0].update({'array': [1, 2, 3, 4, 5, 6, 7, 8, 9], 'number': 256})
        sleep(num_nodes)
        print("----------------------Test ended----------------------")
        print(nodes[0].id)
        print([len(n.routing_table) for n in nodes])
        for node in nodes[1:]:
            print(node.status, len(node.routing_table))
            assert b"store" == node['store']
            assert b"hello" == node['test']
            assert u'成功' == node[u'测试']
            assert 256 == node['number']
            assert [1, 2, 3, 4, 5, 6, 7, 8, 9] == node['array']
            if leasing:
                with raises(KeyError):
                    node['test'] = b"This shouldn't work"
            with raises(KeyError):
                node['test2']

        close_all_nodes(nodes)


@mark.run(order=4)
def test_storage_leasing_Plaintext(iters=2):
    # type: (int) -> None
    storage_validation(iters, 7100, 3, 'Plaintext', True)


@mark.run(order=4)
def test_storage_leasing_SSL(iters=2):
    # type: (int) -> None
    storage_validation(iters, 7200, 3, 'SSL', True)


@mark.run(order=4)
def test_storage_Plaintext(iters=2):
    # type: (int) -> None
    storage_validation(iters, 7300, 3, 'Plaintext', False)


@mark.run(order=4)
def test_storage_SSL(iters=2):
    # type: (int) -> None
    storage_validation(iters, 7400, 3, 'SSL', False)


def delta_validation(iters, start_port, num_nodes, encryption, leasing):
    # type: (int, int, int, str, bool) -> None
    for i in xrange(iters):
        print("----------------------Test start----------------------")
        nodes = [
            sync.SyncSocket(
                'localhost',
                start_port + i * num_nodes,
                prot=sync.Protocol('', encryption),
                debug_level=5,
                leasing=leasing)
        ]
        for j in xrange(1, num_nodes):
            new_node = sync.SyncSocket(
                'localhost',
                start_port + i * num_nodes + j,
                prot=sync.Protocol('', encryption),
                debug_level=5,
                leasing=leasing)
            nodes[-1].connect('localhost', start_port + i * num_nodes + j)
            nodes.append(new_node)
            sleep(0.5)
        print("----------------------Test event----------------------")
        nodes[0].apply_delta('store', {'seven': 7})
        nodes[1].apply_delta(
            'store', {'array': [1, 2, 3, 4, 5, 6, 7, 8, 9],
                      'number': 256})
        nodes[2].apply_delta('store', {'three': {'three': 'three'}})
        sleep(num_nodes)
        print("----------------------Test ended----------------------")
        print(nodes[0].id)
        print([len(n.routing_table) for n in nodes])
        for node in nodes:
            print(node.status, len(node.routing_table))
            assert node['store'] == {
                'seven': 7,
                'three': {
                    'three': 'three'
                },
                'array': [1, 2, 3, 4, 5, 6, 7, 8, 9],
                'number': 256
            }

        close_all_nodes(nodes)


@mark.run(order=4)
def test_delta_Plaintext(iters=2):
    # type: (int) -> None
    delta_validation(iters, 7500, 3, 'Plaintext', False)


@mark.run(order=4)
def test_delta_SSL(iters=2):
    # type: (int) -> None
    delta_validation(iters, 7600, 3, 'SSL', False)
