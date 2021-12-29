#!/usr/bin/env python3
"""
What does this module do?
"""

import sys
from pathlib import Path

root_path = Path(__file__).parent.parent
build_path = root_path / 'build'
query_path = root_path / 'queries'

# Make sure the modules in the project root will be found
sys.path.append(str(root_path))

# Make sure the build path exists
build_path.mkdir(parents=True, exist_ok=True)
