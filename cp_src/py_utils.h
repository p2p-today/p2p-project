#ifndef CP2P_PY_UTILS
#define CP2P_PY_UTILS TRUE

#include <Python.h>
#include <bytesobject.h>
#include <string>

#ifdef _cplusplus

#include <stdexcept>

extern "C"  {
#endif

static PyObject *pybytes_from_string(unsigned char *str, size_t len)   {
    Py_buffer buffer;
    int res = PyBuffer_FillInfo(&buffer, 0, str, (Py_ssize_t)len, true, PyBUF_CONTIG_RO);
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

#ifdef _cplusplus
}
#endif

using namespace std;

static PyObject *pybytes_from_string(string str)   {
    unsigned char* c_str = (unsigned char*)str.c_str();
    size_t len = str.length();
    return pybytes_from_string(c_str, len);
}

static string string_from_pybytes(PyObject *bytes)  {
    if (PyBytes_Check(bytes))   {
        CP2P_DEBUG("Decoding as bytes\n")
        char *buff = NULL;
        Py_ssize_t len = 0;
        PyBytes_AsStringAndSize(bytes, &buff, &len);
        return string(buff, len);
    }
#if PY_MAJOR_VERSION >= 3
    else if (PyObject_CheckBuffer(bytes))   {
        CP2P_DEBUG("Decoding as buffer\n")
        PyObject *tmp = PyBytes_FromObject(bytes);
        string ret = string_from_pybytes(tmp);
        Py_XDECREF(tmp);
        return ret;
    }
#else
    else if (PyByteArray_Check(bytes))  {
        CP2P_DEBUG("Decoding as bytearray\n")
        char *buff = PyByteArray_AS_STRING(bytes);
        Py_ssize_t len = PyByteArray_GET_SIZE(bytes);
        return string(buff, len);
    }
#endif
    else if (PyUnicode_Check(bytes))    {
        CP2P_DEBUG("Decoding as unicode (incoming recursion)\n")
        PyObject *tmp = PyUnicode_AsEncodedString(bytes, (char*)"utf-8", (char*)"strict");
        string ret = string_from_pybytes(tmp);
        Py_XDECREF(tmp);
        return ret;
    }
    else    {
        PyErr_SetObject(PyExc_TypeError, bytes);
        return string();
    }
}

static vector<string> vector_string_from_pylist(PyObject *incoming)    {
    vector<string> out;
    if (PyList_Check(incoming)) {
        for(Py_ssize_t i = 0; i < PyList_Size(incoming); i++) {
            PyObject *value = PyList_GetItem(incoming, i);
            out.push_back(string_from_pybytes(value));
            if (PyErr_Occurred())
                return out;
        }
    }
    else if (PyTuple_Check(incoming)) {
        for(Py_ssize_t i = 0; i < PyTuple_Size(incoming); i++) {
            PyObject *value = PyTuple_GetItem(incoming, i);
            out.push_back(string_from_pybytes(value));
            if (PyErr_Occurred())
                return out;
        }
    }
    else {
        PyObject *iter = PyObject_GetIter(incoming);
        if (PyErr_Occurred())
            PyErr_SetObject(PyExc_TypeError, incoming);
        else    {
            PyObject *item;
            while ((item = PyIter_Next(iter)) != NULL)  {
                out.push_back(string_from_pybytes(item));
                Py_DECREF(item);
                if (PyErr_Occurred())   {
                    Py_DECREF(iter);
                    return out;
                }
            }
            Py_DECREF(iter);
        }
    }
    return out;
}

static PyObject *pylist_from_vector_string(vector<string> lst) {
    PyObject *listObj = PyList_New( lst.size() );
    if (!listObj)   {
        PyErr_SetString(PyExc_MemoryError, "Unable to allocate memory for Python list");
        return NULL;
    }
    for (unsigned int i = 0; i < lst.size(); i++) {
        PyList_SET_ITEM(listObj, i, pybytes_from_string(lst[i]));
    }
    return listObj;
}

#endif
