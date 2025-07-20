import numpy as np
import importlib
import sys
import types


class DummyBuffer:
    def __init__(self, size):
        self.data = []

    def write(self, arr):
        self.data.extend(arr)
        return len(arr)

    def read(self, n):
        out = self.data[:n]
        self.data = self.data[n:]
        return np.array(out, dtype=np.float32).tobytes()


class DummyStream:
    def __init__(self, data, callback):
        self.data = data.reshape(-1, 1)
        self.callback = callback

    def __enter__(self):
        self.callback(self.data, len(self.data), None, None)
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class DummySD:
    def __init__(self, data, samplerate):
        self.data = data
        self.samplerate = samplerate

    def InputStream(self, channels=1, samplerate=44100, callback=None):
        assert samplerate == self.samplerate
        return DummyStream(self.data, callback)

    def sleep(self, ms):
        pass


def test_record_prints_range(tmp_path, monkeypatch, capsys):
    data = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 10, False)).astype(np.float32)

    sd_stub = types.SimpleNamespace()
    monkeypatch.setitem(sys.modules, "sounddevice", sd_stub)
    record = importlib.import_module("vocals.record")

    sd_dummy = DummySD(data, 10)
    monkeypatch.setattr(record, "sd", sd_dummy)
    monkeypatch.setattr(record.ringbuffer, "RingBuffer", lambda size: DummyBuffer(size))
    monkeypatch.setattr(
        record.utils, "pitch_range", lambda samples, samplerate=10: (430.0, 450.0)
    )
    outfile = tmp_path / "out.wav"
    record.record_to_file(str(outfile), duration=1, samplerate=10, show_range=True)
    captured = capsys.readouterr().out
    assert "Pitch range" in captured
