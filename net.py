try:
    import rsa
except:
    raise Exception("You cannot use this without the rsa module. To install this, run 'pip install rsa'.")

import socket

key_request = "Requesting key".encode('utf-8')
end_of_message = '\x03\x04\x17\x04\x03'.encode('utf-8')
size_request = "Requesting key size".encode('utf-8')


class secureSocket(object):
    def __init__(self, keysize=1024, suppress_warnings=False, *args, **kargs):
        if kargs.get('keysize'):
            keysize = kargs.pop('keysize')
        if kargs.get('suppress_warnings'):
            suppress_warnings = kargs.pop('suppress_warnings')
        if not suppress_warnings:
            if (keysize / 8) - 11 < len(end_of_message):
                raise ValueError('This key is too small to be useful')
            elif keysize > 8192:
                raise ValueError('This key is too large to be practical. Sending is easy. Generating is hard.')
        self.sock = socket.socket(*args, **kargs)
        self.pub, self.priv = rsa.newkeys(keysize)
        self.keysize = keysize
        self.msgsize = (keysize / 8) - 11
        self.key = None
        self.conn = None
        self.peer_keysize = None
        self.peer_msgsize = None

    def bind(self, ip):
        self.sock.bind(ip)

    def listen(self, i):
        self.sock.listen(i)

    def accept(self):
        self.conn, self.addr = self.sock.accept()
        self.sendKey()
        self.requestKey()

    def connect(self, ip):
        self.sock.connect(ip)
        self.conn = self.sock
        self.requestKey()
        self.sendKey()

    def close(self):
        self.conn.close()
        self.conn = None

    def settimeout(self, i):
        self.sock.settimeout(i)
        self.conn.settimeout(i)

    def send(self, msg):
        self.__send__(msg)
        self.__send__(self.sign(msg))

    def recv(self):
        msg = self.__recv__()
        try:
            self.verify(msg, self.__recv__())
        except rsa.pkcs1.VerificationError:
            raise rsa.pkcs1.VerificationError("This message could not be verified. It's possible you are experiencing a man in the middle attack")
        return msg

    def sign(self, msg, hashop='SHA-256'):
        return rsa.sign(msg, self.priv, hashop)

    def verify(self, msg, sig, key=None):
        if key is None:
            key = self.key
        return rsa.verify(msg, sig, key)

    def __send__(self, msg):
        if not isinstance(msg, type("a".encode('utf-8'))):
            msg = msg.encode('utf-8')
        x = 0
        while x < len(msg) - self.peer_msgsize:
            self.conn.sendall(rsa.encrypt(msg[x:x+self.peer_msgsize], self.key))
            x += self.peer_msgsize
        self.conn.sendall(rsa.encrypt(msg[x:], self.key))
        self.conn.sendall(rsa.encrypt(end_of_message, self.key))

    def __recv__(self):
        received = "".encode('utf-8')
        packet = ""
        try:
            while True:
                packet = self.conn.recv(self.msgsize + 11)
                packet = rsa.decrypt(packet, self.priv)
                if packet == end_of_message:
                    return received
                received += packet
        except rsa.pkcs1.DecryptionError as error:
            print("Decryption error---Content: " + str(packet))
            return received

    def requestKey(self):
        while True:
            print("Requesting key size")
            self.conn.send(size_request)
            try:
                self.peer_keysize = int(self.conn.recv(16))
                self.peer_msgsize = (self.peer_keysize / 8) - 11
                print("Requesting key")
                self.conn.send(key_request)
                key = self.conn.recv(self.peer_keysize).split(",")
                self.key = rsa.PublicKey(int(key[0]), int(key[1]))
                print("Key received")
                break
            except EOFError:
                continue
    
    def sendKey(self):
        if self.conn.recv(len(size_request)) != size_request:
            raise ValueError("Handshake has failed due to invalid request from peer")
        print("Sending key size")
        self.conn.sendall(str(self.keysize).encode("utf-8"))
        if self.conn.recv(len(key_request)) != key_request:
            raise ValueError("Handshake has failed due to invalid request from peer")
        print("Sending key")
        self.conn.sendall((str(self.pub.n) + "," + str(self.pub.e)).encode('utf-8'))
