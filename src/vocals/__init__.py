"""Vocals recording package."""

from .multitrack import MultiTrackRecorder
from .utils import estimate_pitch, freq_to_note, note_to_freq, pitch_range

__version__ = "0.1.0"

__all__ = [
    "MultiTrackRecorder",
    "estimate_pitch",
    "pitch_range",
    "note_to_freq",
    "freq_to_note",
    "__version__",
]
