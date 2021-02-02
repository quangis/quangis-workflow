"""
Simple testing module.
"""

from sys import stdin

from quangis import error
from quangis.transformation.cct import cct

print("Reading from standard input...")
count = 0
for line in stdin.readlines():
    line = line.strip()
    if line:
        try:
            expr = cct.parse(line)
        except error.AlgebraTypeError as e:
            count += 1
            print()
            print("FAILED: ", line)
            print(e)
print(count)
