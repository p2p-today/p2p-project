import rsa
import socket
key_request = "Requesting key".encode('utf-8')
end_of_message = "End of message".encode('utf-8')
myPub, myPriv = rsa.newkeys(1024)


def send(msg, conn, key):
    while key is None:
        safeprint("Key not found. Requesting key")
        conn.send(key_request)
        try:
            key = conn.recv(1024).split(",")
            key = rsa.PublicKey(int(key[0]), int(key[1]))
            safeprint("Key received")
        except EOFError:
            continue
    if not isinstance(msg, type("a".encode('utf-8'))):
        msg = msg.encode('utf-8')
    x = 0
    while x < len(msg) - 117:
        conn.sendall(rsa.encrypt(msg[x:x+117], key))
        x += 117
    conn.sendall(rsa.encrypt(msg[x:], key))
    conn.sendall(rsa.encrypt(end_of_message, key))
    return key


def recv(conn):
    received = "".encode('utf-8')
    a = ""
    try:
        while True:
            a = conn.recv(128)
            if a == key_request:
                safeprint("Key requested. Sending key")
                conn.sendall((str(myPriv.n) + "," + str(myPriv.e)).encode('utf-8'))
                continue
            a = rsa.decrypt(a, myPriv)
            safeprint("Packet = " + str(a), verbosity=3)
            if a == end_of_message:
                return received
            received += a
    except rsa.pkcs1.DecryptionError as error:
        safeprint("Decryption error---Content: " + str(a))
        return "".encode('utf-8')
