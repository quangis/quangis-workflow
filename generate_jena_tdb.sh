#!/bin/bash
# Once graphs and queries have been generated, Apache Jena TBD
# <https://jena.apache.org/documentation/tdb/> is a convenient way to locally
# test them without having to manipulate a SPARQL endpoint yet.
set -euo pipefail

# Get Apache Jena binaries if not present yet
if [ ! -e build/apache-jena-4.2.0/ ]; then
    mkdir -p build/
    cd build/
    wget https://dlcdn.apache.org/jena/binaries/apache-jena-4.2.0.zip
    unzip apache-jena-4.2.0.zip
    cd -
fi

# Build TDB & query
rm -rf build/jena-tdb/
mkdir -p build/jena-tdb/
build/apache-jena-4.2.0/bin/tdbloader2 --loc build/jena-tdb/ build/*.ttl
for query in build/*.rq; do
    echo $query
    build/apache-jena-4.2.0/bin/tdbquery --loc=build/jena-tdb/ --query=$query
    echo
done
