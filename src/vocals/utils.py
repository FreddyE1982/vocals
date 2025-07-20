import numpy as np

try:
    import sounddevice as sd
except Exception:  # pragma: no cover - dependency missing in tests
    sd = None


def beep_sound(
    frequency: float, samplerate: int = 44100, duration: float = 0.2
) -> np.ndarray:
    """Return a sine wave beep of ``frequency`` Hz."""

    t = np.linspace(0, duration, int(samplerate * duration), False)
    return np.sin(2 * np.pi * frequency * t).astype(np.float32)


def beep(frequency: float, samplerate: int = 44100, duration: float = 0.2) -> None:
    """Play a short beep of ``frequency`` Hz using ``sounddevice``."""

    if sd is None:
        return

    tone = beep_sound(frequency, samplerate=samplerate, duration=duration)
    sd.play(tone, samplerate=samplerate)
    sd.wait()


def note_to_freq(note: str) -> float:
    """Return frequency in Hz for a note like ``"A4"``."""

    note = note.strip().upper()
    if len(note) < 2:
        raise ValueError("invalid note")

    if note[1] in {"#", "B"}:
        key = note[:2]
        rest = note[2:]
    else:
        key = note[0]
        rest = note[1:]

    try:
        octave = int(rest)
    except ValueError as exc:
        raise ValueError("invalid octave") from exc

    offsets = {
        "C": -9,
        "C#": -8,
        "DB": -8,
        "D": -7,
        "D#": -6,
        "EB": -6,
        "E": -5,
        "F": -4,
        "F#": -3,
        "GB": -3,
        "G": -2,
        "G#": -1,
        "AB": -1,
        "A": 0,
        "A#": 1,
        "BB": 1,
        "B": 2,
    }

    if key not in offsets:
        raise ValueError("invalid note")

    semitones = offsets[key] + 12 * (octave - 4)
    return 440.0 * (2 ** (semitones / 12))


def estimate_pitch(samples: np.ndarray, samplerate: int = 44100) -> float | None:
    """Estimate fundamental frequency of ``samples`` using auto-correlation."""

    if samples.ndim > 1:
        samples = samples[:, 0]

    samples = samples.astype(np.float32, copy=False)
    samples = samples - np.mean(samples)
    if np.max(np.abs(samples)) < 1e-3:
        return None

    corr = np.correlate(samples, samples, mode="full")
    corr = corr[len(corr) // 2 :]
    d = np.diff(corr)
    positive = np.where(d > 0)[0]
    if positive.size == 0:
        return None
    start = positive[0]
    peak = start + np.argmax(corr[start:])
    if peak == 0:
        return None
    return float(samplerate) / float(peak)


def pitch_range(
    samples: np.ndarray, samplerate: int = 44100, frame_size: int = 2048
) -> tuple[float, float] | None:
    """Return estimated min and max pitch for ``samples``."""

    if samples.ndim > 1:
        samples = samples[:, 0]

    pitches: list[float] = []
    hop = frame_size // 2
    for i in range(0, len(samples) - frame_size, hop):
        frame = samples[i : i + frame_size]
        pitch = estimate_pitch(frame, samplerate)
        if pitch is not None:
            pitches.append(pitch)

    if not pitches:
        return None

    return min(pitches), max(pitches)


def freq_to_note(freq: float) -> str:
    """Return the closest note name for ``freq`` in Hz."""

    if freq <= 0:
        raise ValueError("frequency must be positive")

    semitones = round(12 * np.log2(freq / 440.0))
    note_index = (semitones + 9) % 12
    octave = 4 + (semitones + 9) // 12
    names = [
        "C",
        "C#",
        "D",
        "D#",
        "E",
        "F",
        "F#",
        "G",
        "G#",
        "A",
        "A#",
        "B",
    ]
    return f"{names[note_index]}{octave}"
