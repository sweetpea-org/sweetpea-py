#!/usr/bin/env bash

# Make sure to change the version in setup.py before running this script,
# pypi.org releases cannot be overwritten once uploaded, nor restored
# once deleted.

set -x

echo "Removing prior distribution archives"
rm dist/*

echo "Building new distribution archives"
python3 setup.py sdist bdist_wheel

echo "Publishing new distribution to pypi.org"
twine upload dist/*
