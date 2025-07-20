# Vocals Recorder

This project provides a simple command line tool to record vocals to a WAV file.
The time critical audio buffering is implemented in C for best performance.

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
