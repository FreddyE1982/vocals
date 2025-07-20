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
