#!/bin/bash
# ref: https://github.com/nanasess/setup-chromedriver
PLATFORM=$1
CHROMEVERSION=$2

if [[ "${PLATFORM}" == macos* ]]; then ARCHITECTURE="mac64"; else ARCHITECTURE="linux64"; fi
wget -c -nc --retry-connrefused --tries=0 "https://chromedriver.storage.googleapis.com/${CHROMEVERSION}/chromedriver_${ARCHITECTURE}.zip"
unzip -o -q "chromedriver_${ARCHITECTURE}.zip"
sudo mv chromedriver /usr/local/bin/chromedriver
rm "chromedriver_${ARCHITECTURE}.zip"
