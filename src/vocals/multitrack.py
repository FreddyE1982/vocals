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
        self,
        duration: float,
        countdown: int = 0,
        punch_in: bool = False,
        play_tracks: List[int] | None = None,
    ) -> None:
        """Record for ``duration`` seconds to the selected track.

        If ``play_tracks`` is provided, those tracks will be mixed and played
        back while recording to keep the new recording in sync with the
        existing material. When ``punch_in`` is ``True`` the current track is
        muted during the recording window so previously recorded audio does not
        play over the new take.
        """
        if sd is None:
            raise RuntimeError("sounddevice is not available")

        if countdown > 0:
            for i in range(countdown, 0, -1):
                print(i)
                time.sleep(1)

        frames = int(duration * self.samplerate)
        start = self.position
        end = start + frames
        self._ensure_length(self.selected_track, end)

        playback = None
        if play_tracks is not None:
            playback = np.zeros((frames, self.channels), dtype=np.float32)
            for t in play_tracks:
                if not 0 <= t < len(self.tracks):
                    raise ValueError("invalid track index")
                track = self.tracks[t]
                if start < len(track):
                    seg = track[start:end]
                    if t == self.selected_track and punch_in:
                        seg = np.zeros_like(seg)
                    playback[: len(seg), 0] += seg

        if playback is not None:
            recorded = sd.playrec(
                playback,
                samplerate=self.samplerate,
                channels=self.channels,
                dtype="float32",
            )
        else:
            recorded = sd.rec(
                frames,
                samplerate=self.samplerate,
                channels=self.channels,
                dtype="float32",
            )

        sd.wait()

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

    # Import/Export ---------------------------------------------------------

    def import_audio(self, filename: str, track_index: int | None = None) -> None:
        """Load a WAV or MP3 file into ``track_index`` replacing its contents."""
        import os
        import wave

        if track_index is None:
            track_index = self.selected_track
        if not 0 <= track_index < len(self.tracks):
            raise ValueError("invalid track index")

        ext = os.path.splitext(filename)[1].lower()
        if ext == ".wav":
            with wave.open(filename, "rb") as wf:
                if wf.getnchannels() != self.channels:
                    raise ValueError("channel count mismatch")
                if wf.getframerate() != self.samplerate:
                    raise ValueError("samplerate mismatch")
                frames = wf.getnframes()
                data = (
                    np.frombuffer(wf.readframes(frames), dtype="<i2").astype(np.float32)
                    / 32767.0
                )
        else:
            try:
                from pydub import AudioSegment
            except Exception as e:  # pragma: no cover - optional dependency
                raise RuntimeError("pydub required for mp3 import") from e

            audio = AudioSegment.from_file(filename)
            if audio.frame_rate != self.samplerate:
                audio = audio.set_frame_rate(self.samplerate)
            if audio.channels != self.channels:
                audio = audio.set_channels(self.channels)
            samples = audio.get_array_of_samples()
            data = np.array(samples, dtype=np.float32) / 32767.0

        self.tracks[track_index] = data
        self.position = 0

    def export_audio(
        self, filename: str, track_indices: List[int] | None = None
    ) -> None:
        """Mix ``track_indices`` and export to a WAV or MP3 file."""
        import os
        import wave

        mix = self.mix_tracks(track_indices)
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".wav":
            with wave.open(filename, "wb") as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)
                wf.setframerate(self.samplerate)
                wf.writeframes((mix * 32767).astype("<i2").tobytes())
        else:
            try:
                from pydub import AudioSegment
            except Exception as e:  # pragma: no cover - optional dependency
                raise RuntimeError("pydub required for mp3 export") from e

            segment = AudioSegment(
                (mix * 32767).astype("<i2").tobytes(),
                frame_rate=self.samplerate,
                sample_width=2,
                channels=self.channels,
            )
            segment.export(filename, format="mp3")

    def mix_tracks(self, track_indices: List[int] | None = None) -> np.ndarray:
        """Return a mix of ``track_indices`` or all tracks."""
        if track_indices is None:
            track_indices = list(range(len(self.tracks)))
        max_len = (
            max(len(self.tracks[i]) for i in track_indices) if track_indices else 0
        )
        mix = np.zeros(max_len, dtype=np.float32)
        for i in track_indices:
            track = self.tracks[i]
            mix[: len(track)] += track
        return mix
