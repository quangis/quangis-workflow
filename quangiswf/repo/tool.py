from __future__ import annotations
from collections import defaultdict
from rdflib import Graph
from rdflib.term import URIRef, Node, BNode, Literal
from rdflib.compare import isomorphic
from typing import Iterable, Hashable, Mapping
from itertools import chain
from abc import abstractmethod

from quangiswf.repo.workflow import Workflow
from quangiswf.repo.tool2url import tool2url
from quangiswf.namespace import (
    n3, RDF, TOOLSCHEMA, WF, TOOL, SUPERTOOL, bind_all)

ALLOW_DISCONNECTED_SUPERTOOL = False

class DisconnectedArtefactsError(Exception):
    pass

class ToolAlreadyExistsError(Exception):
    pass

class ToolNotFoundError(Exception):
    pass


class Implementation(object):
    def __init__(self, name: str, uri: URIRef):
        self.name = name
        self.uri = uri

    @abstractmethod
    def graph(self) -> Graph:
        return NotImplemented


class Tool(Implementation):
    """A tool is a reference to an actual concrete tool, as implemented by, for 
    example, ArcGIS or QGIS."""

    def __init__(self, name: str, url: URIRef) -> None:
        self.url = url
        super().__init__(name, TOOL[name])

    def graph(self) -> Graph:
        g = Graph()
        g.add((self.uri, RDF.type, TOOLSCHEMA.Tool))
        g.add((self.uri, TOOLSCHEMA.url, self.url))
        return g


class Supertool(Implementation):
    """A supertool is a workflow *schema*."""

    def __init__(self, name: str,
            inputs: Mapping[str, Hashable],
            output: Hashable) -> None:

        self.map: dict[Hashable, BNode] = defaultdict(BNode)
        map = self.map

        self.inputs: dict[str, BNode] = {i: map[x] for i, x in inputs.items()}
        self.output: BNode = map[output]

        self.all_inputs: set[BNode] = set()
        self.all_outputs: set[BNode] = set()
        self.constituent_tools: set[URIRef] = set()

        self._graph = Graph()
        super().__init__(name, SUPERTOOL[name])

    @staticmethod
    def propose(wf: Workflow, action: Node) -> URIRef | Supertool:
        """Propose a tool or supertool that implements this action. This is an 
        expensive operation because, in the case of a supertool, a proposal 
        supertool is extracted."""
        name, impl = wf.impl(action)

        if (impl, RDF.type, WF.Workflow) in wf:
            assert isinstance(impl, BNode), "subworkflows should be blank"

            supertool = Supertool(name,
                inputs=wf.inputs_labelled(action),
                output=wf.output(action))

            for a in wf.low_level_actions(impl):
                _, tool = wf.impl(a)
                supertool.add_action(tool, wf.inputs(a), wf.output(a))

            supertool.sanity_check()
            return supertool

        else:
            assert isinstance(impl, URIRef), "tools should be URIRefs"
            assert name in tool2url, "unknown tool"
            return impl

    def add_action(self, tool: URIRef,
           inputs: Iterable[Hashable], output: Hashable) -> None:

        inputsm = [self.map[x] for x in inputs]
        outputm = self.map[output]
        self.all_inputs.update(inputsm)
        self.all_outputs.add(outputm)
        self.constituent_tools.add(tool)

        action = BNode()
        self._graph.add((self.uri, TOOLSCHEMA.action, action))
        self._graph.add((action, TOOLSCHEMA.apply, tool))
        self._graph.add((action, TOOLSCHEMA.output, outputm))
        for x in inputsm:
            self._graph.add((action, TOOLSCHEMA.input, x))

    def match(self, other: Supertool) -> bool:
        return (self.constituent_tools == other.constituent_tools
            and isomorphic(self._graph, other._graph))

    def sanity_check(self):
        """Sanity check."""
        in1 = self.all_inputs - self.all_outputs
        in2 = set(self.inputs.values())
        if not in1 == in2:
            raise DisconnectedArtefactsError(
                f"Expected {len(in2)} input(s) for {n3(self.uri)} but "
                f"found {len(in1)} inside.")

        out1 = self.all_outputs - self.all_inputs
        out2 = set((self.output,))
        if not out1 == out2:
            raise DisconnectedArtefactsError(
                f"Expected 1 output for {n3(self.uri)} but "
                f"found {len(out1)} inside.")

    def graph(self) -> Graph:
        g = Graph()
        g += self._graph
        g.add((self.uri, RDF.type, TOOLSCHEMA.Supertool))
        for i, x in self.inputs.items():
            g.add((x, TOOLSCHEMA.id, Literal(i)))
        return g


class ToolRepo(object):
    # TODO input/output permutations

    def __init__(self) -> None:
        self.tools: dict[URIRef, Tool] = dict()
        self.supertools: dict[URIRef, Supertool] = dict()

        for name, url in tool2url.items():
            tool = Tool(name, URIRef(url))
            self.tools[tool.uri] = tool

    def __contains__(self, tool: URIRef | Implementation) -> bool:
        if isinstance(tool, URIRef):
            return tool in self.tools or tool in self.supertools
        else:
            return tool.uri in self

    def find_tool(self, tool: Implementation) -> URIRef:
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
        elif isinstance(tool, Tool):
            return tool.uri
        else:
            assert isinstance(tool, URIRef) and tool in self.tools
            return tool

    def register_supertool(self, supertool: Supertool) -> Supertool:
        if not ALLOW_DISCONNECTED_SUPERTOOL:
            supertool.sanity_check()
        if (supertool.uri in self.supertools and not
                supertool.match(self.supertools[supertool.uri])):
            raise ToolAlreadyExistsError(
                f"The supertool {supertool.uri} already exists in the "
                f"repository and is different from the one that you "
                f"are attempting to register.")
        self.supertools[supertool.uri] = supertool
        return supertool

    def graph(self) -> Graph:
        g = Graph()
        bind_all(g, default=TOOLSCHEMA)
        for tool in chain(self.tools.values(), self.supertools.values()):
            g += tool.graph()
        return g
