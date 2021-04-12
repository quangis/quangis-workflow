Core concept transformation algebra
===============================================================================

This repository contains the implementation for the core concept 
transformation algebra of the [QuAnGIS](https://questionbasedanalysis.com/) 
project.

It is based on the 
[transformation-algebra](https://github.com/quangis/transformation_algebra) 
package developed for this project, which you will need to have installed:

    pip3 install 'transformation-algebra>=0.1.0'

Usage example:

    >>> from cct import *
    >>> pi1(objectregions)
    R1(Obj)
    >>> print(algebra.parse("pi1 (objectregions x)"))
    pi1 (objectregions x) : R1(Obj)


For tests, you will additionally need the [rdflib](https://rdflib.dev/) 
package and an appropriate `ToolDescription_TransformationAlgebra.ttl` [1] in 
this directory. To run the tests:

    python3 -m unittest test.py


### Notes

1. Internally available at `QuAnGIS/ownpapers/TheoryofGISFunctions/`.
