#ifndef CP2P_PMESSAGE_WRAPPER
#define CP2P_PMESSAGE_WRAPPER TRUE

#include <Python.h>
#include <bytesobject.h>
#include "structmember.h"
#include "base.h"
#include <string>
#include "py_utils.h"

using namespace std;

typedef struct {
    PyObject_HEAD
    pathfinding_message msg;
    /* Type-specific fields go here. */
} pmessage_wrapper;

static void pmessage_wrapper_dealloc(pmessage_wrapper* self)  {
    Py_TYPE(self)->tp_free((PyObject*)self);
}

static PyObject *pmessage_wrapper_new(PyTypeObject *type, PyObject *args, PyObject *kwds)   {
    pmessage_wrapper *self;

    self = (pmessage_wrapper *)type->tp_alloc(type, 0);

    return (PyObject *)self;
}

static int pmessage_wrapper_init(pmessage_wrapper *self, PyObject *args, PyObject *kwds)  {
    const char *msg_type=NULL, *sender=NULL;
    int type_size = 0, sender_size = 0;
    PyObject *payload=NULL, *compression=NULL;

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
        self->msg = pathfinding_message(string(msg_type, type_size), string(sender, sender_size), load, comp);
    }
    else    {
        self->msg = pathfinding_message(string(msg_type, type_size), string(sender, sender_size), load);
    }

    return 0;
}

static pmessage_wrapper *pmessage_feed_string(PyTypeObject *type, PyObject *args, PyObject *kwds)    {
    const char *str=NULL;
    int str_size = 0, sizeless = 0;
    PyObject *compressions=NULL;

    static char *kwlist[] = {(char*)"string", (char*)"sizeless", (char*)"compressions", NULL};

    if (! PyArg_ParseTupleAndKeywords(args, kwds, "s#|pO!", kwlist, 
                                      &str, &str_size, &sizeless, &PyList_Type, &compressions))
        return NULL;

    string str_string = string(str, str_size);
    pmessage_wrapper *ret = (pmessage_wrapper *)type->tp_alloc(type, 0);

    if (ret != NULL)    {
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

static PyObject *pmessage_payload(pmessage_wrapper *self)    {
    PyObject *ret = pylist_from_vector_string(self->msg.payload);
    if (PyErr_Occurred())
        return NULL;
    return ret;
}

static PyObject *pmessage_packets(pmessage_wrapper *self)    {
    PyObject *ret = pylist_from_vector_string(self->msg.packets());
    if (PyErr_Occurred())
        return NULL;
    return ret;
}

static PyObject *pmessage_str(pmessage_wrapper *self)    {
    string cp_str = self->msg.str();
    PyObject *ret = pybytes_from_string(cp_str);
    if (PyErr_Occurred())
        return NULL;
    return ret;
}

static PyObject *pmessage_sender(pmessage_wrapper *self)    {
    string cp_str = self->msg.sender;
    PyObject *ret = pybytes_from_string(cp_str);
    if (PyErr_Occurred())
        return NULL;
    return ret;
}

static PyObject *pmessage_msg_type(pmessage_wrapper *self)    {
    string cp_str = self->msg.msg_type;
    PyObject *ret = pybytes_from_string(cp_str);
    if (PyErr_Occurred())
        return NULL;
    return ret;
}

static PyObject *pmessage_id(pmessage_wrapper *self)    {
    string cp_str = self->msg.id();
    PyObject *ret = pybytes_from_string(cp_str);
    if (PyErr_Occurred())
        return NULL;
    return ret;
}

static PyObject *pmessage_timestamp_58(pmessage_wrapper *self)    {
    string cp_str = self->msg.time_58();
    PyObject *ret = pybytes_from_string(cp_str);
    if (PyErr_Occurred())
        return NULL;
    return ret;
}

static PyObject *pmessage_timestamp(pmessage_wrapper *self)    {
    PyObject *ret = PyLong_FromUnsignedLong(self->msg.timestamp);
    if (PyErr_Occurred())
        return NULL;
    return ret;
}

static unsigned long long pmessage__len__(pmessage_wrapper *self)    {
    return self->msg.length();
}

static PyMemberDef pmessage_wrapper_members[] = {
    {NULL}  /* Sentinel */
};

static PyGetSetDef pmessage_wrapper_getsets[] = {
    {"payload", (getter)pmessage_payload, NULL,
        "Return the payload of this message"
    },
    {"packets", (getter)pmessage_packets, NULL,
        "Return the packets of this message"
    },
    {"string", (getter)pmessage_str, NULL,
        "Return the string of this message"
    },
    {"sender", (getter)pmessage_sender, NULL,
        "Return the sender ID of this message"
    },
    {"msg_type", (getter)pmessage_msg_type, NULL,
        "Return the message type"
    },
    {"time", (getter)pmessage_timestamp, NULL,
        "Return the message time"
    },
    {"time_58", (getter)pmessage_timestamp_58, NULL,
        "Return the message encoded in base_58"
    },
    {"id", (getter)pmessage_id, NULL,
        "Return the message ID"
    },
    {NULL}  /* Sentinel */
};


static PyMethodDef pmessage_wrapper_methods[] = {
    {"feed_string", (PyCFunction)pmessage_feed_string, METH_CLASS | METH_KEYWORDS | METH_VARARGS, 
        "Constructs a pathfinding_message from a string or bytes object.\n\
\n\
Args:\n\
    string:         The string you wish to parse\n\
    sizeless:       A boolean which describes whether this string has its size header (default: it does)\n\
    compressions:   A list containing the standardized compression methods this message might be under (default: [])\n\
\n\
Returns:\n\
    A cbase.pathfinding_message from the given string\n\
\n\
Raises:\n\
   TypeError: Fed a non-string, non-bytes argument\n\
   AssertionError: Initial size header is incorrect\n\
   Exception:      Unrecognized compression method fed in compressions\n\
   struct.error:   Packet headers are incorrect OR unrecognized compression\n\
   IndexError:     See struct.error\n\
\n\
Warning:\n\
   This part is a work in progress. Currently errors often cause segfaults, and the above Exceptions are not consistently raised."},
    {NULL}  /* Sentinel */
};

static PySequenceMethods pmessage_as_sequence = {
    (lenfunc)pmessage__len__, /*sq_length*/
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
    "pathfinding_message",/* tp_name */
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
    pmessage_wrapper_getsets,  /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc)pmessage_wrapper_init,/* tp_init */
    0,                         /* tp_alloc */
    pmessage_wrapper_new,   /* tp_new */
};

#endif