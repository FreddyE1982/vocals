from setuptools import Extension, setup

ringbuffer_ext = Extension(
    "vocals.ringbuffer",
    sources=["src/vocals/ringbuffer/ringbuffer.c"],
)

setup(
    name="vocals",
    version="0.1.0",
    packages=["vocals"],
    package_dir={"": "src"},
    ext_modules=[ringbuffer_ext],
)
