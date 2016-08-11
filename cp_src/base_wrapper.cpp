#include "stdlib.h"
#include <Python.h>
#include <bytesobject.h>
#include <stdexcept>
#include "structmember.h"
#include "base.h"
#include <string>

using namespace std;

PyObject *pybytes_from_string(string str)   {
    unsigned char* c_str = (unsigned char*)str.c_str();
    Py_buffer buffer;
    int res = PyBuffer_FillInfo(&buffer, 0, c_str, (Py_ssize_t)str.length(), true, PyBUF_CONTIG_RO);
    if (res == -1) {
        PyErr_SetString(PyExc_RuntimeError, "Could not reconvert item back to python object");
        return NULL;
    }
#if PY_MAJOR_VERSION >= 3
    PyObject *memview = PyMemoryView_FromBuffer(&buffer);
    PyObject *ret = PyBytes_FromObject(memview);
    Py_XDECREF(memview);
#elif PY_MINOR_VERSION >= 7
    PyObject *memview = PyMemoryView_FromBuffer(&buffer);
    PyObject *ret = PyObject_CallMethod(memview, "tobytes", "");
    Py_XDECREF(memview);
#else
    PyObject *ret = PyString_Encode(c_str, (Py_ssize_t)str.length(), "raw_unicode_escape", "strict");
#endif
    return ret;
}

vector<string> vector_string_from_pylist(PyObject *incoming)    {
    vector<string> out;
    if (PyList_Check(incoming)) {
        for(Py_ssize_t i = 0; i < PyList_Size(incoming); i++) {
            PyObject *value = PyList_GetItem(incoming, i);
            if (PyBytes_Check(value))
                out.push_back(string(PyBytes_AsString(value)));
            else if (PyUnicode_Check(value))    {
                PyObject *tmp = PyUnicode_AsEncodedString(value, "raw_unicode_escape", "strict");
                out.push_back(string(PyBytes_AsString(tmp)));
                Py_XDECREF(tmp);
            }
#if PY_MAJOR_VERSION >= 3
            else if (PyObject_CheckBuffer(value))   {
                PyObject *tmp = PyBytes_FromObject(value);
                out.push_back(string(PyBytes_AsString(tmp)));
                Py_XDECREF(tmp);
            }
#endif
            else    {
                PyErr_SetObject(PyExc_TypeError, value);
                vector<string> err;
                return err;
            }
        }
    }
    return out;
}

PyObject *pylist_from_vector_string(vector<string> lst) {
    PyObject *listObj = PyList_New( lst.size() );
    if (!listObj) throw logic_error("Unable to allocate memory for Python list");
    for (unsigned int i = 0; i < lst.size(); i++) {
        PyList_SET_ITEM(listObj, i, pybytes_from_string(lst[i]));
    }
    return listObj;    
}

typedef struct {
    PyObject_HEAD
    pathfinding_message *msg;
    /* Type-specific fields go here. */
} pmessage_wrapper;

static void pmessage_wrapper_dealloc(pmessage_wrapper* self)  {
    Py_TYPE(self)->tp_free((PyObject*)self);
}

static PyObject *pmessage_wrapper_new(PyTypeObject *type, PyObject *args, PyObject *kwds)   {
    pmessage_wrapper *self;

    self = (pmessage_wrapper *)type->tp_alloc(type, 0);
    if (self != NULL)
        self->msg = NULL;

    return (PyObject *)self;
}

static int pmessage_wrapper_init(pmessage_wrapper *self, PyObject *args, PyObject *kwds)  {
    const char *msg_type=NULL, *sender=NULL;
    int type_size = 0, sender_size = 0;
    PyObject *payload=NULL, *compression=NULL;
    pathfinding_message *tmp;

    static char *kwlist[] = {(char*)"msg_type", (char*)"sender", (char*)"payload", (char*)"compressions", NULL};

    if (! PyArg_ParseTupleAndKeywords(args, kwds, "s#s#O!|O!", kwlist, 
                                      &msg_type, &type_size, &sender, &sender_size, &PyList_Type, &payload, &PyList_Type, &compression))
        return -1;

    vector<string> load = vector_string_from_pylist(payload);
    if (PyErr_Occurred())
        return -1;

    if (compression)    {
        vector<string> comp = vector_string_from_pylist(compression);
        if (PyErr_Occurred())
            return -1;
        tmp = new pathfinding_message(string(msg_type, type_size), string(sender, sender_size), load, comp);
    }
    else    {
        tmp = new pathfinding_message(string(msg_type, type_size), string(sender, sender_size), load);
    }
    delete self->msg;
    self->msg = tmp;

    return 0;
}

static pmessage_wrapper *feed_string(PyTypeObject *type, PyObject *args, PyObject *kwds)    {
    const char *str=NULL, *sender=NULL;
    int str_size = 0, sizeless = 0;
    PyObject *compressions=NULL;

    static char *kwlist[] = {(char*)"string", (char*)"sizeless", (char*)"compressions", NULL};

    if (! PyArg_ParseTupleAndKeywords(args, kwds, "s#|pO!", kwlist, 
                                      &str, &str_size, &sizeless, &PyList_Type, &compressions))
        return NULL;

    string str_string = string(str, str_size);
    pmessage_wrapper *ret = (pmessage_wrapper *)type->tp_alloc(type, 0);

    if (ret != NULL)    {
        delete ret->msg;
        if (sizeless && compressions)
            ret->msg = pathfinding_message::feed_string(str_string, sizeless, vector_string_from_pylist(compressions));
        else if (compressions)
            ret->msg = pathfinding_message::feed_string(str_string, vector_string_from_pylist(compressions));
        else if (sizeless)
            ret->msg = pathfinding_message::feed_string(str_string, sizeless);
        else
            ret->msg = pathfinding_message::feed_string(str_string.substr(4));
    }

    if (PyErr_Occurred())
        return NULL;

    return ret;
}

static PyObject *payload(pmessage_wrapper *self)    {
    if (self->msg == NULL)  {
        PyErr_SetString(PyExc_AttributeError, "msg");
        return NULL;
    }
    PyObject *ret = pylist_from_vector_string(self->msg->payload);
    if (PyErr_Occurred())
        return NULL;
    return ret;
}

static PyObject *packets(pmessage_wrapper *self)    {
    if (self->msg == NULL)  {
        PyErr_SetString(PyExc_AttributeError, "msg");
        return NULL;
    }
    PyObject *ret = pylist_from_vector_string(self->msg->packets());
    if (PyErr_Occurred())
        return NULL;
    return ret;
}

static PyObject *str(pmessage_wrapper *self)    {
    if (self->msg == NULL)  {
        PyErr_SetString(PyExc_AttributeError, "msg");
        return NULL;
    }
    string cp_str = self->msg->str();
    PyObject *ret = pybytes_from_string(cp_str);
    if (PyErr_Occurred())
        return NULL;
    return ret;
}

static PyObject *sender(pmessage_wrapper *self)    {
    if (self->msg == NULL)  {
        PyErr_SetString(PyExc_AttributeError, "msg");
        return NULL;
    }
    string cp_str = self->msg->sender;
    PyObject *ret = pybytes_from_string(cp_str);
    if (PyErr_Occurred())
        return NULL;
    return ret;
}

static PyObject *msg_type(pmessage_wrapper *self)    {
    if (self->msg == NULL)  {
        PyErr_SetString(PyExc_AttributeError, "msg");
        return NULL;
    }
    string cp_str = self->msg->msg_type;
    PyObject *ret = pybytes_from_string(cp_str);
    if (PyErr_Occurred())
        return NULL;
    return ret;
}

static PyObject *id(pmessage_wrapper *self)    {
    if (self->msg == NULL)  {
        PyErr_SetString(PyExc_AttributeError, "msg");
        return NULL;
    }
    string cp_str = self->msg->id();
    PyObject *ret = pybytes_from_string(cp_str);
    if (PyErr_Occurred())
        return NULL;
    return ret;
}

static PyObject *time_58(pmessage_wrapper *self)    {
    if (self->msg == NULL)  {
        PyErr_SetString(PyExc_AttributeError, "msg");
        return NULL;
    }
    string cp_str = self->msg->time_58();
    PyObject *ret = pybytes_from_string(cp_str);
    if (PyErr_Occurred())
        return NULL;
    return ret;
}

static PyObject *timestamp(pmessage_wrapper *self)    {
    if (self->msg == NULL)  {
        PyErr_SetString(PyExc_AttributeError, "msg");
        return NULL;
    }
    PyObject *ret = PyLong_FromUnsignedLong(self->msg->timestamp);
    if (PyErr_Occurred())
        return NULL;
    return ret;
}

static unsigned long long __len__(pmessage_wrapper *self)    {
    if (self->msg == NULL)  {
        PyErr_SetString(PyExc_AttributeError, "msg");
        return 0;
    }
    return self->msg->length();
}

static PyMemberDef pmessage_wrapper_members[] = {
    {NULL}  /* Sentinel */
};


static PyMethodDef pmessage_wrapper_methods[] = {
    {"payload", (PyCFunction)payload, METH_NOARGS,
        "Return the payload of this message"
    },
    {"packets", (PyCFunction)packets, METH_NOARGS,
        "Return the packets of this message"
    },
    {"string", (PyCFunction)str, METH_NOARGS,
        "Return the string of this message"
    },
    {"sender", (PyCFunction)sender, METH_NOARGS,
        "Return the sender ID of this message"
    },
    {"msg_type", (PyCFunction)msg_type, METH_NOARGS,
        "Return the message type"
    },
    {"id", (PyCFunction)id, METH_NOARGS,
        "Return the message ID"
    },
    {"time", (PyCFunction)timestamp, METH_NOARGS,
        "Return the message time"
    },
    {"time_58", (PyCFunction)time_58, METH_NOARGS,
        "Return the message encoded in base_58"
    },
    {"feed_string", (PyCFunction)feed_string, METH_CLASS | METH_KEYWORDS | METH_VARARGS, 
        "Returns the pathfinding_message which corresponds to a serialized string"},
    {NULL}  /* Sentinel */
};

static PySequenceMethods pmessage_as_sequence = {
    (lenfunc)__len__, /*sq_length*/
    0, /*sq_concat*/
    0, /*sq_repeat*/
    0, /*sq_item*/
    0, /*sq_slice*/
    0, /*sq_ass_item*/
    0, /*sq_ass_slice*/
    0  /*sq_contains*/
};

static PyTypeObject pmessage_wrapper_type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "cbase.pathfinding_message",/* tp_name */
    sizeof(pmessage_wrapper),  /* tp_basicsize */
    0,                         /* tp_itemsize */
    (destructor)pmessage_wrapper_dealloc,/* tp_dealloc */
    0,                         /* tp_print */
    0,                         /* tp_getattr */
    0,                         /* tp_setattr */
    0,                         /* tp_reserved */
    0,                         /* tp_repr */
    0,                         /* tp_as_number */
    &pmessage_as_sequence,     /* tp_as_sequence */
    0,                         /* tp_as_mapping */
    0,                         /* tp_hash  */
    0,                         /* tp_call */
    0,                         /* tp_str */
    0,                         /* tp_getattro */
    0,                         /* tp_setattro */
    0,                         /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,/* tp_flags */
    "C++ implementation of the pathfinding_message object",/* tp_doc */
    0,                         /* tp_traverse */
    0,                         /* tp_clear */
    0,                         /* tp_richcompare */
    0,                         /* tp_weaklistoffset */
    0,                         /* tp_iter */
    0,                         /* tp_iternext */
    pmessage_wrapper_methods,  /* tp_methods */
    pmessage_wrapper_members,  /* tp_members */
    0,                         /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc)pmessage_wrapper_init,/* tp_init */
    0,                         /* tp_alloc */
    pmessage_wrapper_new,   /* tp_new */
};

static PyMethodDef BaseMethods[] = {
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

static PyMethodDef FlagsMethods[] = {
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

void addFlags(PyObject* flags_wrapper)  {
    //Main flags
    PyModule_AddObject(flags_wrapper, "broadcast",   pybytes_from_string(string((size_t) 1, flags::broadcast)));
    PyModule_AddObject(flags_wrapper, "waterfall",   pybytes_from_string(string((size_t) 1, flags::waterfall)));
    PyModule_AddObject(flags_wrapper, "whisper",     pybytes_from_string(string((size_t) 1, flags::whisper)));
    PyModule_AddObject(flags_wrapper, "renegotiate", pybytes_from_string(string((size_t) 1, flags::renegotiate)));
    PyModule_AddObject(flags_wrapper, "ping",        pybytes_from_string(string((size_t) 1, flags::ping)));
    PyModule_AddObject(flags_wrapper, "pong",        pybytes_from_string(string((size_t) 1, flags::pong)));


    //Sub-flags
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

    //Implemented compression methods
    PyModule_AddObject(flags_wrapper, "gzip", pybytes_from_string(string((size_t) 1, flags::gzip)));
    PyModule_AddObject(flags_wrapper, "zlib", pybytes_from_string(string((size_t) 1, flags::zlib)));

    //non-implemented compression methods (based on list from compressjs):
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
}

#if PY_MAJOR_VERSION >= 3

    static struct PyModuleDef basemodule = {
       PyModuleDef_HEAD_INIT,
       "cbase",  /* name of module */
       "A C++ implementation of select features from the py2p.base module",/* module documentation, may be NULL */
       -1,      /* size of per-interpreter state of the module,
                   or -1 if the module keeps state in global variables. */
       BaseMethods
    };

    static struct PyModuleDef flagsmodule = {
       PyModuleDef_HEAD_INIT,
       "flags",  /* name of module */
       "Storage container for protocol level flags",/* module documentation, may be NULL */
       -1,      /* size of per-interpreter state of the module,
                   or -1 if the module keeps state in global variables. */
       FlagsMethods
    };

    PyMODINIT_FUNC PyInit_cbase()    {
        PyObject *cbase, *flags_wrapper;

        pmessage_wrapper_type.tp_new = PyType_GenericNew;
        if (PyType_Ready(&pmessage_wrapper_type) < 0)
            return NULL;

        cbase = PyModule_Create(&basemodule);
        if (cbase == NULL)
            return NULL;

        flags_wrapper = PyModule_Create(&flagsmodule);
        if (flags_wrapper == NULL)
            return NULL;

        Py_INCREF(&pmessage_wrapper_type);
        PyModule_AddObject(cbase, "pathfinding_message", (PyObject *)&pmessage_wrapper_type);

        addFlags(flags_wrapper);

        PyObject *cbase_dict = PyModule_GetDict(cbase);
        PyDict_SetItemString(cbase_dict, "flags", flags_wrapper);

        return cbase;
    }

        int main(int argc, char *argv[])    {
    #if PY_MINOR_VERSION >= 5
            wchar_t *program = Py_DecodeLocale(argv[0], NULL);
    #else
            size_t size = strlen(argv[0]) + 1;
            wchar_t* program = new wchar_t[size];
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
            delete[] program;
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

        cbase = Py_InitModule3("cbase", BaseMethods,
                           "C++ implementation of some base functions");
        flags_wrapper = Py_InitModule3("flags", FlagsMethods,
                           "Storage container for protocol level flags");

        Py_INCREF(&pmessage_wrapper_type);
        PyModule_AddObject(cbase, "pathfinding_message", (PyObject *)&pmessage_wrapper_type);

        addFlags(flags_wrapper);

        PyObject *cbase_dict = PyModule_GetDict(cbase);
        PyDict_SetItemString(cbase_dict, "flags", flags_wrapper);
    }

    int main(int argc, char *argv[])    {
        Py_SetProgramName(argv[0]);
        Py_Initialize();
        initcbase();
        return 0;
    }

#endif
