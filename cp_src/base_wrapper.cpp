#include "stdlib.h"
#include "Python.h"
#include "bytesobject.h"
#include <stdexcept>
#include "structmember.h"
#include "base.h"
#include <string>

using namespace std;

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
        string cp_str = lst[i];
        unsigned char* c_str = (unsigned char*)cp_str.c_str();
        Py_buffer buffer;
        int res = PyBuffer_FillInfo(&buffer, 0, c_str, (Py_ssize_t)cp_str.length(), true, PyBUF_CONTIG_RO);
        if (res == -1) {
            PyErr_SetString(PyExc_RuntimeError, "Could not reconvert item back to python object");
            return NULL;
        }
        PyObject *memview = PyMemoryView_FromBuffer(&buffer);
#if PY_MAJOR_VERSION >= 3
        PyObject *ret = PyBytes_FromObject(memview);
#else
        PyObject *ret = PyObject_CallMethod(memview, "tobytes", "");
#endif
        Py_XDECREF(memview);
        PyList_SET_ITEM(listObj, i, ret);
    }
    return listObj;    
}

typedef struct {
    PyObject_HEAD
    pathfinding_message *msg;
    /* Type-specific fields go here. */
} pmessage_wrapper;

#if PY_MAJOR_VERSION >= 3

    static void pmessage_wrapper_dealloc(pmessage_wrapper* self)  {
        //Py_XDECREF(self->first);
        Py_TYPE(self)->tp_free((PyObject*)self);
    }
#else

    static void pmessage_wrapper_dealloc(pmessage_wrapper* self)  {
        //Py_XDECREF(self->first);
        self->ob_type->tp_free((PyObject*)self);
    }
#endif

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

static PyObject *payload(pmessage_wrapper *self)    {
    if (self->msg == NULL)  {
        PyErr_SetString(PyExc_AttributeError, "msg");
        return NULL;
    }
    return pylist_from_vector_string(self->msg->payload);
}

static PyObject *packets(pmessage_wrapper *self)    {
    if (self->msg == NULL)  {
        PyErr_SetString(PyExc_AttributeError, "msg");
        return NULL;
    }
    return pylist_from_vector_string(self->msg->packets());
}

static PyObject *str(pmessage_wrapper *self)    {
    if (self->msg == NULL)  {
        PyErr_SetString(PyExc_AttributeError, "msg");
        return NULL;
    }
    string cp_str = self->msg->str();
    unsigned char* c_str = (unsigned char*)cp_str.c_str();
    Py_buffer buffer;
    int res = PyBuffer_FillInfo(&buffer, 0, c_str, (Py_ssize_t)cp_str.length(), true, PyBUF_CONTIG_RO);
    if (res == -1) {
        PyErr_Print();
        exit(EXIT_FAILURE);
    }
    PyObject* memview = PyMemoryView_FromBuffer(&buffer);
#if PY_MAJOR_VERSION >= 3
    PyObject* ret = PyBytes_FromObject(memview);
#else
    PyObject *ret = PyObject_CallMethod(memview, "tobytes", "");
#endif
    Py_XDECREF(memview);
    return ret;
    //return PyBytes_FromString(self->msg->str().c_str());
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
    {NULL}  /* Sentinel */
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
    0,                         /* tp_as_sequence */
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

#if PY_MAJOR_VERSION >= 3

    static struct PyModuleDef basemodule = {
       PyModuleDef_HEAD_INIT,
       "cbase",  /* name of module */
       NULL,    /* module documentation, may be NULL */
       -1,      /* size of per-interpreter state of the module,
                   or -1 if the module keeps state in global variables. */
       BaseMethods
    };

    PyMODINIT_FUNC PyInit_cbase()    {
        PyObject* m;

        pmessage_wrapper_type.tp_new = PyType_GenericNew;
        if (PyType_Ready(&pmessage_wrapper_type) < 0)
            return NULL;

        m = PyModule_Create(&basemodule);
        if (m == NULL)
            return NULL;

        Py_INCREF(&pmessage_wrapper_type);
        PyModule_AddObject(m, "pathfinding_message", (PyObject *)&pmessage_wrapper_type);
        return m;
    }

    int main(int argc, char *argv[])    {
        wchar_t *program = Py_DecodeLocale(argv[0], NULL);

        if (program == NULL) {
            fprintf(stderr, "Fatal error: cannot decode argv[0]\n");
            exit(1);
        }

        PyImport_AppendInittab("cbase", PyInit_cbase);
        Py_SetProgramName(program);
        Py_Initialize();
        PyImport_ImportModule("cbase");
        PyMem_RawFree(program);
        return 0;
    }

#else


    #ifndef PyMODINIT_FUNC  /* declarations for DLL import/export */
        #define PyMODINIT_FUNC void
    #endif
    PyMODINIT_FUNC initcbase()  {
        PyObject* m;

        pmessage_wrapper_type.tp_new = PyType_GenericNew;
        if (PyType_Ready(&pmessage_wrapper_type) < 0)
            return;

        m = Py_InitModule3("cbase", BaseMethods,
                           "C++ implementation of some base functions");

        Py_INCREF(&pmessage_wrapper_type);
        PyModule_AddObject(m, "pathfinding_message", (PyObject *)&pmessage_wrapper_type);
    }

    int main(int argc, char *argv[])    {
        Py_SetProgramName(argv[0]);
        Py_Initialize();
        initcbase();
        return 0;
    }

#endif