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

    def playrec(self, play_data, samplerate=44100, channels=1, dtype="float32"):
        # play_data is array with same length as data
        self.play(play_data, samplerate)
        return self.rec(len(play_data), samplerate, channels, dtype)

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


def test_record_with_metronome(monkeypatch):
    record_data = np.zeros(10, dtype=np.float32)
    sd_dummy = DummySD(record_data)
    monkeypatch.setattr("vocals.multitrack.sd", sd_dummy)
    monkeypatch.setattr(
        "vocals.multitrack.utils.beep_sound",
        lambda *a, **k: np.ones(3, dtype=np.float32),
    )

    rec = MultiTrackRecorder(num_tracks=1, samplerate=10)
    rec.record(duration=1, metronome_bpm=120)

    expected = np.zeros((10, 1), dtype=np.float32)
    expected[0:3, 0] += 1
    expected[5:8, 0] += 1
    assert np.allclose(sd_dummy.play_data, expected)


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


def test_playback_during_record(monkeypatch):
    # track 0 provides playback material while recording track 1
    record_data = np.array([10, 11, 12, 13], dtype=np.float32)
    sd_dummy = DummySD(record_data)
    monkeypatch.setattr("vocals.multitrack.sd", sd_dummy)

    rec = MultiTrackRecorder(num_tracks=2, samplerate=4)
    rec.tracks[0] = np.array([1, 2, 3, 4], dtype=np.float32)
    rec.select_track(1)
    rec.record(duration=1, play_tracks=[0])

    assert np.allclose(rec.tracks[1], record_data)
    assert np.allclose(sd_dummy.play_data[:, 0], rec.tracks[0])


def test_countdown_with_playback(monkeypatch):
    record_data = np.array([5, 6, 7, 8], dtype=np.float32)
    sd_dummy = DummySD(record_data)
    monkeypatch.setattr("vocals.multitrack.sd", sd_dummy)

    sleeps = []
    monkeypatch.setattr("time.sleep", lambda s: sleeps.append(s))
    beeps = []
    monkeypatch.setattr(
        "vocals.multitrack.utils.beep",
        lambda freq, samplerate=44100, duration=0.2: beeps.append(freq),
    )

    rec = MultiTrackRecorder(num_tracks=2, samplerate=4)
    rec.tracks[0] = np.array([1, 1, 1, 1], dtype=np.float32)
    rec.select_track(1)
    rec.record(duration=1, countdown=2, play_tracks=[0])

    assert sleeps == [1, 1]
    assert beeps == [880, 660]
    assert np.allclose(sd_dummy.play_data[:, 0], rec.tracks[0])


def test_pitch_range_method():
    sr = 8000
    rec = MultiTrackRecorder(num_tracks=1, samplerate=sr)
    t = np.linspace(0, 1, sr, False)
    part1 = np.sin(2 * np.pi * 220 * t[: sr // 2])
    part2 = np.sin(2 * np.pi * 440 * t[: sr // 2])
    rec.tracks[0] = np.concatenate([part1, part2]).astype(np.float32)
    low, high = rec.pitch_range()
    assert low == pytest.approx(220, rel=0.05)
    assert high == pytest.approx(440, rel=0.05)
