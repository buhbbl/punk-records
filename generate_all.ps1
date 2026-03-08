# This script generates all the data files for the project. It should be run from the root directory of the project.

# Check if build_punk_records.py exists
if (-Not (Test-Path "build_punk_records.py" -PathType Leaf)) {
    Write-Host "Error: build_punk_records.py not found. Please run this script from the root directory of the project." -ForegroundColor Red
    exit 1
}

# Run the build script for each language
$languages = @("english", "french", "chinese-hongkong", "chinese-taiwan", "english-asia", "thai")

foreach ($lang in $languages) {
    Write-Host "Generating data for language: $lang"
    python build_punk_records.py --language $lang --out-dir . --split-per-card
}