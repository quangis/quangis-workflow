"""
Simple testing module.
"""

from sys import stdin

from quangis.transformation.algebra import algebra

print("Reading from standard input...")
for line in stdin.readlines():
    expr = algebra.parse(line)
    print(expr)
