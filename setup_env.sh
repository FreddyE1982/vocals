#!/bin/sh
set -e
pip install -r requirements.txt
python setup.py build_ext --inplace
pip install -e .
