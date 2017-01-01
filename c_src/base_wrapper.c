/**
* Base Python Wrapper
* ===================
*/
#include <Python.h>
#include <bytesobject.h>
#include "structmember.h"
#include <string.h>
#include "base.h"
#include "py_utils.h"
#include "protocol_wrapper.h"
#include "InternalMessage_wrapper.h"
#include "flags_wrapper.h"

#ifdef _cplusplus
extern "C" {
#endif

static PyMethodDef BaseMethods[] = {
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

#if PY_MAJOR_VERSION >= 3

    static struct PyModuleDef basemodule = {
       PyModuleDef_HEAD_INIT,
       "cbase",  /* name of module */
       "A C implementation of select features from the py2p.base module",/* module documentation, may be NULL */
       -1,      /* size of per-interpreter state of the module,
                   or -1 if the module keeps state in global variables. */
       BaseMethods
    };

    PyMODINIT_FUNC PyInit_cbase()    {
        PyObject *cbase, *flags_wrapper;

        pmessage_wrapper_type.tp_new = PyType_GenericNew;
        if (PyType_Ready(&pmessage_wrapper_type) < 0)
            return NULL;

        protocol_wrapper_type.tp_new = PyType_GenericNew;
        if (PyType_Ready(&protocol_wrapper_type) < 0)
            return NULL;

        cbase = PyModule_Create(&basemodule);
        if (cbase == NULL)
            return NULL;

        flags_wrapper = PyModule_Create(&flagsmodule);
        if (flags_wrapper == NULL)
            return NULL;

        Py_INCREF(&protocol_wrapper_type);
        PyModule_AddObject(cbase, "protocol", (PyObject *)&protocol_wrapper_type);

        Py_INCREF(&pmessage_wrapper_type);
        PyModule_AddObject(cbase, "InternalMessage", (PyObject *)&pmessage_wrapper_type);

        addConstants(cbase, flags_wrapper);

        return cbase;
    }

        int main(int argc, char *argv[])    {
    #if PY_MINOR_VERSION >= 5
            wchar_t *program = Py_DecodeLocale(argv[0], NULL);
    #else
            size_t size = strlen(argv[0]) + 1;
            wchar_t *program = (wchar_t *) malloc(sizeof(wchar_t) * size);
            mbstowcs(program, argv[0], size);
    #endif

            if (program == NULL) {
                fprintf(stderr, "Fatal error: cannot decode argv[0]\n");
                exit(1);
            }

            PyImport_AppendInittab("cbase", PyInit_cbase);
            Py_SetProgramName(program);
            Py_Initialize();
            PyImport_ImportModule("cbase");
    #if PY_MINOR_VERSION >= 5
            PyMem_RawFree(program);
    #else
            free(program);
    #endif
            return 0;
        }

#else


    #ifndef PyMODINIT_FUNC  /* declarations for DLL import/export */
        #define PyMODINIT_FUNC void
    #endif
    PyMODINIT_FUNC initcbase()  {
        PyObject *cbase, *flags_wrapper;

        pmessage_wrapper_type.tp_new = PyType_GenericNew;
        if (PyType_Ready(&pmessage_wrapper_type) < 0)
            return;

        protocol_wrapper_type.tp_new = PyType_GenericNew;
        if (PyType_Ready(&protocol_wrapper_type) < 0)
            return;

        cbase = Py_InitModule3("cbase", BaseMethods,
                           "C++ implementation of some base functions");
        flags_wrapper = Py_InitModule3("flags", FlagsMethods,
                           "Storage container for protocol level flags");

        Py_INCREF(&pmessage_wrapper_type);
        PyModule_AddObject(cbase, "InternalMessage", (PyObject *)&pmessage_wrapper_type);

        Py_INCREF(&protocol_wrapper_type);
        PyModule_AddObject(cbase, "protocol", (PyObject *)&protocol_wrapper_type);

        addConstants(cbase, flags_wrapper);
    }

    int main(int argc, char *argv[])    {
        Py_SetProgramName(argv[0]);
        Py_Initialize();
        initcbase();
        return 0;
    }

#ifdef _cplusplus
}
#endif

#endif
