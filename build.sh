#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python version specified in environment
PYTHON_VERSION=${PYTHON_VERSION:-3.9.0}
python -m pip install --upgrade pip
pip install -r requirements.txt
