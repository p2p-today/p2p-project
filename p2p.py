# TODO: Write portions to also work with asyncio
# TODO: Make sure it rejects different protocols
# TODO: Investigate requester-side handshake delay
# TODO: Investigate waterfall overflow

import asyncore, asynchat, hashlib, json, multiprocessing.pool, socket, threading, time, uuid
from collections import namedtuple, deque
from operator import methodcaller

version = "0.0.E"

user_salt = str(uuid.uuid4())
sep_sequence = "\x1c\x1d\x1e\x1f"
end_sequence = sep_sequence[::-1]


base_protocol = namedtuple("protocol", ['end', 'sep', 'flag'])
base_message = namedtuple("message", ['msg', 'sender'])
headers = ["handshake", "new peers", "waterfall", "private"]


class protocol(base_protocol):
    def id(self):
        h = hashlib.sha256(''.join([str(x) for x in self] + [version]).encode())
        return h.hexdigest()


class message(base_message):
    def reply(self, *args):
        if self.sender:
            self.sender.snd('private', *args)
        else:
            return False

    def parse(self):
        return self.msg.split(self.sender.protocol.sep)


class p2p_connection(object):
    def __init__(self, addr, port, prot=protocol(end_sequence, sep_sequence, None), out_addr=None):
        self.protocol = prot
        self.incoming = ChatServer(addr, port, self, self.protocol)
        self.handlers = []
        self.daemon = threading.Thread(target=asyncore.loop)
        self.daemon.daemon = True
        self.daemon.start()
        self.queue = deque()
        if not out_addr:
            self.out_addr = (addr, port)

    def cleanup(self):
        self.handlers = list(set(self.handlers))
        removes = []
        ids = [handler.id for handler in self.handlers]
        for handler in self.handlers[::-1]:  # Check for removal in reverse order
                                             # Trusts older connections more
            # If socket is closed, connection is in multiple times, 
            # or it's been a minutes with data and no terminator, kill connection
            if not handler.connected or max(ids.count(handler.id) - 1, 0) or \
               (len(handler.buffer) and handler.time + 60 < time.time()):
                removes.append(handler)
                print(handler.id, not handler.connected, max(ids.count(handler.id) - 1, 0), \
               (len(handler.buffer) and handler.time + 60 < time.time()))
            ids = [handler.id for handler in self.handlers if handler not in removes]
        for handler in removes:
            handler.close()
            self.handlers.remove(handler)

    def handle_request(self, msg, handle):
        msg = message(msg, handle)
        packets = msg.parse()
        print("Message received: %s" % msg.parse())
        if packets[0] == "handshake":
            if packets[2] != self.protocol.id():
                handle.close()
            handle.id = packets[1]
            handle.addr = tuple(json.loads(packets[3]))
            print(handle, handle.id)
        elif packets[0] == "new peers":
            new_handlers = json.loads(packets[1])
            for handler in new_handlers:
                self.connect(*handler)
        elif packets[0] == "private":
            meta_msg = packets[1:]
            self.queue.appendleft(message(self.protocol.sep.join(meta_msg), handle))
        elif packets[0] == "waterfall":
            if self.incoming.get_id() not in packets:
                meta_msg = packets[1:]
                meta_id = meta_msg[meta_msg.index("ids:") + 1]
                try:
                    self.cleanup()
                    meta_handler = self.handlers[[h.id for h in self.handlers].index(meta_id)]
                    # If I'm connected to the original sender, I almost certainly got it
                    print("waterfall terminated")
                except:
                    self.queue.appendleft(message(self.protocol.sep.join(meta_msg[:meta_msg.index("ids:")]), None))
                    self.waterfall(msg, handle)
            else:
                print("Waterfall terminated")
        else:
            self.waterfall(msg, handle)
            self.queue.appendleft(msg)
        self.cleanup()

    def waterfall(self, msg, handler):
        return
        if msg.parse()[0] == "waterfall":
            meta_msg = msg.parse() + [handler.id, self.incoming.get_id()]
        else:
            meta_msg = ["waterfall"] + msg.parse() + ["ids:", handler.id, self.incoming.get_id()]
        print("Waterfalling %s" %str(meta_msg))
        for handler in [h for h in self.handlers if h.id != handler.id]:
            handler.snd(*meta_msg)

    def send(self, *args):
        self.cleanup()
        multiprocessing.pool.ThreadPool().map(methodcaller('snd', *args), self.handlers)

    def recv(self, quantity=1):
        if quantity != 1:
            ret_list = []
            while len(self.queue) and quantity > 0:
                ret_list.append(self.queue.pop())
                quantity -= 1
            return ret_list
        elif len(self.queue):
            return self.queue.pop()
        return None

    def connect(self, addr, port, id=None):
        self.cleanup()
        try:
            if socket.getaddrinfo(addr, port)[0] == socket.getaddrinfo(*self.incoming.addr)[0] or \
            (addr, port) in (h.addr for h in self.handlers) or \
            id and id in (h.id for h in self.handlers):
                print("Connection already established")
                print(socket.getaddrinfo(addr, port)[0] == socket.getaddrinfo(*self.incoming.addr)[0], \
                        (addr, port) in (h.addr for h in self.handlers), \
                        id and id in (h.id for h in self.handlers))
                return
            conn = socket.socket()
            conn.connect((addr, port))
            handler = ChatHandler(conn, self, self.protocol)
            handler.id = id
            handler.snd("handshake", self.incoming.get_id(), self.protocol.id(), json.dumps(self.out_addr))
            handler.snd("new peers", json.dumps([h.addr + (h.id, ) for h in self.handlers]))
            self.handlers.append(handler)
            # print("Appended ", port, addr, " to handler list: ", handler)
        except:
            print("Connection unsuccessful")


class ChatHandler(asynchat.async_chat):
    def __init__(self, sock, server, prot=protocol(end_sequence, sep_sequence, None)):
        asynchat.async_chat.__init__(self, sock=sock)
        self.protocol = prot
        self.set_terminator(self.protocol.end)
        self.buffer = []
        self.server = server
        self.id = None
        self.time = time.time()
        # print(self.protocol)
 
    def collect_incoming_data(self, data):
        self.buffer.append(data)
        self.time = time.time()

    def found_terminator(self):
        msg = ''.join(self.buffer)
        # print('Received: %s' % msg)
        self.buffer = []
        self.server.handle_request(msg, self)

    def snd(self, *args):
        msg = self.protocol.sep.join(args)
        # print(str(msg) + self.protocol.end)
        self.push(str(msg) + self.protocol.end)


class ChatServer(asyncore.dispatcher):
    def __init__(self, host, port, server, prot=protocol(end_sequence, sep_sequence, None)):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind((host, port))
        self.listen(5)
        self.server = server
        self.protocol = prot
        print(self.protocol)

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            print('Incoming connection from %s' % repr(addr))
            handler = ChatHandler(sock, self.server, self.protocol)
            handler.snd("handshake", self.get_id(), self.protocol.id(), json.dumps(self.server.out_addr))
            handler.snd("new peers", json.dumps([h.addr + (h.id, ) for h in self.server.handlers]))
            self.server.handlers.append(handler)
            # print("Appended ", handler.addr, " to handler list: ", handler)

    def get_id(self):
        info = [str(self.addr), self.__repr__(), self.protocol.id(), user_salt]
        h = hashlib.sha384(''.join(info).encode())
        return h.hexdigest()
