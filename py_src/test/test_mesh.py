import sys, time
from .. import mesh

if sys.version_info[0] > 2:
    xrange = range

def test_propagation(iters=3):
    start_port = 5555
    num_nodes = 3
    for i in xrange(iters):
        nodes = []
        nodes.append(mesh.mesh_socket('localhost', start_port + i*num_nodes))
        for j in xrange(1, num_nodes):
            new_node = mesh.mesh_socket('localhost', start_port + i*num_nodes + j)
            nodes[-1].connect('localhost', start_port + i*num_nodes + j)
            nodes.append(new_node)
        time.sleep(0.5)
        nodes[0].send(b"hello")
        time.sleep(0.5)
        print(nodes[0].id)
        for node in nodes[1:]:
            print(node.status)
            assert b"hello" == node.recv().packets[1]
            # Failure is either no message received: AttributeError
            #                   message doesn't match: AssertionError
        del nodes[:]