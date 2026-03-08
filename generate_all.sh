#! /bin/bash

# This script generates all the data files for the project. It should be run from the root directory of the project.

# Check if build_punk_records.py exists
if [ ! -f build_punk_records.py ]; then
    echo "Error: build_punk_records.py not found. Please run this script from the root directory of the project."
    exit 1
fi 

# Run the build script for each language
for lang in english french chinese-hongkong chinese-taiwan english-asia thai; do
    echo "Generating data for language: $lang"
    python build_punk_records.py --language $lang --out-dir . --split-per-card
done