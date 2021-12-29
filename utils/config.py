#!/usr/bin/env python3
"""
What does this module do?
"""

import sys
from pathlib import Path
from rdflib import Namespace

root_path = Path(__file__).parent.parent
build_path = root_path / 'build'
query_path = root_path / 'queries'

GIS = Namespace('http://geographicknowledge.de/vocab/GISConcepts.rdf#')
WF = Namespace('http://geographicknowledge.de/vocab/Workflow.rdf#')
TOOLS = Namespace('http://geographicknowledge.de/vocab/GISTools.rdf#')

# Make sure the modules in the project root will be found
sys.path.append(str(root_path))

# Make sure the build path exists
build_path.mkdir(parents=True, exist_ok=True)
