#!/bin/bash

mkdir -p build/
for F in workflows/*.ttl; do
    N="$(basename -s .ttl "$F")"
    python3 -m transformation_algebra graph -L cct -T tools/tools.ttl \
        -o "build/$N.dot" -t dot "$F"
done
