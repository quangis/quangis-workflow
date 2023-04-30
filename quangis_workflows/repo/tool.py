from __future__ import annotations
import random
import string
from collections import defaultdict
from itertools import count
from rdflib.term import URIRef, Node, BNode
from rdflib.compare import isomorphic
from typing import Iterable
from transforge.list import GraphList

from quangis_workflows.repo.tool2url import tool2url
from quangis_workflows.namespace import n3, RDF, TOOL

class UnknownToolError(Exception):
    pass


class Supertool(GraphList):
    """A supertool is a workflow *schema*."""

    def __init__(self, uri: URIRef,
            inputs: Iterable[Node], outputs: Iterable[Node],
            actions: Iterable[tuple[URIRef, Iterable[Node], Iterable[Node]]]):

        super().__init__()

        code = ''.join(random.choice(string.ascii_lowercase) for i in range(4))
        counter = count()

        map: dict[Node, BNode] = defaultdict(
            lambda: BNode(f"{code}{next(counter)}"))

        self.uri = uri
        self.inputs = [map[x] for x in inputs]
        self.outputs = [map[x] for x in outputs]
        self.all_inputs: set[BNode] = set()
        self.all_outputs: set[BNode] = set()
        self.constituent_tools: set[URIRef] = set()

        self.add((uri, RDF.type, TOOL.Supertool))
        self.add((uri, TOOL.inputs, self.add_list(self.inputs)))
        self.add((uri, TOOL.outputs, self.add_list(self.outputs)))
        for tool, inputs, outputs in actions:
            self._add_action(tool,
                [map[x] for x in inputs],
                [map[x] for x in outputs])

    def _add_action(self, tool: URIRef,
           inputs: Iterable[BNode], outputs: Iterable[BNode]) -> None:
        inputs = inputs if isinstance(inputs, list) else list(inputs)
        outputs = outputs if isinstance(outputs, list) else list(outputs)
        self.all_inputs.update(inputs)
        self.all_outputs.update(outputs)

        action = BNode()
        self.constituent_tools.add(tool)
        self.add((self.uri, TOOL.action, action))
        self.add((action, TOOL.apply, tool))
        self.add((action, TOOL.inputs, self.add_list(inputs)))
        self.add((action, TOOL.outputs, self.add_list(outputs)))

    def match(self, other: Supertool) -> bool:
        return (self.constituent_tools == other.constituent_tools
            and isomorphic(self, other))

    def sanity_check(self):
        """Sanity check."""
        in1 = self.all_inputs - self.all_outputs
        in2 = set(self.inputs)
        out1 = self.all_outputs - self.all_inputs
        out2 = set(self.outputs)
        if not (in1 == in2 and out1 == out2):
            raise RuntimeError(f"In supertool {n3(self.uri)}, there are "
                f"loose inputs or outputs.")


class ToolRepo(object):
    # TODO input/output permutations

    tools = tool2url

    def __init__(self) -> None:
        self.supertools: dict[URIRef, Supertool] = dict()

    def find_tool(self, tool: URIRef | Supertool) -> URIRef:
        """Find a (super)tool in this tool repository that matches the given 
        tool, even if the name of the supertool is different. This is an 
        expensive operation because, in the case of a supertool, a proposal 
        supertool is extracted and checked for isomorphism with existing 
        supertools."""
        if isinstance(tool, Supertool):

            if (tool.uri in self.supertools):
                if tool.match(self.supertools[tool.uri]):
                    return tool.uri
                else:
                    raise UnknownToolError(f"{n3(tool.uri)} can be found, but "
                        f"doesn't match the given supertool of the same name.")

            for candidate in self.supertools.values():
                if tool.match(candidate):
                    return candidate.uri

            raise UnknownToolError(
                f"There is no supertool like {n3(tool.uri)} in the tool "
                f" repository.")
        else:
            return tool

    def register_supertool(self, supertool: Supertool) -> Supertool:
        supertool.sanity_check()
        if (supertool.uri in self.supertools and not
                supertool.match(self.supertools[supertool.uri])):
            raise RuntimeError
        self.supertools[supertool.uri] = supertool
        return supertool
