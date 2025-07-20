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
