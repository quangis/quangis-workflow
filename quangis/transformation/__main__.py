"""
Simple testing module.
"""

from sys import stdin

from quangis.transformation.algebra import CCT

algebra = CCT()
print("Reading from standard input...")
for line in stdin.readlines():
    line = line.strip()
    if line:
        try:
            expr = algebra.parse(line)
            print(expr)
        except Exception as e:
            print("FAILED PARSE FOR:", line)
            print(e)
            exit(0)
