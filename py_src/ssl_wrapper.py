import os, socket, ssl, sys, tempfile
from OpenSSL import crypto

if sys.version_info < (3, ):
    import atexit
    cleanup_files = []

    def cleanup():  # pragma: no cover
        for f in cleanup_files:
            os.remove(f)

    atexit.register(cleanup)

def generate_self_signed_cert(cert_file, key_file):
    """Generate a SSL certificate.

    If the cert_path and the key_path are present they will be overwritten.
    """
    # create a key pair
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)
 
    # create a self-signed cert
    cert = crypto.X509()
    cert.get_subject().C = 'PY'
    cert.get_subject().ST = 'py2p generated cert'
    cert.get_subject().L = 'py2p generated cert'
    cert.get_subject().O = 'py2p generated cert'
    cert.get_subject().OU = 'py2p generated cert'
    cert.get_subject().CN = socket.gethostname()
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(10 * 365 * 24 * 60 * 60) 
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(key)
    cert.sign(key, 'sha1')
 
    cert_file.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    key_file.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))

def get_socket(server_side):
    if server_side:
        self_path = os.path.dirname(os.path.realpath(__file__))
        names = (None, None)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".cert", dir=self_path) as cert_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".key", dir=self_path) as key_file:
                generate_self_signed_cert(cert_file, key_file)
                names = (cert_file.name, key_file.name)
        sock = ssl.wrap_socket(socket.socket(), suppress_ragged_eofs=True, server_side=True, keyfile=names[1], certfile=names[0])
        if sys.version_info >= (3, ):
            os.remove(names[0])
            os.remove(names[1])
        else:
            cleanup_files.extend(names)
        return sock
    else:
        return ssl.wrap_socket(socket.socket(), server_side=False, suppress_ragged_eofs=True)