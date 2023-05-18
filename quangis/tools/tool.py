from __future__ import annotations
from collections import defaultdict
from rdflib import Graph
from rdflib.term import URIRef, Node, BNode, Literal
from rdflib.compare import isomorphic
from typing import Iterator, Iterable, Hashable, Mapping
from abc import abstractmethod
from transforge.namespace import shorten

from quangis.workflow import Workflow, dimensions
from quangis.polytype import Polytype
from quangis.namespace import (
    n3, RDF, RDFS, VOCAB, WF, SUPER, ABSTR, CCT)
from quangis.cctrans import cct


class CCTError(Exception):
    pass

class UntypedArtefactError(Exception):
    pass


class DisconnectedArtefactsError(Exception):
    pass


class Tool(object):
    def __init__(self, uri: URIRef):
        self.uri = uri
        self.name = shorten(uri)

    @abstractmethod
    def to_graph(self, g: Graph) -> Graph:
        return NotImplemented


class ToolImplementation(Tool):
    pass


class ConcreteTool(ToolImplementation):
    """A basic concrete tool is a reference to a single implemented tool, as 
    implemented by, for example, ArcGIS or QGIS."""

    def __init__(self, uri: URIRef, url: URIRef) -> None:
        # name = name or shorten(uri)
        super().__init__(uri)
        self.url = url

    @staticmethod
    def from_graph(graph: Graph) -> Iterator[ConcreteTool]:
        for tool in graph.subjects(RDF.type, VOCAB.ConcreteTool):
            assert isinstance(tool, URIRef)
            url = graph.value(tool, RDFS.seeAlso, any=False)
            assert isinstance(url, URIRef)
            yield ConcreteTool(tool, url)

    def to_graph(self, g: Graph) -> Graph:
        assert not (self.uri, RDF.type, VOCAB.ConcreteTool) in g
        g.add((self.uri, RDF.type, VOCAB.ConcreteTool))
        g.add((self.uri, RDFS.seeAlso, self.url))
        return g


class SuperTool(ToolImplementation):
    """A supertool is an *ensemble* of concrete tools; in other words: a 
    workflow schema that acts as a compound tool."""

    def __init__(self, uri: URIRef) -> None:

        self.map: dict[Hashable, BNode] = defaultdict(BNode)

        self.inputs: dict[str, BNode] = dict()
        self.output: BNode | None = None

        self.all_inputs: set[BNode] = set()
        self.all_outputs: set[BNode] = set()
        self.constituent_tools: set[URIRef] = set()

        self._graph = Graph()
        super().__init__(uri)

    @staticmethod
    def extract(wf: Workflow, action: Node) -> SuperTool:
        """Propose a supertool that corresponds to the subworkflow associated 
        with the given action."""
        impl = wf.tool(action)
        label = wf.label(impl)

        if (impl, RDF.type, WF.Workflow) in wf:
            assert isinstance(impl, BNode), \
                "subworkflows should be blank nodes"

            supertool = SuperTool(SUPER[label])

            for a in wf.low_level_actions(impl):
                tool = wf.tool(a)
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
    def from_graph(g: Graph) -> Iterator[SuperTool]:
        for uri in g.subjects(RDF.type, VOCAB.SuperTool):
            assert isinstance(uri, URIRef)
            supertool = SuperTool(uri)
            global_inputs: dict[str, BNode] = dict()
            for action in g.objects(uri, VOCAB.action):
                tool = g.value(action, VOCAB.apply, any=False)
                assert isinstance(tool, URIRef)
                output = g.value(action, VOCAB.output, any=False)
                assert isinstance(output, BNode)

                inputs: list[BNode] = []
                for input in g.objects(action, VOCAB.input):
                    assert isinstance(input, BNode)
                    inputs.append(input)
                    id = g.value(input, VOCAB.id, any=False)
                    if id:
                        assert isinstance(id, Literal)
                        global_inputs[id.value] = input

                supertool.add_action(tool, inputs, output)
            supertool.add_io(global_inputs)

            yield supertool

    def to_graph(self, g: Graph) -> Graph:
        g += self._graph
        g.add((self.uri, RDF.type, VOCAB.SuperTool))
        for i, x in self.inputs.items():
            g.add((x, VOCAB.id, Literal(i)))
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
        self._graph.add((self.uri, VOCAB.action, action))
        self._graph.add((action, VOCAB.apply, tool))
        self._graph.add((action, VOCAB.output, outputm))
        for x in inputsm:
            self._graph.add((action, VOCAB.input, x))

    def match(self, other: SuperTool) -> bool:
        return (self.constituent_tools == other.constituent_tools
            and isomorphic(self._graph, other._graph))


class AbstractTool(Tool):
    """An abstract tool is a *signature* or *specification* of a tool. It may 
    correspond to one or more concrete tools, or even ensembles of tools. It 
    must describe the format of its input and output (ie the core concept 
    datatypes) and it must describe its purpose (in terms of a core concept 
    transformation expression).

    An abstract tool may be implemented by multiple (super)tools, because, for 
    example, a tool could be implemented in both QGIS and ArcGIS. Conversely, 
    multiple signatures may be implemented by the same (super)tool, if it can 
    be used in multiple contexts --- in the same way that a hammer can be used 
    either to drive a nail into a plank of wood or to break a piggy bank."""

    def __init__(self, uri: URIRef,
            inputs: dict[str, Polytype],
            output: Polytype,
            cct_expr: str,
            implementations: Iterable[URIRef] = ()) -> None:
        super().__init__(uri)
        self.inputs: dict[str, Polytype] = inputs
        self.output: Polytype = output
        self.cct_expr: str = cct_expr
        self.description: str | None = None
        self.implementations: set[URIRef] = set(implementations)
        self.cct_p = cct.parse(cct_expr, defaults=True)

    @staticmethod
    def propose(wf: Workflow, action: Node) -> AbstractTool:
        """Create a new signature proposal from a tool application."""
        impl = wf.tool(action)
        name = wf.label(impl)
        if isinstance(impl, URIRef):
            lbl = n3(impl)
        else:
            lbl = f"a subworkflow labelled '{name}'"

        cct_expr = wf.cct_expr(action)
        if not cct_expr:
            raise CCTError(
                f"AbstractTool of {lbl} has no CCT expression")

        inputs = dict()
        for i, x in enumerate(wf.inputs(action, labelled=True), start=1):
            t = inputs[str(i)] = wf.type(x)
            if t.empty():
                raise UntypedArtefactError(
                    f"The CCD type of the {i}'th input artefact of an "
                    f"action associated with {lbl} is empty or too general.")

        outputs = [wf.type(x) for x in wf.outputs(action)]
        assert len(outputs) == 1
        output = outputs[0]
        if output.empty():
            raise UntypedArtefactError(
                f"The CCD type of the output artefact of an action "
                f"associated with {lbl} is empty or too general.")

        return AbstractTool(ABSTR[name], inputs, output, cct_expr)

    @staticmethod
    def from_graph(graph: Graph) -> Iterator[AbstractTool]:
        for sig in graph.subjects(RDF.type, VOCAB.AbstractTool):
            assert isinstance(sig, URIRef)

            cct_literal = graph.value(sig, CCT.expression, any=False)
            assert isinstance(cct_literal, Literal)

            implementations: set[URIRef] = set()
            for impl in graph.objects(sig, VOCAB.implementation):
                assert isinstance(impl, URIRef)
                implementations.add(impl)

            inputs: dict[str, Polytype] = dict()
            for artefact in graph.objects(sig, VOCAB.input):
                t = Polytype.assemble(dimensions,
                    graph.objects(artefact, RDF.type))
                id_literal = graph.value(artefact, VOCAB.id, any=False)
                assert isinstance(id_literal, Literal)
                i = str(id_literal)
                assert i not in inputs
                inputs[i] = t

            output_artefact = graph.value(sig, VOCAB.output, any=False)
            output = Polytype.assemble(dimensions,
                graph.objects(output_artefact, RDF.type))

            yield AbstractTool(uri=sig,
                inputs=inputs,
                output=output,
                cct_expr=str(cct_literal),
                implementations=implementations
            )

    def to_graph(self, g: Graph) -> Graph:
        assert isinstance(self.uri, URIRef)
        assert not (self.uri, RDF.type, VOCAB.AbstractTool) in g

        g.add((self.uri, RDF.type, VOCAB.AbstractTool))
        g.add((self.uri, CCT.expression, Literal(self.cct_expr)))

        for impl in self.implementations:
            g.add((self.uri, VOCAB.implementation, impl))

        for i, x in self.inputs.items():
            artefact = BNode()
            for uri in x.uris():
                g.add((artefact, RDF.type, uri))
            g.add((artefact, VOCAB.id, Literal(i)))
            g.add((self.uri, VOCAB.input, artefact))

        artefact = BNode()
        for uri in self.output.uris():
            g.add((artefact, RDF.type, uri))
        g.add((self.uri, VOCAB.output, artefact))

        return g

    def covers_implementation(self, candidate: AbstractTool) -> bool:
        return (bool(candidate.implementations)
            and candidate.implementations.issubset(self.implementations))

    def matches_cct(self, candidate: AbstractTool) -> bool:
        """Check that the expression of the candidate matches the expression 
        associated with this one. Note that a non-matching expression doesn't 
        mean that tools are actually semantically different, since there are 
        multiple ways to express the same idea (consider `compose f g x` vs 
        `f(g(x))`). Therefore, some manual intervention may be necessary."""
        return (self.cct_p and candidate.cct_p
            and self.cct_p.match(candidate.cct_p))

    def subsumes_input_datatype(self, candidate: AbstractTool) -> bool:
        # For now, we do not take into account permutations. We probably 
        # should, since even in the one test that I did (wffood), we see that 
        # SelectLayerByLocationPointObjects has two variants with just the 
        # order of the inputs flipped.
        il1 = list(self.inputs.keys())
        il2 = list(candidate.inputs.keys())
        return (il1 == il2 and all(
            candidate.inputs[k1].subtype(self.inputs[k2])
            for k1, k2 in zip(il1, il2)))

    def subsumes_output_datatype(self, candidate: AbstractTool) -> bool:
        return self.output.subtype(candidate.output)

    def subsumes_datatype(self, candidate: AbstractTool) -> bool:
        """If the inputs in the candidate signature are subtypes of the ones in 
        this one (and the outputs are supertypes), then this signature *covers* 
        the other signature. If the reverse is true, then this signature is 
        narrower than what the candidate one requires, which suggests that it 
        should be generalized. If the candidate signature is neither covered by 
        this one nor generalizes it, then the two signatures are 
        independent."""
        return (self.subsumes_input_datatype(candidate) and 
            self.subsumes_output_datatype(candidate))