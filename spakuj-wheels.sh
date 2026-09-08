#!/bin/sh
# Napuni wheels/ svime sto requirements.txt trazi, za linux/amd64 i za Python
# koji je u python:3. Posle toga build radi bez PyPI-ja.
#   sh spakuj-wheels.sh
set -e
cd "$(dirname "$0")"

rm -rf wheels
mkdir -p wheels

docker run --rm --platform linux/amd64 \
    -v "$(pwd)/requirements.txt:/requirements.txt:ro" \
    -v "$(pwd)/wheels:/wheels" \
    --entrypoint sh python:3 -c \
    'pip download -q -r /requirements.txt -d /wheels && pip download -q setuptools wheel -d /wheels'

echo "wheels/: $(ls wheels | wc -l) fajlova, $(du -sh wheels | cut -f1)"
echo
echo "Provera da instalacija radi bez mreze:"
docker run --rm --network none --platform linux/amd64 \
    -v "$(pwd)/requirements.txt:/requirements.txt:ro" \
    -v "$(pwd)/wheels:/wheels:ro" \
    --entrypoint sh python:3 -c \
    'pip install -q --no-cache-dir --no-index --find-links /wheels -r /requirements.txt &&
     python -c "import flask, web3, pymongo, redis, MySQLdb; print(\"  offline install radi\")"'
