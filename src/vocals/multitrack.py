import time
from typing import List

import numpy as np

try:
    import sounddevice as sd
except Exception as e:  # pragma: no cover - dependency missing in tests
    sd = None


class MultiTrackRecorder:
    """Simple multi track recorder supporting seek and punch-in recording."""

    def __init__(self, num_tracks: int = 2, samplerate: int = 44100, channels: int = 1):
        self.samplerate = samplerate
        self.channels = channels
        self.tracks: List[np.ndarray] = [
            np.zeros(0, dtype=np.float32) for _ in range(num_tracks)
        ]
        self.selected_track = 0
        self.position = 0  # current play/record position in samples
        self.selection: tuple[int, int, int] | None = None
        self.clipboard: np.ndarray = np.zeros(0, dtype=np.float32)

    def select_track(self, index: int) -> None:
        """Select track index for recording and playback."""
        if not 0 <= index < len(self.tracks):
            raise ValueError("invalid track index")
        self.selected_track = index
        self.position = 0

    def seek(self, seconds: float) -> None:
        """Seek to position in seconds."""
        if seconds < 0:
            raise ValueError("seconds must be positive")
        self.position = int(seconds * self.samplerate)
        self._ensure_length(self.selected_track, self.position)

    def _ensure_length(self, track_index: int, length: int) -> None:
        track = self.tracks[track_index]
        if len(track) < length:
            pad = np.zeros(length - len(track), dtype=np.float32)
            self.tracks[track_index] = np.concatenate([track, pad])

    def record(
        self, duration: float, countdown: int = 0, punch_in: bool = False
    ) -> None:
        """Record for ``duration`` seconds to the selected track."""
        if sd is None:
            raise RuntimeError("sounddevice is not available")
        if countdown > 0:
            for i in range(countdown, 0, -1):
                print(i)
                time.sleep(1)
        frames = int(duration * self.samplerate)
        recorded = sd.rec(
            frames, samplerate=self.samplerate, channels=self.channels, dtype="float32"
        )
        sd.wait()
        start = self.position
        end = start + frames
        self._ensure_length(self.selected_track, end)
        track = self.tracks[self.selected_track]
        track[start:end] = recorded[:, 0]
        self.position = end

    def play(self, duration: float | None = None) -> None:
        """Play from current position for ``duration`` seconds if given."""
        if sd is None:
            raise RuntimeError("sounddevice is not available")
        max_len = max(len(t) for t in self.tracks)
        if duration is None:
            end = max_len
        else:
            end = min(self.position + int(duration * self.samplerate), max_len)
        if end <= self.position:
            return
        length = end - self.position
        mix = np.zeros(length, dtype=np.float32)
        for track in self.tracks:
            if self.position < len(track):
                segment = track[self.position : end]
                mix[: len(segment)] += segment
        sd.play(mix, samplerate=self.samplerate)
        sd.wait()
        self.position = end

    def pause(self) -> None:
        """Stop playback or recording."""
        if sd is not None:
            sd.stop()

    # Editing functionality -------------------------------------------------

    def select_range(
        self,
        start_seconds: float,
        end_seconds: float,
        track_index: int | None = None,
    ) -> None:
        """Select a region on a track between ``start_seconds`` and ``end_seconds``."""
        if start_seconds < 0 or end_seconds <= start_seconds:
            raise ValueError("invalid selection range")
        if track_index is None:
            track_index = self.selected_track
        if not 0 <= track_index < len(self.tracks):
            raise ValueError("invalid track index")
        start = int(start_seconds * self.samplerate)
        end = int(end_seconds * self.samplerate)
        self._ensure_length(track_index, end)
        self.selection = (track_index, start, end)
        self.position = start

    def copy(self) -> None:
        """Copy the currently selected audio to the clipboard."""
        if self.selection is None:
            raise RuntimeError("nothing selected")
        t, start, end = self.selection
        self.clipboard = self.tracks[t][start:end].copy()

    def cut(self) -> None:
        """Cut the selected audio to the clipboard."""
        if self.selection is None:
            raise RuntimeError("nothing selected")
        t, start, end = self.selection
        self.clipboard = self.tracks[t][start:end].copy()
        track = self.tracks[t]
        self.tracks[t] = np.concatenate([track[:start], track[end:]])
        self.position = start
        self.selection = None

    def paste(self, track_index: int | None = None) -> None:
        """Paste clipboard audio to ``track_index`` at the current position."""
        if self.clipboard.size == 0:
            return
        if track_index is None:
            track_index = self.selected_track
        if not 0 <= track_index < len(self.tracks):
            raise ValueError("invalid track index")
        track = self.tracks[track_index]
        self._ensure_length(track_index, self.position)
        self.tracks[track_index] = np.concatenate(
            [track[: self.position], self.clipboard, track[self.position :]]
        )
        self.position += len(self.clipboard)

    def move(self, to_track_index: int, position_seconds: float | None = None) -> None:
        """Move selected audio to ``to_track_index`` at ``position_seconds``."""
        self.cut()
        if position_seconds is not None:
            self.position = int(position_seconds * self.samplerate)
        self.selected_track = to_track_index
        self.paste()
