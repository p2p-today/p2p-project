import os, socket, ssl, sys, tempfile

try:
    from OpenSSL import crypto

    def generate_self_signed_cert(cert_file, key_file):
        """Given two file-like objects, generate an SSL key and certificate."""
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

except ImportError:
    try:
        from cryptography import x509
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
        from cryptography.x509.oid import NameOID
        import datetime, uuid

        def generate_self_signed_cert(cert_file, key_file):
            """Given two file-like objects, generate an SSL key and certificate."""
            one_day = datetime.timedelta(1, 0, 0)
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            public_key = private_key.public_key()
            builder = x509.CertificateBuilder()
            builder = builder.subject_name(x509.Name([
                x509.NameAttribute(NameOID.COMMON_NAME, u'cryptography.io'),
            ]))
            builder = builder.issuer_name(x509.Name([
                x509.NameAttribute(NameOID.COMMON_NAME, u'cryptography.io'),
            ]))
            builder = builder.not_valid_before(datetime.datetime.today() - one_day)
            builder = builder.not_valid_after(datetime.datetime.today() + datetime.timedelta(365*10))
            builder = builder.serial_number(int(uuid.uuid4()))
            builder = builder.public_key(public_key)
            builder = builder.add_extension(
                x509.BasicConstraints(ca=False, path_length=None), critical=True,
            )
            certificate = builder.sign(
                private_key=private_key, algorithm=hashes.SHA256(),
                backend=default_backend()
            )

            key_file.write(private_key.private_bytes(
                Encoding.PEM, 
                PrivateFormat.TraditionalOpenSSL,
                NoEncryption()
            ))
            cert_file.write(certificate.public_bytes(Encoding.PEM))

    except ImportError:  # pragma: no cover
        raise

def get_socket(server_side):
    if server_side:
        names = (None, None)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".cert") as cert_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".key") as key_file:
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

if sys.version_info < (3, ):
    import atexit
    cleanup_files = []

    def cleanup():  # pragma: no cover
        for f in cleanup_files:
            os.remove(f)

    atexit.register(cleanup)