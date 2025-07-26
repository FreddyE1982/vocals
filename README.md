# Vocals Recorder

This project provides a simple command line tool to record vocals to a WAV file.
The time critical audio buffering is implemented in C for best performance.

The package now also includes a basic multi track recorder. The
``MultiTrackRecorder`` class allows recording multiple tracks, seeking within
a track and mixing them for playback. Recording can optionally start after a
countdown and supports punch‑in recording where audio is overwritten from the
current position. The recorder also allows selecting parts of tracks and
cutting, copying or pasting them between tracks for simple editing. Audio can
be imported from WAV or MP3 files and a mix of tracks can be exported back to
WAV or MP3.

The recorder features a simple *take library*. Portions of a track can be
selected and stored as a take. Additional takes for the same region can be
recorded using automatic punch‑in recording and are kept together in the
library. A stored take can be reapplied to replace the current audio for that
selection.

The ``vocals.utils`` module now provides simple pitch analysis helpers. A
recorded track's pitch range can be inspected using
``MultiTrackRecorder.pitch_range``. This helps vocalists monitor the lowest and
highest notes they hit during a take.

The ``record`` method now accepts a ``metronome_bpm`` argument to play a click
track while recording. The command line ``record`` tool also supports a
``--bpm`` option so vocalists can keep time even when no other tracks are
available.

The ``record`` command also has a ``--reference`` option to play a short
reference note before recording begins. Notes can be given as a frequency or a
note name like ``A4`` which is converted using ``vocals.utils.note_to_freq``.
The ``vocals.utils.freq_to_note`` helper performs the reverse conversion and
can be used to display the nearest note for a detected pitch.

When using ``python -m vocals.record`` the ``--show-range`` flag will print the
detected pitch range of the take once recording finishes. Additionally the
``vocals.warmup`` module can play a simple ascending and descending scale to
help warm up the voice:

```bash
python -m vocals.warmup
```

## Usage

```bash
python -m vocals.record output.wav -d 10
```

To build the extension in place run:

```bash
pip install -r requirements.txt
python setup.py build_ext --inplace
pip install -e .
```

You can also build the project inside a Docker container:

```bash
docker build -t vocals .
```

Recording requires the PortAudio library to be available on the system.
MP3 import and export require the ``pydub`` package and ``ffmpeg`` to be
installed.
