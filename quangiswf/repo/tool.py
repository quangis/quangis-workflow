from __future__ import annotations
from collections import defaultdict
from rdflib import Graph
from rdflib.term import URIRef, Node, BNode, Literal
from rdflib.compare import isomorphic
from typing import Iterator, Iterable, Hashable, Mapping
from abc import abstractmethod

from transforge.namespace import shorten
from quangiswf.repo.workflow import Workflow
from quangiswf.namespace import (
    n3, RDF, RDFS, TOOLSCHEMA, WF, SUPERTOOL)

class DisconnectedArtefactsError(Exception):
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

    def __init__(self, name: str) -> None:

        self.map: dict[Hashable, BNode] = defaultdict(BNode)

        self.inputs: dict[str, BNode] = dict()
        self.output: BNode | None = None

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
            assert isinstance(impl, BNode), \
                "subworkflows should be blank nodes"

            supertool = Supertool(label)

            for a in wf.low_level_actions(impl):
                _, tool = wf.impl(a)
                assert isinstance(tool, URIRef)
                supertool.add_action(tool, wf.inputs(a), wf.output(a))

            supertool.add_io(inputs=wf.inputs_labelled(action),
                output=wf.output(action))

            return supertool
        else:
            raise RuntimeError(
                f"Cannot propose a supertool for {impl}, labelled '{label}', "
                f"because it is not a subworkflow")

    @staticmethod
    def from_graph(g: Graph) -> Iterator[Supertool]:
        for uri in g.subjects(RDF.type, TOOLSCHEMA.Supertool):
            assert isinstance(uri, URIRef)
            supertool = Supertool(uri)
            global_inputs: dict[str, BNode] = dict()
            for action in g.objects(uri, TOOLSCHEMA.action):
                tool = g.value(uri, TOOLSCHEMA.apply, any=False)
                assert isinstance(tool, URIRef)
                output = g.value(uri, TOOLSCHEMA.output, any=False)
                assert isinstance(output, BNode)

                inputs: list[BNode] = []
                for input in g.objects(action, TOOLSCHEMA.input):
                    assert isinstance(input, BNode)
                    inputs.append(input)
                    id = g.value(input, TOOLSCHEMA.id, any=False)
                    if id:
                        assert isinstance(id, Literal)
                        global_inputs[id.value] = input

                supertool.add_action(tool, inputs, output)
            supertool.add_io(global_inputs)

            yield supertool

    def to_graph(self, g: Graph) -> Graph:
        g += self._graph
        g.add((self.uri, RDF.type, TOOLSCHEMA.Supertool))
        for i, x in self.inputs.items():
            g.add((x, TOOLSCHEMA.id, Literal(i)))
        return g

    def add_io(self, inputs: Mapping[str, Hashable],
            output: Hashable | None = None) -> None:
        # Sanity check: any artefact must be both the output and input of an 
        # action; or else, only one of these, in which case it must be 
        # accounted for as the input or output of the supertool.
        found_inputs = self.all_inputs - self.all_outputs
        real_inputs = set(self.map[x] for x in inputs.values())

        if found_inputs != real_inputs:
            raise DisconnectedArtefactsError(
                f"Expected {len(real_inputs)} input(s) for {n3(self.uri)} but "
                f"found {len(found_inputs)} inside.")

        for label, input in inputs.items():
            self.inputs[label] = self.map[input]

        found_outputs = list(self.all_outputs - self.all_inputs)
        assert len(found_outputs) == 1

        if len(found_outputs) != 1:
            raise DisconnectedArtefactsError(
                f"Expected an output for {n3(self.uri)} but "
                f"found {len(found_outputs)} inside. This may be due to "
                f"a cycle in the workflow.")

        found_output = found_outputs[0]
        if output and not found_output == self.map[output]:
            raise DisconnectedArtefactsError(
                f"The output for {n3(self.uri)} does not correspond to the "
                f"one found.")

        self.output = found_output

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
