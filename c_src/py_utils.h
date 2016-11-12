#ifndef CP2P_PY_UTILS
#define CP2P_PY_UTILS TRUE

#include <Python.h>
#include <bytesobject.h>
#include <string.h>

#ifdef _cplusplus

extern "C"  {
#endif

static PyObject *pybytes_from_chars(const unsigned char *str, size_t len)   {
    Py_buffer buffer;
    int res = PyBuffer_FillInfo(&buffer, 0, (void *)str, (Py_ssize_t)len, 1, PyBUF_CONTIG_RO);
    if (res == -1) {
        PyErr_SetString(PyExc_RuntimeError, (char*)"Could not reconvert item back to python object");
        return NULL;
    }
#if PY_MAJOR_VERSION >= 3
    PyObject *memview = PyMemoryView_FromBuffer(&buffer);
    PyObject *ret = PyBytes_FromObject(memview);
    Py_XDECREF(memview);
#elif PY_MINOR_VERSION >= 7
    PyObject *memview = PyMemoryView_FromBuffer(&buffer);
    PyObject *ret = PyObject_CallMethod(memview, (char*)"tobytes", (char*)"");
    Py_XDECREF(memview);
#else
    PyObject *ret = PyString_Encode((char*)str, (Py_ssize_t)len, (char*)"raw_unicode_escape", (char*)"strict");
#endif
    return ret;
}

static char *chars_from_pybytes(PyObject *bytes, size_t *len)  {
    if (PyBytes_Check(bytes))   {
        CP2P_DEBUG("Decoding as bytes\n");
        char *buff = NULL;
        PyBytes_AsStringAndSize(bytes, &buff, (Py_ssize_t *)len);
        char *ret = (char *) malloc(sizeof(char) * (*len));
        memcpy(ret, buff, *len);
        return ret;
    }
#if PY_MAJOR_VERSION >= 3
    else if (PyObject_CheckBuffer(bytes))   {
        CP2P_DEBUG("Decoding as buffer (incoming recursion)\n")
        PyObject *tmp = PyBytes_FromObject(bytes);
        char *ret = chars_from_pybytes(tmp, len);
        Py_XDECREF(tmp);
        return ret;
    }
#else
    else if (PyByteArray_Check(bytes))  {
        CP2P_DEBUG("Decoding as bytearray\n");
        char *buff = PyByteArray_AS_STRING(bytes);
        *len = PyByteArray_GET_SIZE(bytes);
        char *ret = (char *) malloc(sizeof(char) * (*len));
        memcpy(ret, buff, *len);
        return ret;
    }
#endif
    else if (PyUnicode_Check(bytes))    {
        CP2P_DEBUG("Decoding as unicode (incoming recursion)\n");
        PyObject *tmp = PyUnicode_AsEncodedString(bytes, (char*)"utf-8", (char*)"strict");
        char *ret = chars_from_pybytes(tmp, len);
        Py_XDECREF(tmp);
        return ret;
    }
    else    {
        PyErr_SetObject(PyExc_TypeError, bytes);
        return NULL;
    }
}

static char **array_string_from_pylist(PyObject *incoming, size_t **arr_lens, size_t *num_objects)    {
    char **out;
    if (PyList_Check(incoming)) {
        *num_objects = (size_t) PyList_Size(incoming);
        out = (char **) malloc(sizeof(char *) * (*num_objects));
        *arr_lens = (size_t *) malloc(sizeof(size_t) * (*num_objects));
        size_t i;
        for(i = 0; i < *num_objects; i++) {
            PyObject *value = PyList_GetItem(incoming, (Py_ssize_t) i);
            out[i] = chars_from_pybytes(value, &((*arr_lens)[i]));
            if (PyErr_Occurred())
                return out;
        }
    }
    else if (PyTuple_Check(incoming)) {
        *num_objects = (size_t) PyTuple_Size(incoming);
        out = (char **) malloc(sizeof(char *) * (*num_objects));
        *arr_lens = (size_t *) malloc(sizeof(size_t) * (*num_objects));
        size_t i;
        for(i = 0; i < *num_objects; i++) {
            PyObject *value = PyTuple_GetItem(incoming, (Py_ssize_t) i);
            out[i] = chars_from_pybytes(value, &((*arr_lens)[i]));
            if (PyErr_Occurred())
                return out;
        }
    }
    else {
        PyObject *iter = PyObject_GetIter(incoming);
        PyObject *tup = PySequence_Tuple(iter);
        if (PyErr_Occurred())
            PyErr_SetObject(PyExc_TypeError, incoming);
        else    {
            out = array_string_from_pylist(tup, arr_lens, num_objects);
            Py_DECREF(iter);
            Py_DECREF(tup);
        }
    }
    return out;
}

static PyObject *pylist_from_array_string(char **lst, size_t *lens, size_t num) {
    PyObject *listObj = PyList_New(num);
    if (!listObj)   {
        PyErr_SetString(PyExc_MemoryError, "Unable to allocate memory for Python list");
        return NULL;
    }
    size_t i;
    for (i = 0; i < num; i++) {
        PyList_SET_ITEM(listObj, i, pybytes_from_chars((unsigned char*)lst[i], lens[i]));
    }
    return listObj;
}

#ifdef _cplusplus
}

#endif

#endif
