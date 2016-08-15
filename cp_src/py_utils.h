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
    PyObject *ret = PyString_Encode(c_str, (Py_ssize_t)str.length(), (char*)"raw_unicode_escape", (char*)"strict");
#endif
    return ret;
}

static vector<string> vector_string_from_pylist(PyObject *incoming)    {
    vector<string> out;
    if (PyList_Check(incoming)) {
        for(Py_ssize_t i = 0; i < PyList_Size(incoming); i++) {
            PyObject *value = PyList_GetItem(incoming, i);
            if (PyBytes_Check(value))
                out.push_back(string(PyBytes_AsString(value)));
            else if (PyUnicode_Check(value))    {
                PyObject *tmp = PyUnicode_AsEncodedString(value, (char*)"raw_unicode_escape", (char*)"strict");
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

static PyObject *pylist_from_vector_string(vector<string> lst) {
    PyObject *listObj = PyList_New( lst.size() );
    if (!listObj) throw logic_error("Unable to allocate memory for Python list");
    for (unsigned int i = 0; i < lst.size(); i++) {
        PyList_SET_ITEM(listObj, i, pybytes_from_string(lst[i]));
    }
    return listObj;    
}

#endif