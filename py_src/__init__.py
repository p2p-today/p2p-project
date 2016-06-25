from .mesh import mesh_socket
# from .chord import chord_socket
from .base import version, build_num

try:
    from .net import uses_RSA, decryption_error, verification_error, newkeys,\
                     encrypt, decrypt, sign, verify, secure_socket
except ImportError:  # pragma: no cover
    import warnings
    warnings.warn("Could not import encrypted socket module. Please install rsa from pip.", ImportWarning)
    uses_RSA = None

__version__ = version + "+" + build_num

__all__ = ["mesh", "chord", "net", "base"]