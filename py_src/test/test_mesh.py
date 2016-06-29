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
    propagation_validation(iters, 5100, 3, 'Plaintext')

def test_propagation_SSL(iters=3):
    propagation_validation(iters, 5200, 3, 'SSL')

def protocol_rejection_validation(iters, start_port, encryption):
    for i in xrange(iters):
        f = mesh.mesh_socket('localhost', start_port + i*2, prot=mesh.protocol('test', encryption))
        g = mesh.mesh_socket('localhost', start_port + i*2 + 1, prot=mesh.protocol('test2', encryption))
        f.connect('localhost', start_port + i*2)
        time.sleep(0.5)
        assert len(f.routing_table) == len(f.awaiting_ids) == len(g.routing_table) == len(g.awaiting_ids) == 0
        del f, g

def test_protocol_rejection_Plaintext(iters=3):
    protocol_rejection_validation(iters, 5300, 'Plaintext')

def test_protocol_rejection_SSL(iters=3):
    protocol_rejection_validation(iters, 5400, 'SSL')

def disconnect(node, method):
    if method == 'crash':
        connection = list(node.routing_table.values())[0]
        connection.sock.shutdown(socket.SHUT_RDWR)
        del connection
    elif method == 'disconnect':
        node.daemon.disconnect(list(node.routing_table.values())[0])
    else:  # pragma: no cover
        raise ValueError()

def connection_recovery_validation(iters, start_port, encryption, method):
    for i in xrange(iters):
        f = mesh.mesh_socket('localhost', start_port + i*3, prot=mesh.protocol('', encryption))
        g = mesh.mesh_socket('localhost', start_port + i*3 + 1, prot=mesh.protocol('', encryption))
        h = mesh.mesh_socket('localhost', start_port + i*3 + 2, prot=mesh.protocol('', encryption))
        f.connect('localhost', start_port + i*3 + 1)
        g.connect('localhost', start_port + i*3 + 2)
        time.sleep(0.5)
        assert len(f.routing_table) == len(g.routing_table) == len(h.routing_table) == 2, "Initial connection failed"
        disconnect(f, method)
        time.sleep(2)
        try:
            assert len(f.routing_table) == len(g.routing_table) == len(h.routing_table) == 2, "Network recovery failed"
        except:
            print("f.status: {}\n".format(f.status))
            print("g.status: {}\n".format(g.status))
            print("h.status: {}\n".format(h.status))
            raise
        del f, g, h

def test_disconnect_recovery_Plaintext(iters=3):
    connection_recovery_validation(iters, 5500, 'Plaintext', 'disconnect')

def test_disconnect_recovery_SSL(iters=3):
    connection_recovery_validation(iters, 5600, 'SSL', 'disconnect')

def test_conn_error_recovery_Plaintext(iters=3):
    connection_recovery_validation(iters, 5700, 'Plaintext', 'crash')

def test_conn_error_recovery_SSL(iters=3):
    connection_recovery_validation(iters, 5800, 'SSL', 'crash')