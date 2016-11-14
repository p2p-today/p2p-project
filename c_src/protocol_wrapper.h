#ifndef CP2P_PROTOCOL_TYPE
#define CP2P_PROTOCOL_TYPE TRUE

#ifdef _cplusplus
extern "C"  {
#endif

#include <Python.h>
#include <bytesobject.h>
#include "structmember.h"
#include "SubnetStruct.h"
#include "base.h"
#include "py_utils.h"

typedef struct {
    PyObject_HEAD
    SubnetStruct *sub;
} protocol_wrapper;

static void protocol_wrapper_dealloc(protocol_wrapper* self)    {
    Py_BEGIN_ALLOW_THREADS
    destroySubnet(self->sub);
    Py_END_ALLOW_THREADS
    Py_TYPE(self)->tp_free((PyObject*)self);
}

static PyObject *protocol_wrapper_new(PyTypeObject *type, PyObject *args, PyObject *kwds)   {
    protocol_wrapper *self;

    self = (protocol_wrapper *)type->tp_alloc(type, 0);

    return (PyObject *)self;
}

static int protocol_wrapper_init(protocol_wrapper *self, PyObject *args, PyObject *kwds)    {
    const char *sub=NULL, *enc=NULL;
    int sub_size = 0, enc_size = 0;

    static char *kwlist[] = {(char*)"subnet", (char*)"encryption", NULL};

    if (! PyArg_ParseTupleAndKeywords(args, kwds, "s#s#", kwlist,
                                      &sub, &sub_size, &enc, &enc_size))
        return -1;

    Py_BEGIN_ALLOW_THREADS
    CP2P_DEBUG("Building protocol\n");
    self->sub = getSubnet((char *)sub, sub_size, (char *)enc, enc_size);
    Py_END_ALLOW_THREADS

    return 0;
}

static PyObject *protocol_id(protocol_wrapper *self)    {
    char * id;
    PyObject *ret;
    Py_BEGIN_ALLOW_THREADS
    CP2P_DEBUG("Entering id getter\n");
    id = subnetID(self->sub);
    Py_END_ALLOW_THREADS
    ret = pybytes_from_chars((unsigned char*)id, self->sub->idSize);
    if (PyErr_Occurred())
        return NULL;
    return ret;
}

static PyObject *protocol_subnet(protocol_wrapper *self)    {
    PyObject *ret = Py_BuildValue("s#", self->sub->subnet, self->sub->subnetSize);
    if (PyErr_Occurred())
        return NULL;
    return ret;
}

static PyObject *protocol_encryption(protocol_wrapper *self)    {
    PyObject *ret = Py_BuildValue("s#", self->sub->encryption, self->sub->encryptionSize);
    if (PyErr_Occurred())
        return NULL;
    return ret;
}

static PyGetSetDef protocol_wrapper_getsets[] = {
    {(char*)"subnet", (getter)protocol_subnet, NULL,
        (char*)"Return the protocol subnet name"
    },
    {(char*)"encryption", (getter)protocol_encryption, NULL,
        (char*)"Return the protocol encryption method"
    },
    {(char*)"id", (getter)protocol_id, NULL,
        (char*)"Return the protocol ID"
    },
    {NULL}  /* Sentinel */
};

static PyObject *protocol_getitem(protocol_wrapper *self, Py_ssize_t index)  {
    if (index == 0 || index == -2)
        return Py_BuildValue("s#", self->sub->subnet, self->sub->subnetSize);
    else if (index == 1 || index == -1)
        return Py_BuildValue("s#", self->sub->encryption, self->sub->encryptionSize);

    PyErr_SetString(PyExc_IndexError, "tuple index out of range");
    return NULL;
}

static unsigned short protocol__len__(protocol_wrapper *self)    {
    return 2;
}

static PySequenceMethods protocol_wrapper_sequence = {
    (lenfunc)protocol__len__,       /* __len__ */
    0,                              /* __add__ */
    0,                              /* __mul__ */
    (ssizeargfunc)protocol_getitem, /* __getitem__ */
    0,                              /* __getslice__ */
    0,                              /* __setitem__ */
    0                               /* __setslice__ */
};

static PyTypeObject protocol_wrapper_type = {
    PyVarObject_HEAD_INIT(NULL, 0)
    "protocol",                /* tp_name */
    sizeof(protocol_wrapper),  /* tp_basicsize */
    0,                         /* tp_itemsize */
    (destructor)protocol_wrapper_dealloc,/* tp_dealloc */
    0,                         /* tp_print */
    0,                         /* tp_getattr */
    0,                         /* tp_setattr */
    0,                         /* tp_reserved */
    0,                         /* tp_repr */
    0,                         /* tp_as_number */
    &protocol_wrapper_sequence,/* tp_as_sequence */
    0,                         /* tp_as_mapping */
    0,                         /* tp_hash  */
    0,                         /* tp_call */
    0,                         /* tp_str */
    0,                         /* tp_getattro */
    0,                         /* tp_setattro */
    0,                         /* tp_as_buffer */
    Py_TPFLAGS_DEFAULT,        /* tp_flags */
    "C implementation of the protocol object",/* tp_doc */
    0,                         /* tp_traverse */
    0,                         /* tp_clear */
    0,                         /* tp_richcompare */
    0,                         /* tp_weaklistoffset */
    0,                         /* tp_iter */
    0,                         /* tp_iternext */
    0,                         /* tp_methods */
    0,                         /* tp_members */
    protocol_wrapper_getsets,  /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc)protocol_wrapper_init,/* tp_init */
    0,                         /* tp_alloc */
    protocol_wrapper_new,      /* tp_new */
};

#ifdef _cplusplus
}
#endif

#endif
