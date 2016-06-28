import socket, sys, time
from .. import mesh

if sys.version_info[0] > 2:
    xrange = range

def propagation_validation(iters, start_port, num_nodes, encryption):
    for i in xrange(iters):
        nodes = [mesh.mesh_socket('localhost', start_port + i*num_nodes, prot=mesh.protocol('', encryption))]
        for j in xrange(1, num_nodes):
            new_node = mesh.mesh_socket('localhost', start_port + i*num_nodes + j, prot=mesh.protocol('', encryption))
            nodes[-1].connect('localhost', start_port + i*num_nodes + j)
            nodes.append(new_node)
        time.sleep(0.5)
        nodes[0].send(b"hello")
        time.sleep(num_nodes)
        print(nodes[0].id)
        print([len(n.routing_table) for n in nodes])
        for node in nodes[1:]:
            print(node.status, len(node.routing_table))
            assert b"hello" == node.recv().packets[1]
            # Failure is either no message received: AttributeError
            #                   message doesn't match: AssertionError
        del nodes[:]

def test_propagation_Plaintext(iters=3):
    propagation_validation(iters, 5555, 3, 'Plaintext')

def test_propagation_SSL(iters=3):
    propagation_validation(iters, 6600, 3, 'SSL')

def protocol_rejection_validation(iters, start_port, encryption):
    for i in xrange(iters):
        f = mesh.mesh_socket('localhost', start_port + i*2, prot=mesh.protocol('test', encryption))
        g = mesh.mesh_socket('localhost', start_port + i*2 + 1, prot=mesh.protocol('test2', encryption))
        f.connect('localhost', start_port + i*2)
        time.sleep(0.5)
        assert len(f.routing_table) == len(f.awaiting_ids) == len(g.routing_table) == len(g.awaiting_ids) == 0
        del f, g

def test_protocol_rejection_Plaintext(iters=3):
    protocol_rejection_validation(iters, 5000, 'Plaintext')

def test_protocol_rejection_SSL(iters=3):
    protocol_rejection_validation(iters, 6700, 'SSL')

def disconnect_recovery_validation(iters, start_port, encryption):
    for i in xrange(iters):
        f = mesh.mesh_socket('localhost', start_port + i*3, prot=mesh.protocol('', encryption), debug_level=6)
        g = mesh.mesh_socket('localhost', start_port + i*3 + 1, prot=mesh.protocol('', encryption), debug_level=6)
        h = mesh.mesh_socket('localhost', start_port + i*3 + 2, prot=mesh.protocol('', encryption), debug_level=6)
        f.connect('localhost', start_port + i*3 + 1)
        g.connect('localhost', start_port + i*3 + 2)
        time.sleep(0.5)
        assert len(f.routing_table) == len(g.routing_table) == len(h.routing_table) == 2
        connection = list(f.routing_table.values())[0]
        f.daemon.disconnect(connection)
        connection.sock.shutdown(socket.SHUT_RDWR)
        del connection
        time.sleep(2)
        assert len(f.routing_table) == len(g.routing_table) == len(h.routing_table) == 2
        del f, g, h

def test_disconnect_recovery_Plaintext(iters=3):
    disconnect_recovery_validation(iters, 5200, 'Plaintext')

def test_disconnect_recovery_SSL(iters=3):
    disconnect_recovery_validation(iters, 6900, 'SSL')