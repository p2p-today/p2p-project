from __future__ import print_function
import warnings, socket, sys
from threading import Thread
from functools import partial
from multiprocessing.pool import ThreadPool as Pool

key_request = "Requesting key".encode('utf-8')
size_request = "Requesting key size".encode('utf-8')
end_of_message = '\x03\x04\x17\x04\x03'.encode('utf-8')  # For the ASCII nerds, that's:
                                                         # End of text, End of tx, End of tx block, End of tx, End of text

# This next section is to set up for different RSA implementations. Currently supported are rsa and PyCrypto. I plan to add cryptography in the future.

try:
    import rsa
    uses_RSA = True
    decryption_error = rsa.pkcs1.DecryptionError
    verification_error = rsa.pkcs1.VerificationError
    newkeys    = rsa.newkeys
    encrypt    = rsa.encrypt
    decrypt    = rsa.decrypt
    sign       = rsa.sign
    verify     = rsa.verify
    public_key = rsa.PublicKey
except ImportError:
    try:
        from Crypto.Hash import SHA512, SHA384, SHA256, SHA, MD5
        from Crypto.Cipher.PKCS1_v1_5 import PKCS115_Cipher
        from Crypto.Signature import PKCS1_v1_5
        from Crypto.PublicKey import RSA
        from Crypto import Random

        uses_RSA = False
        warnings.warn('Using the PyCrypto module is not recommended. It makes communication with smaller-than-standard keylengths inconsistent. Please run \'pip install rsa\' to use this more effectively.', ImportWarning, stacklevel=2)

        class decryption_error(Exception): pass
        class verification_error(Exception): pass

        if sys.version_info > (3,):
            long = int


        def newkeys(size):
            """Wrapper for PyCrypto RSA key generation, to better match rsa's method"""
            random_generator = Random.new().read
            key = RSA.generate(size, random_generator)
            return key.publickey(), key

        
        def encrypt(msg, key):
            """Wrapper for PyCrypto RSA encryption method, to better match rsa's method"""
            return PKCS115_Cipher(key).encrypt(msg)


        def decrypt(msg, key):
            """Wrapper for PyCrypto RSA decryption method, to better match rsa's method"""
            ret = PKCS115_Cipher(key).decrypt(msg, None)
            if not ret:
                raise decryption_error("Decryption failed")
            return ret


        def sign(msg, key, hashop):
            """Wrapper for PyCrypto RSA signing method, to better match rsa's method"""
            hashtable = {'MD5': MD5,
                         'SHA-1': SHA,
                         'SHA-256': SHA256,
                         'SHA-384': SHA384,
                         'SHA-512': SHA512}
            hsh = hashtable.get(hashop).new()
            hsh.update(msg)
            signer = PKCS1_v1_5.PKCS115_SigScheme(key)
            return signer.sign(hsh)


        def verify(msg, sig, key):
            """Wrapper for PyCrypto RSA signature verification, to better match rsa's method"""
            for hashop in [SHA512, SHA384, SHA256, SHA, MD5]:
                hsh = hashop.new()
                hsh.update(msg)
                check = PKCS1_v1_5.PKCS115_SigScheme(key)
                res = check.verify(hsh, sig)
                if res:
                    break
            if not res:
                raise verification_error("Signature verification failed")
            return True
            

        def public_key(n, e):
            """Wrapper for PyCrypto RSA key constructor, to better match rsa's method"""
            return RSA.construct((long(n), long(e)))

    except ImportError:  # pragma: no cover
        raise ImportError("You cannot use this without the rsa or PyCrypto module. To install this, run 'pip install rsa'. The rsa module is recommended because, while it's slightly slower, it's much more flexible, and ensures communication with other secure_sockets.")


class secure_socket(socket.socket):
    """An RSA encrypted and secured socket. Requires either the rsa or PyCrypto module"""
    def __init__(self, sock_family=socket.AF_INET, sock_type=socket.SOCK_STREAM, proto=0, fileno=None, keysize=1024, silent=False):
        super(secure_socket, self).__init__(sock_family, sock_type, proto, fileno)
        if keysize < 1024:
            warnings.warn('Using a <1024 key length will make communication with PyCrypto implementations inconsistent. If you\'re using PyCrypto, expect an imminent exception.', RuntimeWarning, stacklevel=2)
        if keysize < max(354, (len(end_of_message) + 11) * 8):
            raise ValueError('This key is too small to be useful.')
        elif keysize > 8192:
            warnings.warn('This key is too large to be practical. Sending is easy. Generating is hard.', RuntimeWarning, stacklevel=2)
        self.__key_async = Pool().map_async(newkeys, [keysize])  # Gen in background to reduce block
        self.__pub, self.__priv = None, None    # Temporarily set to None so they can generate in background
        self.__keysize = keysize
        self.__key = None
        self.__peer_keysize = None
        self.__peer_msgsize = None
        self.__buffer = "".encode()
        self.__key_exchange = None
        self.__silent = silent
        # Socket inheritence section
        if sys.version_info[0] < 3:
            self.__sock_recv = self._sock.recv
        else:
            self.__sock_recv = super(secure_socket, self).recv
        self.send = partial(secure_socket.send, self)
        self.sendall = self.send
        self.recv = partial(secure_socket.recv, self)
        self.dup = partial(secure_socket.dup, self)

    def __print(self, *args):
        """Private method to print if __silent is False"""
        if not self.__silent:
            print(*args)

    @property
    def keysize(self):
        """Your key size in bits"""
        return self.__keysize

    def __map_key(self):
        """Private method to block if key is being generated"""
        if not self.__pub:
            self.__print("Waiting to grab key")
            self.__pub, self.__priv = self.__key_async.get()[0]
            del self.__key_async

    @property
    def pub(self):
        """Your public key; blocks if still generating"""
        self.__map_key()
        return self.__pub

    @property
    def priv(self):
        """Your private key; blocks if still generating"""
        self.__map_key()
        return self.__priv

    def __request_key(self):
        """Requests your peer's key over plaintext"""
        self.__print("Requesting key size")
        super(secure_socket, self).sendall(size_request)
        self.__peer_keysize = int(self.__sock_recv(16))
        if not uses_RSA and self.__peer_keysize < 1024:
            warnings.warn('Your peer is using a small key length. Because you\'re using PyCrypto, sending may silently fail, as on some keys PyCrypto will not construct it correctly. To fix this, please run \'pip install rsa\'.', RuntimeWarning, stacklevel=2)
        self.__peer_msgsize = (self.__peer_keysize // 8) - 11
        self.__print("Requesting key")
        super(secure_socket, self).sendall(key_request)
        keys = self.__sock_recv(self.__peer_keysize)
        if isinstance(keys, type(b'')):
            keys = keys.decode()
        key = keys.split(",")
        self.__key = public_key(int(key[0]), int(key[1]))
        self.__print("Key received")
    
    def __send_key(self):
        """Sends your key over plaintext"""
        req = self.__sock_recv(len(size_request))
        if req != size_request:
            raise ValueError("Handshake has failed due to invalid request from peer: %s" % req)
        self.__print("Sending key size")
        keysize = str(self.keysize) + ' ' * (16 - len(str(self.keysize)))
        super(secure_socket, self).sendall(keysize.encode("utf-8"))
        req = self.__sock_recv(len(key_request))
        if req != key_request:
            raise ValueError("Handshake has failed due to invalid request from peer")
        self.__print("Sending key")
        key = (str(self.pub.n) + "," + str(self.pub.e)).encode('utf-8')
        super(secure_socket, self).sendall(key + ' '.encode() * (self.keysize - len(key)))

    def __handshake(self, order):
        """Wrapper for sendKey and requestKey"""
        t = self.gettimeout()
        super(secure_socket, self).settimeout(None)
        if order:
            self.__send_key()
        self.__request_key()
        if not order:
            self.__send_key()
        super(secure_socket, self).settimeout(t)

    def settimeout(self, timeout):
        """Sets the timeout for the socket. Blocks if keys are being exchanged."""
        if self.__key_exchange:
            self.__key_exchange.join()
            self.__key_exchange = None
        super(secure_socket, self).settimeout(timeout)

    @property
    def peer_keysize(self):
        """Your peer's key size in bits"""
        return self.__peer_keysize

    @property
    def key(self):
        """Your peer's public key; blocks if you're receiving it"""
        if self.__key_exchange:
            self.__key_exchange.join()
            self.__key_exchange = None
        return self.__key

    def close(self):
        """Closes your connection to another socket, then cleans up metadata"""
        super(secure_socket, self).close()
        self.__key = None
        self.__peer_keysize = None
        self.__peer_msgsize = None
    
    def dup(self, conn=None):
        """Duplicates this secure_socket, with all key information, connected to the same peer.
        Blocks if keys are being exchanged."""
        # 
        # Ridiculous python2/3 compatability secion
        if sys.version_info[0] < 3:
            sock = secure_socket(self.family, self.type)
            if not conn:
                sock._sock = socket.socket.dup(self)
            else:
                sock._sock = conn
        else:
            if not conn:
                sock = super(secure_socket, self).dup()
            else:
                import _socket
                sock = secure_socket()
                fd = _socket.dup(conn.fileno())
                super(secure_socket, sock).__init__(conn.family, conn.type, conn.proto, fd)
        # End ridiculous compatability section
        sock.__silent = self.__silent
        sock.__map_key()
        sock.__pub, sock.__priv = self.pub, self.priv  # Uses public API so it blocks when key is generating
        sock.__keysize = self.__keysize
        sock.__key = self.key  # Uses public API so it blocks when key is exchanging
        sock.__peer_keysize = self.__peer_keysize
        sock.__peer_msgsize = self.__peer_msgsize
        sock.__buffer = self.__buffer
        # Socket inheritence section
        if sys.version_info[0] < 3:
            sock.__sock_recv = sock._sock.recv
        else:
            sock.__sock_recv == super(secure_socket, self).recv
        sock.send = partial(secure_socket.send, sock)
        sock.sendall = sock.send
        sock.recv = partial(secure_socket.recv, sock)
        sock.dup = partial(secure_socket.dup, sock)
        # End socket inheritence section
        return sock

    def accept(self):
        """Accepts an incoming connection.
        Like a native socket, it returns a copy of the socket and the connected address."""
        conn, addr = super(secure_socket, self).accept()
        sock = self.dup(conn=conn)
        sock.__key_exchange = Thread(target=sock.__handshake, args=(1,))
        sock.__key_exchange.daemon = True
        sock.__key_exchange.start()
        return sock, addr

    def connect(self, ip):
        """Connects to another secure_socket"""
        super(secure_socket, self).connect(ip)
        self.__key_exchange = Thread(target=self.__handshake, args=(0,))
        self.__key_exchange.daemon = True
        self.__key_exchange.start()

    def sign(self, msg, hashop='best'):
        """Signs a message with a given hash, or self-determined one. If using PyCrypto, always defaults to SHA-512"""
        try:
            msg = msg.encode()
        except:
            pass
        if hashop != 'best':
            return sign(msg, self.priv, hashop)
        elif self.__keysize >= 746:
            return sign(msg, self.priv, 'SHA-512')
        elif self.__keysize >= 618:
            return sign(msg, self.priv, 'SHA-384')
        elif self.__keysize >= 490:
            return sign(msg, self.priv, 'SHA-256')
        elif self.__keysize >= 362:
            return sign(msg, self.priv, 'SHA-1')
        else:   # if self.__keysize < 354: raises OverflowError
            return sign(msg, self.priv, 'MD5')

    def verify(self, msg, sig, key=None):
        """Verifies a message with a given key (Default: your peer's)"""
        if key is None:
            key = self.key
        return verify(msg, sig, key)

    def __send(self, msg):
        """Base method for sending a message. Encrypts and sends. Use send instead."""
        if not isinstance(msg, type("a".encode('utf-8'))):
            msg = str(msg).encode('utf-8')
        x = 0
        while x < len(msg) - self.__peer_msgsize:
            super(secure_socket, self).sendall(encrypt(msg[x:x+self.__peer_msgsize], self.key))
            x += self.__peer_msgsize
        super(secure_socket, self).sendall(encrypt(msg[x:], self.key))
        super(secure_socket, self).sendall(encrypt(end_of_message, self.key))

    def send(self, msg):
        """Sends an encrypted copy of your message, and an encrypted signature.
        Blocks if keys are being exchanged."""
        wait = self.key  # Use public API to block until key exchanged
        self.__send(msg)
        self.__send(self.sign(msg))  # Uses public API in order to use most comprehensive hash

    def __recv(self):
        """Base method for receiving a message. Receives and decrypts. Use recv instead."""
        received = b''
        packet = b''
        try:
            while packet != end_of_message:
                received += packet
                packet = self.__sock_recv((self.__keysize + 6) // 8)
                packet = decrypt(packet, self.priv)
            return received
        except decryption_error:
            print("Decryption error---Content: " + repr(packet))
            raise
        except ValueError as error:
            if error.args[0] in ["invalid literal for int() with base 16: ''", "invalid literal for int() with base 16: b''"]:
                return 0
            else:
                raise error

    def recv(self, size=None):
        """Receives and decrypts a message, then verifies it against the attached signature.
        Blocks if keys are being exchanged, regardless of timeout settings."""
        #
        # If there's a buffer, return from that immediately
        if self.__buffer:
            msg = self.__buffer[:size]  # If size is None, it grabs everything
            self.__buffer = self.__buffer[len(msg):]
            return msg
        # Otherwise, get a message and signature from your peer
        msg = self.__recv()
        sig = self.__recv()
        if not (msg or sig):
            return ''
        self.verify(msg, sig)  # Uses public API so it blocks when key is exchanging
        # If a size isn't defined, return the whole message. Otherwise manage the buffer as well.
        self.__buffer += msg
        ret = self.__buffer[:size]
        self.__buffer = self.__buffer[len(ret):]
        return ret