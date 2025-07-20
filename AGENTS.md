# Guidelines for `vocals` Repository

This project contains a simple audio recording tool written in Python with a C
extension for time critical parts. When making changes keep the following rules
in mind:

## Code style
- Use `black` for formatting Python code.
- C code should be formatted with `clang-format` (LLVM style).
- Keep functions short and well documented with docstrings or comments.

## Building
- Install dependencies using `pip install -r requirements.txt`.
- Build the extension in place with `python setup.py build_ext --inplace`.
- The recording script requires the PortAudio library on the system. On Debian
  based systems install `libportaudio2` and `libportaudio-dev`.

## Testing
- Run tests with `pytest` from the repository root.
- Ensure tests pass before committing.

## Pull request notes
- Summarize major changes and mention if any tests failed.
