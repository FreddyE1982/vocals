import numpy as np
import pytest
from vocals.multitrack import MultiTrackRecorder


class DummySD:
    def __init__(self, data):
        self.data = data
        self.play_called = False

    def rec(self, frames, samplerate=44100, channels=1, dtype="float32"):
        assert frames == len(self.data)
        return self.data.reshape(-1, channels)

    def wait(self):
        pass

    def play(self, data, samplerate=44100):
        self.play_called = True
        self.play_data = data

    def stop(self):
        self.play_called = False


def test_record_and_play(monkeypatch):
    sd_dummy = DummySD(np.arange(4, dtype=np.float32))
    monkeypatch.setattr("vocals.multitrack.sd", sd_dummy)
    rec = MultiTrackRecorder(num_tracks=1, samplerate=4)
    rec.record(duration=1)
    assert np.allclose(rec.tracks[0], sd_dummy.data)
    rec.seek(0)
    rec.play()
    assert sd_dummy.play_called
    assert np.allclose(sd_dummy.play_data, sd_dummy.data)
