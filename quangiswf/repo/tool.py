from __future__ import annotations
from collections import defaultdict
from rdflib import Graph
from rdflib.term import URIRef, Node, BNode, Literal
from rdflib.compare import isomorphic
from typing import Iterator, Iterable, Hashable, Mapping
from itertools import chain
from abc import abstractmethod

from transforge.namespace import shorten
from quangiswf.repo.workflow import Workflow
from quangiswf.namespace import (
    n3, RDF, RDFS, TOOLSCHEMA, WF, SUPERTOOL, bind_all)

class DisconnectedArtefactsError(Exception):
    pass

class ToolAlreadyExistsError(Exception):
    pass

class ToolNotFoundError(KeyError):
    pass


class Implementation(object):
    def __init__(self, name: str, uri: URIRef):
        self.name = name
        self.uri = uri

    @abstractmethod
    def to_graph(self, g: Graph) -> Graph:
        return NotImplemented


class Tool(Implementation):
    """A tool is a reference to an actual concrete tool, as implemented by, for 
    example, ArcGIS or QGIS."""

    def __init__(self, uri: URIRef, url: URIRef,
            name: str | None = None) -> None:
        name = name or shorten(uri)
        super().__init__(name, uri)
        self.url = url

    @staticmethod
    def from_graph(graph: Graph) -> Iterator[Tool]:
        for tool in graph.subjects(RDF.type, TOOLSCHEMA.Tool):
            assert isinstance(tool, URIRef)
            url = graph.value(tool, RDFS.seeAlso, any=False)
            assert isinstance(url, URIRef)
            yield Tool(tool, url)

    def to_graph(self, g: Graph) -> Graph:
        assert not (self.uri, RDF.type, TOOLSCHEMA.Tool) in g
        g.add((self.uri, RDF.type, TOOLSCHEMA.Tool))
        g.add((self.uri, RDFS.seeAlso, self.url))
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
    def extract(wf: Workflow, action: Node) -> Supertool:
        """Propose a supertool that corresponds to the subworkflow associated 
        with the given action."""
        label, impl = wf.impl(action)

        if (impl, RDF.type, WF.Workflow) in wf:
            assert isinstance(impl, BNode), "subworkflows should be blank"

            supertool = Supertool(label,
                inputs=wf.inputs_labelled(action),
                output=wf.output(action))

            for a in wf.low_level_actions(impl):
                _, tool = wf.impl(a)
                assert isinstance(tool, URIRef)
                supertool.add_action(tool, wf.inputs(a), wf.output(a))

            supertool.check_artefacts()
            return supertool
        else:
            raise RuntimeError(
                f"Cannot propose a supertool for {impl}, labelled '{label}', "
                f"because it is not a subworkflow")

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

    def check_artefacts(self):
        """Sanity check: any artefact must be both the output and input of an 
        action; or else, only one of these, in which case it must be accounted 
        for as the input or output of the supertool."""
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
                f"found {len(out1)} inside. This may be due to "
                f"a cycle in the workflow.")

    def to_graph(self, g: Graph) -> Graph:
        g += self._graph
        g.add((self.uri, RDF.type, TOOLSCHEMA.Supertool))
        for i, x in self.inputs.items():
            g.add((x, TOOLSCHEMA.id, Literal(i)))
        return g


class ToolRepo(object):
    def __init__(self) -> None:
        self.tools: dict[URIRef, Tool] = dict()
        self.supertools: dict[URIRef, Supertool] = dict()

    def __getitem__(self, key: URIRef) -> Implementation:
        return self.tools.get(key) or self.supertools[key]

    def __contains__(self, tool: URIRef | Implementation) -> bool:
        if isinstance(tool, URIRef):
            return tool in self.tools or tool in self.supertools
        else:
            return tool.uri in self

    def find_supertool(self, supertool: Supertool) -> Supertool:
        """Find a (super)tool in this tool repository that matches the given 
        one. This is an expensive operation because we have to check for 
        isomorphism with existing supertools."""
        if supertool.uri in self.supertools:
            if supertool.match(self.supertools[supertool.uri]):
                return supertool
            else:
                raise ToolNotFoundError(
                    f"{n3(supertool.uri)} can be found, but it does not match"
                    f"the given supertool of the same name.")

        for candidate in self.supertools.values():
            if supertool.match(candidate):
                return candidate

        raise ToolNotFoundError(
            f"There is no supertool like {n3(supertool.uri)} in the tool "
            f"repository.")

    def register_supertool(self, supertool: Supertool) -> None:
        if supertool.uri in self.supertools:
            raise ToolAlreadyExistsError(
                f"The supertool {supertool.uri} already exists in the "
                f"repository.")
        self.supertools[supertool.uri] = supertool

    def check_composition(self):
        """Check that all tools in every supertool are concrete tools."""
        for supertool in self.supertools:
            if not all(tool in self.tools for tool in 
                    supertool.constituent_tools):
                raise RuntimeError(
                    "All tools in a supertool must be concrete tools")

    def graph(self) -> Graph:
        g = Graph()
        bind_all(g, default=TOOLSCHEMA)
        for tool in chain(self.tools.values(), self.supertools.values()):
            tool.to_graph(g)
        return g
