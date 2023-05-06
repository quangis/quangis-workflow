from __future__ import annotations
from collections import defaultdict
from itertools import count
from rdflib import Graph
from rdflib.term import URIRef, Node, BNode
from rdflib.compare import isomorphic
from typing import Iterable
from transforge.list import GraphList
from transforge.namespace import shorten

from quangiswf.repo.workflow import Workflow
from quangiswf.repo.tool2url import tool2url
from quangiswf.namespace import (
    n3, RDF, RDFS, TOOLSCHEMA, WF, SUPERTOOL, bind_all)

class ToolNotFoundError(Exception):
    pass


class Supertool(GraphList):
    """A supertool is a workflow *schema*."""

    def __init__(self, name: str,
            inputs: Iterable[Node],
            outputs: Iterable[Node],
            actions: Iterable[tuple[URIRef, Iterable[Node], Iterable[Node]]],
            origin: Node | None = None
            ) -> None:

        super().__init__()

        counter = count()
        map: dict[Node, BNode] = defaultdict(
            lambda: BNode(f"d{next(counter)}_{name}"))

        self.name = name
        self.origin = origin
        self.uri = uri = SUPERTOOL[name]
        self.inputs = [map[x] for x in inputs]
        self.outputs = [map[x] for x in outputs]
        self.all_inputs: set[BNode] = set()
        self.all_outputs: set[BNode] = set()
        self.constituent_tools: set[URIRef] = set()

        self.add((uri, RDF.type, TOOLSCHEMA.Supertool))
        self.add((uri, TOOLSCHEMA.inputs, self.add_list(self.inputs)))
        self.add((uri, TOOLSCHEMA.outputs, self.add_list(self.outputs)))
        for tool, inputs, outputs in actions:
            self._add_action(tool,
                [map[x] for x in inputs],
                [map[x] for x in outputs])

    @staticmethod
    def propose(wf: Workflow, action: Node) -> URIRef | Supertool:
        """Propose a tool or supertool that implements this action. This is an 
        expensive operation because, in the case of a supertool, a proposal 
        supertool is extracted."""
        name, impl = wf.impl(action)
        if (impl, RDF.type, WF.Workflow) in wf:
            supertool = Supertool(name,
                inputs=wf.inputs(action),
                outputs=wf.outputs(action),
                actions=((wf.tool(sub), wf.inputs(sub), wf.outputs(sub))
                    for sub in wf.low_level_actions(impl)),
                origin=action)
            return supertool
        else:
            return URIRef(tool2url[name])

    def _add_action(self, tool: URIRef,
           inputs: Iterable[BNode], outputs: Iterable[BNode]) -> None:
        inputs = inputs if isinstance(inputs, list) else list(inputs)
        outputs = outputs if isinstance(outputs, list) else list(outputs)
        self.all_inputs.update(inputs)
        self.all_outputs.update(outputs)

        action = BNode()
        self.constituent_tools.add(tool)
        self.add((self.uri, TOOLSCHEMA.action, action))
        self.add((action, TOOLSCHEMA.apply, tool))
        for x in inputs:
            self.add((action, TOOLSCHEMA.input, x))
        for x in outputs:
            self.add((action, TOOLSCHEMA.output, x))

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
            raise RuntimeError(f"In supertool '{self.name}', originally "
                f"in tool application {n3(self.origin)}, there are "
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
                    raise ToolNotFoundError(
                        f"{n3(tool.uri)} can be found, but it does not match"
                        f"the given supertool of the same name.")

            for candidate in self.supertools.values():
                if tool.match(candidate):
                    return candidate.uri

            raise ToolNotFoundError(
                f"There is no supertool like {n3(tool.uri)} in the tool "
                f"repository.")
        else:
            return tool

    def register_supertool(self, supertool: Supertool) -> Supertool:
        supertool.sanity_check()
        if (supertool.uri in self.supertools and not
                supertool.match(self.supertools[supertool.uri])):
            raise RuntimeError(
                f"The supertool {supertool.uri} already exists in the "
                f"repository and is different from the one that you "
                f"are attempting to register.")
        self.supertools[supertool.uri] = supertool
        return supertool

    def graph(self) -> Graph:
        g = Graph()
        bind_all(g, default=TOOLSCHEMA)
        for supertool in self.supertools.values():
            g += supertool
        return g
