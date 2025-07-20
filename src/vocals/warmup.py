import argparse
import math

from . import utils


def warmup(
    start_freq: float = 220.0,
    steps: int = 8,
    duration: float = 0.5,
    up_down: bool = True,
) -> None:
    """Play a warmup scale to help singers get ready."""

    freqs = [start_freq * math.pow(2, i / 12) for i in range(steps)]
    if up_down and steps > 1:
        freqs += freqs[-2::-1]
    for f in freqs:
        utils.beep(f, duration=duration)


def main() -> None:
    parser = argparse.ArgumentParser(description="Play a simple warmup scale")
    parser.add_argument(
        "--start", type=float, default=220.0, help="Starting frequency in Hz"
    )
    parser.add_argument("--steps", type=int, default=8, help="Number of semitone steps")
    parser.add_argument(
        "--duration", type=float, default=0.5, help="Beep duration in seconds"
    )
    parser.add_argument(
        "--no-down", action="store_true", help="Don't descend back to the start"
    )
    args = parser.parse_args()
    warmup(
        start_freq=args.start,
        steps=args.steps,
        duration=args.duration,
        up_down=not args.no_down,
    )


if __name__ == "__main__":
    main()
