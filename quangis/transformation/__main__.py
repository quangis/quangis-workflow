"""
Simple testing module.
"""

from sys import stdin

from quangis import error
from quangis.transformation.cct import CCT

algebra = CCT()
print("Reading from standard input...")
for line in stdin.readlines():
    line = line.strip()
    if line:
        try:
            expr = algebra.parse(line)
        except error.AlgebraTypeError as e:
            print("FAILED: ", line)
            print(e)
            exit(1)
        print(expr)
