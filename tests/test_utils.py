import numpy as np
import pytest

from vocals import utils


def test_estimate_pitch():
    samplerate = 8000
    t = np.linspace(0, 1, samplerate, False)
    tone = np.sin(2 * np.pi * 440 * t).astype(np.float32)
    pitch = utils.estimate_pitch(tone, samplerate=samplerate)
    assert pitch == pytest.approx(440, rel=0.02)


def test_pitch_range():
    samplerate = 8000
    t = np.linspace(0, 1, samplerate, False)
    tone_low = np.sin(2 * np.pi * 220 * t[: samplerate // 2])
    tone_high = np.sin(2 * np.pi * 660 * t[: samplerate // 2])
    samples = np.concatenate([tone_low, tone_high]).astype(np.float32)
    low, high = utils.pitch_range(samples, samplerate=samplerate)
    assert low == pytest.approx(220, rel=0.05)
    assert high == pytest.approx(660, rel=0.05)


def test_note_to_freq():
    assert utils.note_to_freq("A4") == pytest.approx(440.0, rel=0.001)
    assert utils.note_to_freq("C4") == pytest.approx(261.63, rel=0.01)


def test_freq_to_note():
    assert utils.freq_to_note(440.0) == "A4"
    assert utils.freq_to_note(261.63) == "C4"
