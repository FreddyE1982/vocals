"""Vocals recording package."""

from .multitrack import MultiTrackRecorder
from .utils import estimate_pitch, note_to_freq, pitch_range, freq_to_note

__all__ = [
    "MultiTrackRecorder",
    "estimate_pitch",
    "pitch_range",
    "note_to_freq",
    "freq_to_note",
]
