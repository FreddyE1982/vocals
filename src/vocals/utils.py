import numpy as np

try:
    import sounddevice as sd
except Exception:  # pragma: no cover - dependency missing in tests
    sd = None


def beep(frequency: float, samplerate: int = 44100, duration: float = 0.2) -> None:
    """Play a short beep of ``frequency`` Hz using ``sounddevice``."""
    if sd is None:
        return
    t = np.linspace(0, duration, int(samplerate * duration), False)
    tone = np.sin(2 * np.pi * frequency * t).astype(np.float32)
    sd.play(tone, samplerate=samplerate)
    sd.wait()
