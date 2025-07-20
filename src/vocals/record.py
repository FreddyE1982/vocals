import argparse
import time
import numpy as np

from . import utils

try:
    import sounddevice as sd
except Exception as e:
    raise SystemExit("sounddevice is required: %s" % e)

try:
    from . import ringbuffer
except Exception as e:
    raise SystemExit("ringbuffer extension not built: %s" % e)


def record_to_file(
    filename,
    duration=5,
    samplerate=44100,
    channels=1,
    countdown=0,
    metronome_bpm=None,
):
    """Record audio from the default microphone and save to a WAV file."""
    buffer = ringbuffer.RingBuffer(int(samplerate * channels))
    recorded = []

    if countdown > 0:
        for i in range(countdown, 0, -1):
            print(i)
            freq = 880 if (countdown - i) % 2 == 0 else 660
            utils.beep(freq, samplerate=samplerate)
            time.sleep(1)

    def callback(indata, frames, time_info, status):
        written = buffer.write(indata.astype("float32").ravel())
        if written < len(indata.ravel()):
            print("buffer overflow")
        out = buffer.read(frames * channels)
        if out:
            recorded.append(np.frombuffer(out, dtype=np.float32))

    stop = None
    if metronome_bpm:
        import threading

        stop = threading.Event()

        def metro():
            interval = 60.0 / metronome_bpm
            while not stop.is_set():
                utils.beep(880, samplerate=samplerate, duration=0.05)
                time.sleep(interval)

        thread = threading.Thread(target=metro)
        thread.start()

    with sd.InputStream(channels=channels, samplerate=samplerate, callback=callback):
        sd.sleep(int(duration * 1000))

    if stop is not None:
        stop.set()
        thread.join()

    if recorded:
        data = np.concatenate(recorded)
    else:
        data = np.array([], dtype=np.float32)

    import wave

    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(samplerate)
        wf.writeframes((data * 32767).astype("<i2").tobytes())


def main():
    parser = argparse.ArgumentParser(description="Record vocals to a WAV file")
    parser.add_argument("outfile", help="Output WAV filename")
    parser.add_argument(
        "-d", "--duration", type=float, default=5, help="Duration in seconds"
    )
    parser.add_argument("-r", "--rate", type=int, default=44100, help="Sample rate")
    parser.add_argument(
        "-c",
        "--countdown",
        type=int,
        default=0,
        help="Countdown in seconds before recording starts",
    )
    parser.add_argument(
        "--bpm",
        type=int,
        default=None,
        help="Play a metronome click at this tempo while recording",
    )
    args = parser.parse_args()
    record_to_file(
        args.outfile,
        args.duration,
        args.rate,
        countdown=args.countdown,
        metronome_bpm=args.bpm,
    )


if __name__ == "__main__":
    main()
