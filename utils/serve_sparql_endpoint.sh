#!/bin/bash
# Once graphs have been generated, we conveniently test them by populating an
# Apache Jena TDB from the graphs, and running a Fuseki SPARQL endpoint on that
# database.
#
# See:
# - <https://jena.apache.org/documentation/tdb/>
# - <https://jena.apache.org/documentation/fuseki2/>
# - <https://repo1.maven.org/maven2/org/apache/jena/jena-fuseki-server/$VER/jena-fuseki-server-$VER.jar>

set -euo pipefail
cd "$(dirname $(realpath $0))"/.. # cwd is project root directory
VER="4.3.2" # Apache Jena version

# Get Apache Jena & Fuseki binaries if not present yet
mkdir -p build/
cd build/
if [ ! -e apache-jena-$VER/ ]; then
    wget https://dlcdn.apache.org/jena/binaries/apache-jena-$VER.zip
    unzip apache-jena-$VER.zip
fi
if [ ! -e apache-jena-fuseki-$VER/ ]; then
    wget https://dlcdn.apache.org/jena/binaries/apache-jena-fuseki-$VER.zip
    unzip apache-jena-fuseki-$VER.zip
fi
cd -

# (Re-)build TDB if not yet present or if any graph has changed
if
    true
    # [ ! -e "build/tdb/" ] 
    # || [ ! -z "$(find build/ -maxdepth 1 -iname '*.ttl' -newer build/tdb/)" ]
then
    rm -rf build/tdb/
    mkdir -p build/tdb/
    build/apache-jena-$VER/bin/tdb1.xloader --loc build/tdb/ build/*.ttl
else
    echo "No change in graphs, not rebuilding TDB." >& 2
fi

# Run the Fuseki server with the TDB we just built
build/apache-jena-fuseki-$VER/fuseki-server \
    --timeout=10000 \
    --loc="$PWD/build/tdb" /name
