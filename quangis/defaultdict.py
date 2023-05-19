from collections import UserDict
from typing import TypeVar, Callable

Key = TypeVar("Key")
Value = TypeVar("Value")

# Like a defaultdict, but instead of a function that takes no arguments, it 
# takes a single argument, namely, the key
class DefaultDict(UserDict[Key, Value]):
    def __init__(self, default: Callable[[Key], Value]):
        self.default = default
        super().__init__()

    def __getitem__(self, key: Key) -> Value:
        try:
            return super().__getitem__(key)
            # return self.data[key]
        except KeyError:
            value = self.default(key)
            self.__setitem__(key, value)
            return value
