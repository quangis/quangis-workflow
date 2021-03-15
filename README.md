Core concept transformation algebra
===============================================================================

This repository contains the implementation for the core concept 
transformation algebra of the [QuAnGIS](https://questionbasedanalysis.com/) 
project.

It is based on the 
[transformation-algebra](https://github.com/quangis/transformation_algebra) 
package developed for this project, which you will need to have installed:

    pip3 install transformation-algebra

Usage example:

    >>> from cct import *
    >>> pi1(objectregions)
    R1(Obj)
    >>> print(algebra.parse("pi1 (objectregions x)"))
    pi1 (objectregions x) : R1(Obj)

To run tests:

    python3 -m unittest tests.py
