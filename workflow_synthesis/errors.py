"""
This module holds the errors that our program might raise.
"""


class WrongDimensionError(ValueError):
    def __init__(self, dimension, allowed_dimensions):
        self.message = "Dimension {} is not one of {}".format(
            dimension, allowed_dimensions)
