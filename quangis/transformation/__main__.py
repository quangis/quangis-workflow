"""
Simple testing module.
"""

from sys import stdin

from quangis import error
from quangis.transformation.cct import cct

print("Reading from standard input...")
for line in stdin.readlines():
    line = line.strip()
    if line:
        try:
            expr = cct.parse(line)
            print("SUCCESS: ", expr)
        except error.AlgebraTypeError as e:
            print("FAILED: ", line)
            print(e)
