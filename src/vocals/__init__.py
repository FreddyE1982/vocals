"""Vocals recording package."""

from .multitrack import MultiTrackRecorder
from .utils import estimate_pitch, pitch_range

__all__ = ["MultiTrackRecorder", "estimate_pitch", "pitch_range"]
