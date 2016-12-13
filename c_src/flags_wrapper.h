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
    PyModule_AddObject(flags_wrapper, "reserved", pylist_from_array_string((char **)RESERVED_FLAGS, RESERVED_LENS, NUM_RESERVED));

    // Main flags
    PyModule_AddObject(flags_wrapper, "broadcast",   pybytes_from_chars(BROADCAST_FLAG, BROADCAST_LEN));
    PyModule_AddObject(flags_wrapper, "renegotiate", pybytes_from_chars(RENEGOTIATE_FLAG, RENEGOTIATE_LEN));
    PyModule_AddObject(flags_wrapper, "whisper",     pybytes_from_chars(WHISPER_FLAG, WHISPER_LEN));
    PyModule_AddObject(flags_wrapper, "ping",        pybytes_from_chars(PING_FLAG, PING_LEN));
    PyModule_AddObject(flags_wrapper, "pong",        pybytes_from_chars(PONG_FLAG, PONG_LEN));

    // Sub-flags
    /*PyModule_AddObject(flags_wrapper, "broadcast",   pybytes_from_chars(BROADCAST_FLAG, BROADCAST_LEN));*/
    PyModule_AddObject(flags_wrapper, "compression", pybytes_from_chars(COMPRESSION_FLAG, COMPRESSION_LEN));
    /*PyModule_AddObject(flags_wrapper, "whisper",     pybytes_from_chars(WHISPER_FLAG, WHISPER_LEN));*/
    /*PyModule_AddObject(flags_wrapper, "ping",        pybytes_from_chars(PING_FLAG, PING_LEN));*/
    /*PyModule_AddObject(flags_wrapper, "pong",        pybytes_from_chars(PONG_FLAG, PONG_LEN));*/
    PyModule_AddObject(flags_wrapper, "handshake",   pybytes_from_chars(HANDSHAKE_FLAG, HANDSHAKE_LEN));
    PyModule_AddObject(flags_wrapper, "notify",      pybytes_from_chars(NOTIFY_FLAG, NOTIFY_LEN));
    PyModule_AddObject(flags_wrapper, "peers",       pybytes_from_chars(PEERS_FLAG, PEERS_LEN));
    PyModule_AddObject(flags_wrapper, "request",     pybytes_from_chars(REQUEST_FLAG, REQUEST_LEN));
    PyModule_AddObject(flags_wrapper, "resend",      pybytes_from_chars(RESEND_FLAG, RESEND_LEN));
    PyModule_AddObject(flags_wrapper, "response",    pybytes_from_chars(RESPONSE_FLAG, RESPONSE_LEN));
    PyModule_AddObject(flags_wrapper, "store",       pybytes_from_chars(STORE_FLAG, STORE_LEN));
    PyModule_AddObject(flags_wrapper, "retrieve",    pybytes_from_chars(RETRIEVE_FLAG, RETRIEVE_LEN));

    // Implemented compression methods
    PyModule_AddObject(flags_wrapper, "gzip", pybytes_from_chars(GZIP_FLAG, GZIP_LEN));
    PyModule_AddObject(flags_wrapper, "zlib", pybytes_from_chars(ZLIB_FLAG, ZLIB_LEN));
    PyModule_AddObject(flags_wrapper, "snappy",   pybytes_from_chars(SNAPPY_FLAG, SNAPPY_LEN));

    // non-implemented compression methods (based on list from compressjs):
    PyModule_AddObject(flags_wrapper, "bwtc",     pybytes_from_chars(BWTC_FLAG, BWTC_LEN));
    PyModule_AddObject(flags_wrapper, "bz2",      pybytes_from_chars(BZ2_FLAG, BZ2_LEN));
    PyModule_AddObject(flags_wrapper, "context1", pybytes_from_chars(CONTEXT1_FLAG, CONTEXT1_LEN));
    PyModule_AddObject(flags_wrapper, "defsum",   pybytes_from_chars(DEFSUM_FLAG, DEFSUM_LEN));
    PyModule_AddObject(flags_wrapper, "dmc",      pybytes_from_chars(DMC_FLAG, DMC_LEN));
    PyModule_AddObject(flags_wrapper, "fenwick",  pybytes_from_chars(FENWICK_FLAG, FENWICK_LEN));
    PyModule_AddObject(flags_wrapper, "huffman",  pybytes_from_chars(HUFFMAN_FLAG, HUFFMAN_LEN));
    PyModule_AddObject(flags_wrapper, "lzjb",     pybytes_from_chars(LZJB_FLAG, LZJB_LEN));
    PyModule_AddObject(flags_wrapper, "lzjbr",    pybytes_from_chars(LZJBR_FLAG, LZJBR_LEN));
    PyModule_AddObject(flags_wrapper, "lzma",     pybytes_from_chars(LZMA_FLAG, LZMA_LEN));
    PyModule_AddObject(flags_wrapper, "lzp3",     pybytes_from_chars(LZP3_FLAG, LZP3_LEN));
    PyModule_AddObject(flags_wrapper, "mtf",      pybytes_from_chars(MTF_FLAG, MTF_LEN));
    PyModule_AddObject(flags_wrapper, "ppmd",     pybytes_from_chars(PPMD_FLAG, PPMD_LEN));
    PyModule_AddObject(flags_wrapper, "simple",   pybytes_from_chars(SIMPLE_FLAG, SIMPLE_LEN));


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
