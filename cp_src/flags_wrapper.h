#ifndef CP2P_FLAGS_WRAPPER
#define CP2P_FLAGS_WRAPPER TRUE

#include <Python.h>
#include <bytesobject.h>
#include "structmember.h"
#include "base.h"
#include <string>
#include "py_utils.h"

using namespace std;

static PyMethodDef FlagsMethods[] = {
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

static void addConstants(PyObject *cbase, PyObject *flags_wrapper)  {
    vector<string> compression;
    for (unsigned int i = 0; i < flags::implemented_compressions.size(); i++)
        compression.push_back(string((size_t)1, flags::implemented_compressions[i]));
    PyModule_AddObject(cbase, "compression", pylist_from_vector_string(compression));
    PyModule_AddObject(cbase, "version", pybytes_from_string(string(CP2P_VERSION)));
    PyModule_AddObject(cbase, "user_salt", pybytes_from_string(user_salt));
    
    // Add reserved flags
    vector<string> reserved_set;
    for (unsigned int i = 0; i < flags::reserved.size(); i++)
        reserved_set.push_back(string((size_t)1, flags::reserved[i]));
    PyModule_AddObject(flags_wrapper, "reserved",   pylist_from_vector_string(reserved_set));

    // Main flags
    PyModule_AddObject(flags_wrapper, "broadcast",   pybytes_from_string(string((size_t) 1, flags::broadcast)));
    PyModule_AddObject(flags_wrapper, "waterfall",   pybytes_from_string(string((size_t) 1, flags::waterfall)));
    PyModule_AddObject(flags_wrapper, "whisper",     pybytes_from_string(string((size_t) 1, flags::whisper)));
    PyModule_AddObject(flags_wrapper, "renegotiate", pybytes_from_string(string((size_t) 1, flags::renegotiate)));
    PyModule_AddObject(flags_wrapper, "ping",        pybytes_from_string(string((size_t) 1, flags::ping)));
    PyModule_AddObject(flags_wrapper, "pong",        pybytes_from_string(string((size_t) 1, flags::pong)));

    // Sub-flags
    /*PyModule_AddObject(flags_wrapper, "broadcast",   pybytes_from_string(string((size_t) 1, flags::broadcast)));*/
    PyModule_AddObject(flags_wrapper, "compression", pybytes_from_string(string((size_t) 1, flags::compression)));
    /*PyModule_AddObject(flags_wrapper, "whisper",     pybytes_from_string(string((size_t) 1, flags::whisper)));*/
    PyModule_AddObject(flags_wrapper, "handshake",   pybytes_from_string(string((size_t) 1, flags::handshake)));
    /*PyModule_AddObject(flags_wrapper, "ping",        pybytes_from_string(string((size_t) 1, flags::ping)));*/
    /*PyModule_AddObject(flags_wrapper, "pong",        pybytes_from_string(string((size_t) 1, flags::pong)));*/
    PyModule_AddObject(flags_wrapper, "notify",      pybytes_from_string(string((size_t) 1, flags::notify)));
    PyModule_AddObject(flags_wrapper, "peers",       pybytes_from_string(string((size_t) 1, flags::peers)));
    PyModule_AddObject(flags_wrapper, "request",     pybytes_from_string(string((size_t) 1, flags::request)));
    PyModule_AddObject(flags_wrapper, "resend",      pybytes_from_string(string((size_t) 1, flags::resend)));
    PyModule_AddObject(flags_wrapper, "response",    pybytes_from_string(string((size_t) 1, flags::response)));
    PyModule_AddObject(flags_wrapper, "store",       pybytes_from_string(string((size_t) 1, flags::store)));
    PyModule_AddObject(flags_wrapper, "retrieve",    pybytes_from_string(string((size_t) 1, flags::retrieve)));

    // Implemented compression methods
    PyModule_AddObject(flags_wrapper, "gzip", pybytes_from_string(string((size_t) 1, flags::gzip)));
    PyModule_AddObject(flags_wrapper, "zlib", pybytes_from_string(string((size_t) 1, flags::zlib)));

    // non-implemented compression methods (based on list from compressjs):
    PyModule_AddObject(flags_wrapper, "bwtc",     pybytes_from_string(string((size_t) 1, flags::bwtc)));
    PyModule_AddObject(flags_wrapper, "bz2",      pybytes_from_string(string((size_t) 1, flags::bz2)));
    PyModule_AddObject(flags_wrapper, "context1", pybytes_from_string(string((size_t) 1, flags::context1)));
    PyModule_AddObject(flags_wrapper, "defsum",   pybytes_from_string(string((size_t) 1, flags::defsum)));
    PyModule_AddObject(flags_wrapper, "dmc",      pybytes_from_string(string((size_t) 1, flags::dmc)));
    PyModule_AddObject(flags_wrapper, "fenwick",  pybytes_from_string(string((size_t) 1, flags::fenwick)));
    PyModule_AddObject(flags_wrapper, "huffman",  pybytes_from_string(string((size_t) 1, flags::huffman)));
    PyModule_AddObject(flags_wrapper, "lzjb",     pybytes_from_string(string((size_t) 1, flags::lzjb)));
    PyModule_AddObject(flags_wrapper, "lzjbr",    pybytes_from_string(string((size_t) 1, flags::lzjbr)));
    PyModule_AddObject(flags_wrapper, "lzma",     pybytes_from_string(string((size_t) 1, flags::lzma)));
    PyModule_AddObject(flags_wrapper, "lzp3",     pybytes_from_string(string((size_t) 1, flags::lzp3)));
    PyModule_AddObject(flags_wrapper, "mtf",      pybytes_from_string(string((size_t) 1, flags::mtf)));
    PyModule_AddObject(flags_wrapper, "ppmd",     pybytes_from_string(string((size_t) 1, flags::ppmd)));
    PyModule_AddObject(flags_wrapper, "simple",   pybytes_from_string(string((size_t) 1, flags::simple)));


    PyObject *cbase_dict = PyModule_GetDict(cbase);
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

#endif