import numpy as np
from vocals import ringbuffer


def test_write_read():
    rb = ringbuffer.RingBuffer(10)
    data = np.arange(5, dtype=np.float32)
    assert rb.write(data) == 5
    out = rb.read(5)
    assert len(out) == 5 * 4
    result = np.frombuffer(out, dtype=np.float32)
    assert np.allclose(result, data)
