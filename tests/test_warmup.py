import numpy as np

from vocals import warmup


def test_warmup_beeps(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "vocals.warmup.utils.beep",
        lambda freq, duration=0.5, samplerate=44100: calls.append(freq),
    )
    warmup.warmup(start_freq=100, steps=3, duration=0.1)
    semitone = 2 ** (1 / 12)
    expected = [100, 100 * semitone, 100 * (semitone**2), 100 * semitone, 100]
    assert [round(f, 3) for f in calls] == [round(f, 3) for f in expected]
