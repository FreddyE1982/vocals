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

## Usage

```bash
python -m vocals.record output.wav -d 10
```

To build the extension in place run:

```bash
pip install -r requirements.txt
python setup.py build_ext --inplace
```

Recording requires the PortAudio library to be available on the system.
MP3 import and export require the ``pydub`` package and ``ffmpeg`` to be
installed.
