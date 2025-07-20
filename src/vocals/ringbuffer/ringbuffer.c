#include <Python.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
  float *buffer;
  size_t capacity;
  size_t head;
  size_t tail;
  size_t size;
} RingBuffer;

static RingBuffer *rb_create(size_t capacity) {
  RingBuffer *rb = (RingBuffer *)malloc(sizeof(RingBuffer));
  if (!rb)
    return NULL;
  rb->buffer = (float *)malloc(capacity * sizeof(float));
  if (!rb->buffer) {
    free(rb);
    return NULL;
  }
  rb->capacity = capacity;
  rb->head = rb->tail = rb->size = 0;
  return rb;
}

static void rb_free(RingBuffer *rb) {
  if (!rb)
    return;
  free(rb->buffer);
  free(rb);
}

static size_t rb_write(RingBuffer *rb, const float *data, size_t count) {
  size_t written = 0;
  while (written < count && rb->size < rb->capacity) {
    rb->buffer[rb->head] = data[written];
    rb->head = (rb->head + 1) % rb->capacity;
    rb->size++;
    written++;
  }
  return written;
}

static size_t rb_read(RingBuffer *rb, float *out, size_t count) {
  size_t read = 0;
  while (read < count && rb->size > 0) {
    out[read] = rb->buffer[rb->tail];
    rb->tail = (rb->tail + 1) % rb->capacity;
    rb->size--;
    read++;
  }
  return read;
}

// Python wrapper

typedef struct {
  PyObject_HEAD RingBuffer *rb;
} PyRingBuffer;

static int PyRingBuffer_init(PyRingBuffer *self, PyObject *args,
                             PyObject *kwds) {
  size_t capacity;
  if (!PyArg_ParseTuple(args, "n", &capacity)) {
    return -1;
  }
  self->rb = rb_create(capacity);
  if (!self->rb) {
    PyErr_SetString(PyExc_MemoryError, "Failed to allocate ring buffer");
    return -1;
  }
  return 0;
}

static void PyRingBuffer_dealloc(PyRingBuffer *self) {
  rb_free(self->rb);
  Py_TYPE(self)->tp_free((PyObject *)self);
}

static PyObject *PyRingBuffer_write(PyRingBuffer *self, PyObject *obj) {
  Py_buffer view;
  if (PyObject_GetBuffer(obj, &view, PyBUF_CONTIG_RO | PyBUF_FORMAT) != 0) {
    return NULL;
  }
  if (view.ndim != 1 || strcmp(view.format, "f") != 0) {
    PyErr_SetString(PyExc_TypeError, "expected a float array");
    PyBuffer_Release(&view);
    return NULL;
  }
  size_t count = view.len / sizeof(float);
  size_t written = rb_write(self->rb, (const float *)view.buf, count);
  PyBuffer_Release(&view);
  return PyLong_FromSize_t(written);
}

static PyObject *PyRingBuffer_read(PyRingBuffer *self, PyObject *args) {
  Py_ssize_t count;
  if (!PyArg_ParseTuple(args, "n", &count)) {
    return NULL;
  }
  PyObject *array = PyBytes_FromStringAndSize(NULL, count * sizeof(float));
  if (!array)
    return NULL;
  char *buf = PyBytes_AS_STRING(array);
  size_t read = rb_read(self->rb, (float *)buf, (size_t)count);
  if (read < (size_t)count) {
    _PyBytes_Resize(&array, read * sizeof(float));
  }
  return array;
}

static PyMethodDef PyRingBuffer_methods[] = {
    {"write", (PyCFunction)PyRingBuffer_write, METH_O,
     "Write floats to the buffer"},
    {"read", (PyCFunction)PyRingBuffer_read, METH_VARARGS,
     "Read floats from the buffer"},
    {NULL, NULL, 0, NULL}};

static PyTypeObject PyRingBufferType = {
    PyVarObject_HEAD_INIT(NULL, 0).tp_name = "ringbuffer.RingBuffer",
    .tp_basicsize = sizeof(PyRingBuffer),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_doc = "Ring buffer for float samples",
    .tp_methods = PyRingBuffer_methods,
    .tp_new = PyType_GenericNew,
    .tp_init = (initproc)PyRingBuffer_init,
    .tp_dealloc = (destructor)PyRingBuffer_dealloc,
};

static PyModuleDef ringbuffermodule = {
    PyModuleDef_HEAD_INIT,
    .m_name = "ringbuffer",
    .m_size = -1,
};

PyMODINIT_FUNC PyInit_ringbuffer(void) {
  PyObject *m;
  if (PyType_Ready(&PyRingBufferType) < 0)
    return NULL;

  m = PyModule_Create(&ringbuffermodule);
  if (!m)
    return NULL;

  Py_INCREF(&PyRingBufferType);
  if (PyModule_AddObject(m, "RingBuffer", (PyObject *)&PyRingBufferType) < 0) {
    Py_DECREF(&PyRingBufferType);
    Py_DECREF(m);
    return NULL;
  }

  return m;
}
