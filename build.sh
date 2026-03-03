#!/bin/bash

# Vercel now installs dependencies automatically from requirements.txt into .vercel_python_packages
# using the 'uv' package manager. We just need to ensure our bash script uses that environment.

export PYTHONPATH=$PYTHONPATH:$(pwd)/.vercel_python_packages

python3 scraper.py
