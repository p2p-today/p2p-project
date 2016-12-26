#ifndef CP2P_PMESSAGE_WRAPPER
#define CP2P_PMESSAGE_WRAPPER TRUE

#include <Python.h>
#include <bytesobject.h>
#include "structmember.h"
#include "base.h"
#include "InternalMessageStruct.h"
#include <string.h>
#include "py_utils.h"

#ifdef _cplusplus
extern "C" {
#endif

typedef struct {
    PyObject_HEAD
    InternalMessageStruct *msg;
    /* Type-specific fields go here. */
} pmessage_wrapper;

static void pmessage_wrapper_dealloc(pmessage_wrapper* self)  {
    destroyInternalMessage(self->msg);
    Py_TYPE(self)->tp_free((PyObject*)self);
}

static PyObject *pmessage_wrapper_new(PyTypeObject *type, PyObject *args, PyObject *kwds)   {
    pmessage_wrapper *self;

    self = (pmessage_wrapper *)type->tp_alloc(type, 0);

    return (PyObject *)self;
}

static int pmessage_wrapper_init(pmessage_wrapper *self, PyObject *args, PyObject *kwds)  {
    char *msg_type, *sender, **load, **comp;
    size_t i, type_len, sender_len, num_load, *load_lens, num_comp, *comp_lens;
    PyObject *py_msg=NULL, *py_sender=NULL, *payload=NULL, *compression=NULL;

    static char *kwlist[] = {(char*)"msg_type", (char*)"sender", (char*)"payload", (char*)"compressions", NULL};

    if (! PyArg_ParseTupleAndKeywords(args, kwds, "OOO|O", kwlist,
                                      &py_msg, &py_sender,
                                      &payload, &compression))
        return -1;

    CP2P_DEBUG("Parsing msg_type\n")
    msg_type = chars_from_pybytes(py_msg, &type_len);
    if (PyErr_Occurred())
        return -1;

    CP2P_DEBUG("Parsing sender\n")
    sender = chars_from_pybytes(py_sender, &sender_len);
    if (PyErr_Occurred())
        return -1;

    CP2P_DEBUG("Parsing payload\n")
    load = array_string_from_pylist(payload, &load_lens, &num_load);
    if (PyErr_Occurred())
        return -1;

    if (compression)    {
        comp = array_string_from_pylist(compression, &comp_lens, &num_comp);
        if (PyErr_Occurred())
            return -1;
    }

    Py_BEGIN_ALLOW_THREADS
    self->msg = constructInternalMessage(msg_type, type_len, sender, sender_len, load, load_lens, num_load);
    for (i = 0; i < num_load; i++)
        free(load[i]);
    free(msg_type);
    free(sender);
    free(load);
    CP2P_DEBUG("Parsing compression list\n")
    if (compression)    {
        setInternalMessageCompressions(self->msg, comp, comp_lens, num_comp);
        for (i = 0; i < num_comp; i++)
            free(comp[i]);
        free(comp_lens);
        free(comp);
    }
    CP2P_DEBUG("pmessage_wrapper variable assigned\n");

    CP2P_DEBUG("Returning\n")
    Py_END_ALLOW_THREADS
    return 0;
}

static pmessage_wrapper *pmessage_feed_string(PyTypeObject *type, PyObject *args, PyObject *kwds)    {
    char *str, **comp;
    size_t i, str_len, *comp_lens, num_comp;
    int err = 0, sizeless = 0;
    PyObject *py_compression=NULL, *py_str=NULL;
    pmessage_wrapper *ret;

    static char *kwlist[] = {(char*)"string", (char*)"sizeless", (char*)"compressions", NULL};

    if (! PyArg_ParseTupleAndKeywords(args, kwds, "O|iO", kwlist,
                                      &py_str, &sizeless, &py_compression))
        return NULL;

    str = chars_from_pybytes(py_str, &str_len);
    if (PyErr_Occurred())
        return NULL;

    ret = (pmessage_wrapper *)type->tp_alloc(type, 0);

    if (ret != NULL)    {
        if (py_compression)
            comp = array_string_from_pylist(py_compression, &comp_lens, &num_comp);
        if (PyErr_Occurred())
            return NULL;

        Py_BEGIN_ALLOW_THREADS
        if (py_compression) {
            ret->msg = deserializeCompressedInternalMessage(str, str_len, sizeless, &err, comp, comp_lens, num_comp);
            for (i = 0; i < num_comp; i++)
                free(comp[i]);
            free(comp);
            free(comp_lens);
        }
        else    {
            ret->msg = deserializeInternalMessage(str, str_len, sizeless, &err);
        }
        CP2P_DEBUG("pmessage was returned\n");
        free(str);
        Py_END_ALLOW_THREADS
        CP2P_DEBUG("Python GIL re-obtained\n");
    }

    if (PyErr_Occurred())    {
        CP2P_DEBUG("Returning NULL (that's bad)\n");
        return NULL;
    }
    else if (err)   {
        CP2P_DEBUG("Returning NULL due to error (that's bad)\n");
        PyErr_SetString(PyExc_IndexError, "Packets could not be correctly parsed");
        return NULL;
    }
    CP2P_DEBUG("Returning normally: %p\n", ret);

    return ret;
}

static PyObject *pmessage_payload(pmessage_wrapper *self)    {
    PyObject *ret = pytuple_from_array_string(self->msg->payload, self->msg->payload_lens, self->msg->num_payload);
    if (PyErr_Occurred())
        return NULL;
    return ret;
}

static PyObject *pmessage_packets(pmessage_wrapper *self)    {
    char **packets;
    size_t i, num, *lens;
    PyObject *ret;
    Py_BEGIN_ALLOW_THREADS
    num = 4 + self->msg->num_payload;
    packets = (char **) malloc(sizeof(char *) * num);
    lens = (size_t *) malloc(sizeof(size_t) * num);
    ensureInternalMessageID(self->msg);
    packets[0] = self->msg->msg_type;
    lens[0] = self->msg->msg_type_len;
    packets[1] = self->msg->sender;
    lens[1] = self->msg->sender_len;
    packets[2] = self->msg->id;
    lens[2] = self->msg->id_len;
    packets[3] = to_base_58(self->msg->timestamp, lens + 3);
    for (i = 0; i < self->msg->num_payload; i++) {
        packets[4+i] = self->msg->payload[i];
        lens[4+i] = self->msg->payload_lens[i];
    }
    Py_END_ALLOW_THREADS
    ret = pytuple_from_array_string(packets, lens, num);
    free(packets[3]);
    free(packets);
    free(lens);
    if (PyErr_Occurred())
        return NULL;
    return ret;
}

static PyObject *pmessage_str(pmessage_wrapper *self)    {
    PyObject *ret;
    if (self->msg->str_len == 0)    {
        Py_BEGIN_ALLOW_THREADS
        ensureInternalMessageStr(self->msg);
        Py_END_ALLOW_THREADS
    }
    ret = pybytes_from_chars((unsigned char*) self->msg->str, self->msg->str_len);
    if (PyErr_Occurred())
        return NULL;
    return ret;
}

static PyObject *pmessage_sender(pmessage_wrapper *self)    {
    PyObject *ret = pybytes_from_chars((unsigned char*) self->msg->sender, self->msg->sender_len);
    if (PyErr_Occurred())
        return NULL;
    return ret;
}

static PyObject *pmessage_msg_type(pmessage_wrapper *self)    {
    PyObject *ret = pybytes_from_chars((unsigned char*) self->msg->msg_type, self->msg->msg_type_len);
    if (PyErr_Occurred())
        return NULL;
    return ret;
}

static PyObject *pmessage_id(pmessage_wrapper *self)    {
    PyObject *ret;
    if (self->msg->id_len == 0) {
        Py_BEGIN_ALLOW_THREADS
        ensureInternalMessageID(self->msg);
        Py_END_ALLOW_THREADS
    }
    ret = pybytes_from_chars((unsigned char*) self->msg->id, self->msg->id_len);
    if (PyErr_Occurred())
        return NULL;
    return ret;
}

static PyObject *pmessage_timestamp_58(pmessage_wrapper *self)    {
    size_t len;
    char *c_str = to_base_58(self->msg->timestamp, &len);
    PyObject *ret = pybytes_from_chars((unsigned char*) c_str, len);
    free(c_str);
    if (PyErr_Occurred())
        return NULL;
    return ret;
}

static PyObject *pmessage_timestamp(pmessage_wrapper *self)    {
    PyObject *ret = PyLong_FromUnsignedLong(self->msg->timestamp);
    if (PyErr_Occurred())
        return NULL;
    return ret;
}

static PyObject *pmessage_compression_used(pmessage_wrapper *self)  {
    PyObject *ret;
    if (self->msg->num_compressions == 0)
        Py_RETURN_NONE;

    ret = pybytes_from_chars((unsigned char*) self->msg->compression[0], self->msg->compression_lens[0]);  // TODO: Do this in a method
    if (PyErr_Occurred())
        return NULL;
    return ret;
}

static PyObject *pmessage_compression_get(pmessage_wrapper *self)   {
    PyObject *ret = pylist_from_array_string(self->msg->compression, self->msg->compression_lens, self->msg->num_compressions);
    if (PyErr_Occurred())
        return NULL;
    return ret;
}

static int pmessage_compression_set(pmessage_wrapper *self, PyObject *value, void *closure) {
    size_t num_compression, *compression_lens;
    char **new_compression;
    if (value == NULL)  {
        PyErr_SetString(PyExc_AttributeError, "Cannot delete compression attribute");
        return -1;
    }

    new_compression = array_string_from_pylist(value, &compression_lens, &num_compression);
    if (PyErr_Occurred())
        return -1;

    Py_BEGIN_ALLOW_THREADS
    setInternalMessageCompressions(self->msg, new_compression, compression_lens, num_compression);
    Py_END_ALLOW_THREADS
    return 0;
}

static unsigned long long pmessage__len__(pmessage_wrapper *self)    {
    ensureInternalMessageStr(self->msg);
    return self->msg->str_len - 4;
}

static PyMemberDef pmessage_wrapper_members[] = {
    {NULL}  /* Sentinel */
};

static PyGetSetDef pmessage_wrapper_getsets[] = {
    {(char*)"payload", (getter)pmessage_payload, NULL,
        (char*)"Return the payload of this message"
    },
    {(char*)"packets", (getter)pmessage_packets, NULL,
        (char*)"Return the packets of this message"
    },
    {(char*)"string", (getter)pmessage_str, NULL,
        (char*)"Return the string of this message"
    },
    {(char*)"sender", (getter)pmessage_sender, NULL,
        (char*)"Return the sender ID of this message"
    },
    {(char*)"msg_type", (getter)pmessage_msg_type, NULL,
        (char*)"Return the message type"
    },
    {(char*)"time", (getter)pmessage_timestamp, NULL,
        (char*)"Return the message time"
    },
    {(char*)"time_58", (getter)pmessage_timestamp_58, NULL,
        (char*)"Return the message encoded in base_58"
    },
    {(char*)"id", (getter)pmessage_id, NULL,
        (char*)"Return the message ID"
    },
    {(char*)"compression_used", (getter)pmessage_compression_used, NULL,
        (char*)"Return the compression method used, or None if there is none"},
    {(char*)"compression", (getter)pmessage_compression_get, (setter)pmessage_compression_set,
        (char*)"A list of the compression methods available for use"},
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
Note:\n\
    If you feed a unicode object, it will be decoded using utf-8. All other objects are\n\
    treated as raw_unicode_escape. If you desire a particular codec, encode it yourself\n\
    before feeding it in.\n\
\n\
Warning:\n\
   This part is a work in progress. Currently errors often cause segfaults, and the above Exceptions are not consistently raised.\n"},
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

#ifdef _cplusplus
}
#endif

#endif
