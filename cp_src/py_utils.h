#ifndef CP2P_PY_UTILS
#define CP2P_PY_UTILS TRUE

#include <Python.h>
#include <bytesobject.h>
#include <stdexcept>
#include <string>

using namespace std;

static PyObject *pybytes_from_string(string str)   {
    unsigned char* c_str = (unsigned char*)str.c_str();
    Py_buffer buffer;
    int res = PyBuffer_FillInfo(&buffer, 0, c_str, (Py_ssize_t)str.length(), true, PyBUF_CONTIG_RO);
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
    PyObject *ret = PyString_Encode((char*)c_str, (Py_ssize_t)str.length(), (char*)"raw_unicode_escape", (char*)"strict");
#endif
    return ret;
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
    if (!listObj) throw logic_error("Unable to allocate memory for Python list");
    for (unsigned int i = 0; i < lst.size(); i++) {
        PyList_SET_ITEM(listObj, i, pybytes_from_string(lst[i]));
    }
    return listObj;    
}

#endif