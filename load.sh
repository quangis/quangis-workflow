#!/bin/sh

python3 -m transformation_algebra vocab \
    -L cct/language.py \
    -b fuseki -s http://localhost:3030/cct

for F in workflows/*.ttl; do
    python -m transformation_algebra graph \
        -L cct/language.py \
        -T tools/tools.ttl \
        -b fuseki -s http://localhost:3030/cct \
        "$F"
done
