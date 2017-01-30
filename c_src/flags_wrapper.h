#ifndef CP2P_FLAGS_WRAPPER
#define CP2P_FLAGS_WRAPPER TRUE

#ifdef _cplusplus
extern "C" {
#endif

#include <Python.h>
#include <bytesobject.h>
#include "structmember.h"
#include "base.h"
#include <string.h>
#include "py_utils.h"

static PyMethodDef FlagsMethods[] = {
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

static void addConstants(PyObject *cbase, PyObject *flags_wrapper)  {
    char user_salt[36];
    PyObject *cbase_dict;
    PyModule_AddObject(cbase, "compression", pylist_from_array_string((char **)COMPRESSION_FLAGS, COMPRESSION_LENS, NUM_COMPRESSIONS));
    PyModule_AddObject(cbase, "version", pybytes_from_chars((unsigned char *) C2P_VERSION, strlen(C2P_VERSION)));
    get_user_salt(user_salt);
    PyModule_AddObject(cbase, "user_salt", pybytes_from_chars((unsigned char *)user_salt, 36));

    // Add reserved flags
    PyModule_AddObject(flags_wrapper, "reserved", pytuple_from_array_char((const unsigned char *)RESERVED_FLAGS, NUM_RESERVED));

    // Main flags
    PyModule_AddObject(flags_wrapper, "broadcast",   PyLong_FromUnsignedLongLong(BROADCAST_FLAG));
    PyModule_AddObject(flags_wrapper, "renegotiate", PyLong_FromUnsignedLongLong(RENEGOTIATE_FLAG));
    PyModule_AddObject(flags_wrapper, "whisper",     PyLong_FromUnsignedLongLong(WHISPER_FLAG));
    PyModule_AddObject(flags_wrapper, "ping",        PyLong_FromUnsignedLongLong(PING_FLAG));
    PyModule_AddObject(flags_wrapper, "pong",        PyLong_FromUnsignedLongLong(PONG_FLAG));

    // Sub-flags
    /*PyModule_AddObject(flags_wrapper, "broadcast",   PyLong_FromUnsignedLongLong(BROADCAST_FLAG));*/
    PyModule_AddObject(flags_wrapper, "compression", PyLong_FromUnsignedLongLong(COMPRESSION_FLAG));
    /*PyModule_AddObject(flags_wrapper, "whisper",     PyLong_FromUnsignedLongLong(WHISPER_FLAG));*/
    /*PyModule_AddObject(flags_wrapper, "ping",        PyLong_FromUnsignedLongLong(PING_FLAG));*/
    /*PyModule_AddObject(flags_wrapper, "pong",        PyLong_FromUnsignedLongLong(PONG_FLAG));*/
    PyModule_AddObject(flags_wrapper, "handshake",   PyLong_FromUnsignedLongLong(HANDSHAKE_FLAG));
    PyModule_AddObject(flags_wrapper, "notify",      PyLong_FromUnsignedLongLong(NOTIFY_FLAG));
    PyModule_AddObject(flags_wrapper, "peers",       PyLong_FromUnsignedLongLong(PEERS_FLAG));
    PyModule_AddObject(flags_wrapper, "request",     PyLong_FromUnsignedLongLong(REQUEST_FLAG));
    PyModule_AddObject(flags_wrapper, "resend",      PyLong_FromUnsignedLongLong(RESEND_FLAG));
    PyModule_AddObject(flags_wrapper, "response",    PyLong_FromUnsignedLongLong(RESPONSE_FLAG));
    PyModule_AddObject(flags_wrapper, "store",       PyLong_FromUnsignedLongLong(STORE_FLAG));
    PyModule_AddObject(flags_wrapper, "retrieve",    PyLong_FromUnsignedLongLong(RETRIEVE_FLAG));

    // Implemented compression methods
    PyModule_AddObject(flags_wrapper, "gzip",     PyLong_FromUnsignedLongLong(GZIP_FLAG));
    PyModule_AddObject(flags_wrapper, "zlib",     PyLong_FromUnsignedLongLong(ZLIB_FLAG));
    PyModule_AddObject(flags_wrapper, "snappy",   PyLong_FromUnsignedLongLong(SNAPPY_FLAG));

    // non-implemented compression methods (based on list from compressjs):
    PyModule_AddObject(flags_wrapper, "bwtc",     PyLong_FromUnsignedLongLong(BWTC_FLAG));
    PyModule_AddObject(flags_wrapper, "bz2",      PyLong_FromUnsignedLongLong(BZ2_FLAG));
    PyModule_AddObject(flags_wrapper, "context1", PyLong_FromUnsignedLongLong(CONTEXT1_FLAG));
    PyModule_AddObject(flags_wrapper, "defsum",   PyLong_FromUnsignedLongLong(DEFSUM_FLAG));
    PyModule_AddObject(flags_wrapper, "dmc",      PyLong_FromUnsignedLongLong(DMC_FLAG));
    PyModule_AddObject(flags_wrapper, "fenwick",  PyLong_FromUnsignedLongLong(FENWICK_FLAG));
    PyModule_AddObject(flags_wrapper, "huffman",  PyLong_FromUnsignedLongLong(HUFFMAN_FLAG));
    PyModule_AddObject(flags_wrapper, "lzjb",     PyLong_FromUnsignedLongLong(LZJB_FLAG));
    PyModule_AddObject(flags_wrapper, "lzjbr",    PyLong_FromUnsignedLongLong(LZJBR_FLAG));
    PyModule_AddObject(flags_wrapper, "lzma",     PyLong_FromUnsignedLongLong(LZMA_FLAG));
    PyModule_AddObject(flags_wrapper, "lzp3",     PyLong_FromUnsignedLongLong(LZP3_FLAG));
    PyModule_AddObject(flags_wrapper, "mtf",      PyLong_FromUnsignedLongLong(MTF_FLAG));
    PyModule_AddObject(flags_wrapper, "ppmd",     PyLong_FromUnsignedLongLong(PPMD_FLAG));
    PyModule_AddObject(flags_wrapper, "simple",   PyLong_FromUnsignedLongLong(SIMPLE_FLAG));


    cbase_dict = PyModule_GetDict(cbase);
    PyDict_SetItemString(cbase_dict, "flags", flags_wrapper);
}

    #if PY_MAJOR_VERSION >= 3

static struct PyModuleDef flagsmodule = {
   PyModuleDef_HEAD_INIT,
   "flags",  /* name of module */
   "Storage container for protocol level flags",/* module documentation, may be NULL */
   -1,      /* size of per-interpreter state of the module,
               or -1 if the module keeps state in global variables. */
   FlagsMethods
};

    #endif

#ifdef _cplusplus
}
#endif

#endif
