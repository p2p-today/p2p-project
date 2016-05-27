try:
    import rsa
    uses_RSA = True
    decryption_error = rsa.pkcs1.DecryptionError
except:
    try:
        from Crypto.PublicKey import RSA
        uses_RSA = False
        import warnings
        warnings.warn('Using the PyCrypto module is not recommended. It makes communication with non-standard keylengths inconsistent. Please run \'pip install rsa\' to use this more effectively.', ImportWarning, stacklevel=2)

        class DecryptionError(Exception): pass

        decryption_error = DecryptionError("Decryption failed")

    except:
        raise ImportError("You cannot use this without the rsa or PyCrypto module. To install this, run 'pip install rsa'. The rsa module is recommended because, while it's slower, it's much more flexible, and ensures communication with other secureSockets.")

import socket

key_request = "Requesting key".encode('utf-8')
size_request = "Requesting key size".encode('utf-8')
end_of_message = '\x03\x04\x17\x04\x03'.encode('utf-8')  # For the ASCII nerds, that's:
                                                         # End of text, End of tx, End of tx block, End of tx, End of text

if uses_RSA:
    """If we're using the rsa module, just map these methods from rsa"""
    newkeys   = rsa.newkeys
    encrypt   = rsa.encrypt
    decrypt   = rsa.decrypt
    sign      = rsa.sign
    verify    = rsa.verify
    PublicKey = rsa.PublicKey
else:

    from Crypto.Hash import MD5, SHA, SHA256, SHA384, SHA512
    """The following table is to make choosing a hash easier"""
    hashtable = {'MD5': MD5,
                 'SHA-1': SHA,
                 'SHA-256': SHA256,
                 'SHA-384': SHA384,
                 'SHA-512': SHA512}


    def newkeys(size):
        """Wrapper for PyCrypto RSA key generation, to better match rsa's method"""
        from Crypto import Random
        from Crypto.PublicKey import RSA
        random_generator = Random.new().read
        key = RSA.generate(size, random_generator)
        return key.publickey(), key

    
    def encrypt(msg, key):
        """Wrapper for PyCrypto RSA encryption method, to better match rsa's method"""
        from Crypto.Cipher.PKCS1_v1_5 import PKCS115_Cipher
        return PKCS115_Cipher(key).encrypt(msg)


    def decrypt(msg, key):
        """Wrapper for PyCrypto RSA decryption method, to better match rsa's method"""
        from Crypto.Cipher.PKCS1_v1_5 import PKCS115_Cipher
        return PKCS115_Cipher(key).decrypt(msg, decryption_error)


    def sign(msg, key, hashop):
        """Wrapper for PyCrypto RSA signing method, to better match rsa's method"""
        from Crypto.Signature import PKCS1_v1_5
        hsh = hashtable.get(hashop).new()
        hsh.update(msg)
        signer = PKCS1_v1_5.PKCS115_SigScheme(key)
        return signer.sign(hsh)


    def verify(msg, sig, key):
        """Wrapper for PyCrypto RSA signature verification, to better match rsa's method"""
        from Crypto.Signature import PKCS1_v1_5
        for hashop in ['SHA-256', 'MD5', 'SHA-1', 'SHA-384', 'SHA-512']:
            hsh = hashtable.get(hashop).new()
            hsh.update(msg)
            check = PKCS1_v1_5.PKCS115_SigScheme(key)
            res = check.verify(hsh, sig)
            if res:
                break
        return res
        

    def PublicKey(n, e):
        """Wrapper for PyCrypto RSA key constructor, to better match rsa's method"""
        return RSA.construct((long(n), long(e)))


class secureSocket(socket.socket):
    """An RSA encrypted and secured socket. Requires either the rsa or PyCrypto module"""
    def __init__(self, sock_family=socket.AF_INET, sock_type=socket.SOCK_STREAM, proto=0, fileno=None, keysize=1024, suppress_warnings=False):
        super(secureSocket, self).__init__(sock_family, sock_type, proto, fileno)
        if not suppress_warnings:
            if uses_RSA and keysize < 1024:
                import warnings
                warnings.warn('Using the rsa module with a <1024 key length will make communication with PyCrypto implementations inconsistent', RuntimeWarning, stacklevel=2)
            if keysize < 354 or (keysize / 8) - 11 < len(end_of_message):
                raise ValueError('This key is too small to be useful')
            elif keysize > 8192:
                raise ValueError('This key is too large to be practical. Sending is easy. Generating is hard.')
        from multiprocessing.pool import ThreadPool as Pool
        self.key_async = Pool().map_async(newkeys, [keysize])  # Gen in background to reduce block
        self.pub, self.priv = None, None    # Temporarily set to None so they can generate in background
        self.keysize = keysize
        self.msgsize = (keysize // 8) - 11
        self.key = None
        self.peer_keysize = None
        self.peer_msgsize = None
        self.buffer = "".encode()
        self.key_exchange = None
        from functools import partial
        import sys
        if sys.version_info[0] < 3:
            self.__recv = self._sock.recv
        else:
            self.__recv = super(secureSocket, self).recv
        self.send = partial(secureSocket.send, self)
        self.sendall = self.send
        self.recv = partial(secureSocket.recv, self)
        self.dup = partial(secureSocket.dup, self)

    def dup(self, conn=None):
        """Duplicates this secureSocket, with all key information, connected to the same peer.
        Blocks if keys are being exchanged."""
        import sys
        if sys.version_info[0] < 3:
            sock = secureSocket(self.family, self.type)
            if not conn:
                sock._sock = socket.socket.dup(self)
            else:
                sock._sock = conn
        else:
            if not conn:
                sock = super(secureSocket, self).dup()
            else:
                import _socket
                sock = secureSocket()
                fd = _socket.dup(conn.fileno())
                super(secureSocket, sock).__init__(conn.family, conn.type, conn.proto, fd)
        sock.pub, sock.priv = self.pub, self.priv
        sock.keysize = self.keysize
        sock.msgsize = self.msgsize
        if self.key_exchange:
            self.key_exchange.join()
            self.key_exchange = None
        sock.key = self.key
        sock.peer_keysize = self.peer_keysize
        sock.peer_msgsize = self.peer_msgsize
        sock.buffer = self.buffer
        from functools import partial
        import sys
        if sys.version_info[0] < 3:
            sock.__recv = sock._sock.recv
        else:
            sock.__recv == super(secureSocket, self).recv
        sock.send = partial(secureSocket.send, sock)
        sock.sendall = sock.send
        sock.recv = partial(secureSocket.recv, sock)
        sock.dup = partial(secureSocket.dup, sock)
        return sock

    def mapKey(self):
        """Deals with the asyncronous generation of keys"""
        if self.pub is None:
            print("Waiting to grab key")
            self.pub, self.priv = self.key_async.get()[0]
            del self.key_async

    def accept(self):
        """Accepts an incoming connection.
        Like a native socket, it returns a copy of the socket and the connected address."""
        conn, addr = super(secureSocket, self).accept()
        sock = self.dup(conn=conn)
        #sock.sendKey()
        #sock.requestKey()
        from threading import Thread
        sock.key_exchange = Thread(target=sock.handshake, args=(1,))
        sock.key_exchange.daemon = True
        sock.key_exchange.start()
        return sock, addr

    def connect(self, ip):
        """Connects to another secureSocket"""
        super(secureSocket, self).connect(ip)
        #self.requestKey()
        #self.sendKey()
        from threading import Thread
        self.key_exchange = Thread(target=self.handshake, args=(0,))
        self.key_exchange.daemon = True
        self.key_exchange.start()

    def close(self):
        """Closes your connection to another socket, then cleans up metadata"""
        super(secureSocket, self).close()
        self.key = None
        self.peer_keysize = None
        self.peer_msgsize = None

    def send(self, msg):
        """Sends an encrypted copy of your message, and an encrypted signature.
        Blocks if keys are being exchanged."""
        if self.key_exchange:
            self.key_exchange.join()
            self.key_exchange = None
        elif self.peer_msgsize == None:
            raise socket.error("You aren't connected to anyone")
        self.__send__(msg)
        self.__send__(self.sign(msg))

    def recv(self, size=None):
        """Receives and decrypts a message, then verifies it against the attached signature.
        Blocks if keys are being exchanged, regardless of timeout settings."""
        if self.key_exchange:
            self.key_exchange.join()
            self.key_exchange = None
        if self.buffer != "".encode():
            if size:
                msg = self.buffer[:size]
                self.buffer = self.buffer[size:]
            else:
                msg = self.buffer
                self.buffer = "".encode()
            return msg
        msg = self.__recv__()
        sig = self.__recv__()
        if not msg or not sig:
            return ''
        if uses_RSA:
            try:
                self.verify(msg, sig)
            except rsa.pkcs1.VerificationError as error:
                print(msg)
        else:
            self.verify(msg, sig)
        if not size:
            return msg
        else:
            self.buffer += msg
            ret = self.buffer[:size]
            self.buffer = self.buffer[size:]
            return ret

    def sign(self, msg, hashop='best'):
        """Signs a message with a given hash, or self-determined one. If using PyCrypto, always defaults to SHA-512"""
        try:
            msg = msg.encode()
        except:
            pass
        self.mapKey()
        if hashop != 'best':
            return sign(msg, self.priv, hashop)
        elif self.keysize >= 745:
            return sign(msg, self.priv, 'SHA-512')
        elif self.keysize >= 618:
            return sign(msg, self.priv, 'SHA-384')
        elif self.keysize >= 490:
            return sign(msg, self.priv, 'SHA-256')
        elif self.keysize >= 362:
            return sign(msg, self.priv, 'SHA-1')
        else:   # if self.keysize < 354: raises OverflowError
            return sign(msg, self.priv, 'MD5')

    def verify(self, msg, sig, key=None):
        """Verifies a message with a given key (Default: your peer's)"""
        if key is None:
            key = self.key
        return verify(msg, sig, key)

    def __send__(self, msg):
        """Base method for sending a message. Encrypts and sends. Use send instead."""
        if not isinstance(msg, type("a".encode('utf-8'))):
            msg = str(msg).encode('utf-8')
        x = 0
        while x < len(msg) - self.peer_msgsize:
            super(secureSocket, self).sendall(encrypt(msg[x:x+self.peer_msgsize], self.key))
            x += self.peer_msgsize
        super(secureSocket, self).sendall(encrypt(msg[x:], self.key))
        super(secureSocket, self).sendall(encrypt(end_of_message, self.key))

    def __recv__(self):
        """Base method for receiving a message. Receives and decrypts. Use recv instead."""
        received = b''
        packet = b''
        try:
            while True:
                packet = self.__recv(self.msgsize + 11)
                packet = decrypt(packet, self.priv)
                if packet == end_of_message:
                    return received
                received += packet
        except decryption_error:
            print("Decryption error---Content: " + repr(packet))
            raise decryption_error
        except ValueError as error:
            if error.args[0] in ["invalid literal for int() with base 16: ''", "invalid literal for int() with base 16: b''"]:
                return 0
            else:
                raise error

    def requestKey(self):
        """Requests your peer's key over plaintext"""
        while True:
            print("Requesting key size")
            super(secureSocket, self).sendall(size_request)
            try:
                self.peer_keysize = int(self.__recv(16))
                if not uses_RSA and self.peer_keysize < 1024:
                    import warnings
                    warnings.warn('Your peer is using a small key length. Because you\'re using PyCrypto, sending may silently fail, as on some keys PyCrypto will not construct it correctly. To fix this, please run \'pip install rsa\'.', RuntimeWarning, stacklevel=2)
                self.peer_msgsize = (self.peer_keysize // 8) - 11
                print("Requesting key")
                super(secureSocket, self).sendall(key_request)
                keys = self.__recv(self.peer_keysize)
                if isinstance(keys, type(b'')):
                    keys = keys.decode()
                key = keys.split(",")
                self.key = PublicKey(int(key[0]), int(key[1]))
                print("Key received")
                break
            except EOFError:
                continue
    
    def sendKey(self):
        """Sends your key over plaintext"""
        req = self.__recv(len(size_request))
        if req != size_request:
            raise ValueError("Handshake has failed due to invalid request from peer: %s" % req)
        print("Sending key size")
        super(secureSocket, self).sendall(str(self.keysize).encode("utf-8"))
        req = self.__recv(len(key_request))
        if req != key_request:
            raise ValueError("Handshake has failed due to invalid request from peer")
        self.mapKey()
        print("Sending key")
        super(secureSocket, self).sendall((str(self.pub.n) + "," + str(self.pub.e)).encode('utf-8'))

    def handshake(self, order):
        """Wrapper for sendKey and requestKey"""
        t = self.gettimeout()
        super(secureSocket, self).settimeout(None)
        if order:
            self.sendKey()
        self.requestKey()
        if not order:
            self.sendKey()
        super(secureSocket, self).settimeout(t)

    def settimeout(self, timeout):
        """Sets the timeout for the socket. Blocks if keys are being exchanged."""
        if self.key_exchange:
            self.key_exchange.join()
            self.key_exchange = None
        super(secureSocket, self).settimeout(timeout)
