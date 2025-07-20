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


def test_copy_paste_between_tracks():
    rec = MultiTrackRecorder(num_tracks=2, samplerate=1)
    rec.tracks[0] = np.array([1, 2, 3, 4], dtype=np.float32)
    rec.select_range(1, 3, track_index=0)
    rec.copy()
    rec.position = 4
    rec.paste(track_index=0)
    assert np.allclose(rec.tracks[0], np.array([1, 2, 3, 4, 2, 3], dtype=np.float32))


def test_cut_move_to_other_track():
    rec = MultiTrackRecorder(num_tracks=2, samplerate=1)
    rec.tracks[0] = np.array([1, 2, 3, 4], dtype=np.float32)
    rec.tracks[1] = np.array([5, 6], dtype=np.float32)
    rec.select_range(1, 3, track_index=0)
    rec.move(to_track_index=1, position_seconds=2)
    assert np.allclose(rec.tracks[0], np.array([1, 4], dtype=np.float32))
    assert np.allclose(rec.tracks[1], np.array([5, 6, 2, 3], dtype=np.float32))


def test_import_export_wav(tmp_path):
    filename = tmp_path / "sample.wav"
    data = np.array([0, 1, -1, 0.5], dtype=np.float32)
    import wave

    with wave.open(str(filename), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(44100)
        wf.writeframes((data * 32767).astype("<i2").tobytes())

    rec = MultiTrackRecorder(num_tracks=1, samplerate=44100)
    rec.import_audio(str(filename))
    assert np.allclose(rec.tracks[0], data, atol=1e-4)

    out = tmp_path / "mix.wav"
    rec.export_audio(str(out))
    with wave.open(str(out), "rb") as wf:
        frames = wf.readframes(wf.getnframes())
        result = np.frombuffer(frames, dtype="<i2").astype(np.float32) / 32767
    assert np.allclose(result, data, atol=1e-4)
