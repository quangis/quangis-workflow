from __future__ import annotations
from rdflib import Graph
from rdflib.term import URIRef, Node, BNode, Literal
from rdflib.compare import isomorphic
from typing import Iterator, Iterable, Mapping, MutableMapping
from abc import abstractmethod
from transforge.namespace import shorten
from collections import defaultdict

from quangis.defaultdict import DefaultDict
from quangis.workflow import Workflow
from quangis.polytype import Polytype
from quangis.namespace import (
    n3, RDF, RDFS, TOOL, MULTI, ABSTR, CCT, DC)
from quangis.cct import cct
from quangis.ccd import ccd

class CCTError(Exception):
    pass

class UntypedArtefactError(Exception):
    pass

class DisconnectedArtefactsError(Exception):
    pass


def gettype(g: Graph, node: Node) -> Polytype:
    return Polytype(ccd.dimensions, g.objects(node, RDF.type))

def geturis(g: Graph, node: Node, pred: Node) -> Iterator[URIRef]:
    for uri in g.objects(node, pred):
        assert isinstance(uri, URIRef)
        yield uri

def getstrs(g: Graph, node: Node, pred: Node) -> Iterator[str]:
    for literal in g.objects(node, RDFS.comment):
        assert isinstance(literal, Literal) and isinstance(literal.value, str)
        yield literal.value

class Artefact(object):
    """An artefact is the input or output of a tool or an action. The schematic 
    input artefacts of a tool MUST be associated with an ID; all other 
    artefacts MUST NOT have IDs. The concrete artefacts of a workflow action 
    and the schematic artefact of a tool abstraction MUST have a type; all 
    other artefacts MAY have a type. These constraints aren't checked at the 
    moment."""

    def __init__(self, type: Polytype | None = None,
            id: str | None = None,
            comments: Iterable[str] = ()):
        self.type = type or Polytype(ccd.dimensions)
        self.id = id
        self.comments = list(comments)

    def to_graph(self, g: Graph, with_comments: bool = True) -> BNode:
        artefact = BNode()
        if self.id:
            g.add((artefact, TOOL.id, Literal(self.id)))
        for uri in self.type.uris():
            g.add((artefact, RDF.type, uri))
        if with_comments:
            for comment in self.comments:
                g.add((artefact, RDFS.comment, Literal(comment)))
        return artefact

    @staticmethod
    def from_graph(g: Graph, artefact: Node) -> Artefact:
        id_literal = (g.value(artefact, TOOL.id, any=False)
            or g.value(artefact, DC.identifier, any=False))
        if id_literal:
            assert isinstance(id_literal, Literal)
            id = id_literal.value
            assert isinstance(id, str)
        else:
            id = None
        return Artefact(type=gettype(g, artefact), id=id,
            comments=getstrs(g, artefact, RDFS.comment))


class Action(object):
    def __init__(self, tool: URIRef,
            inputs: Iterable[Artefact],
            output: Artefact,
            comments: Iterable[str] = ()):
        self.tool = tool
        self.inputs = set(inputs)
        self.output = output
        self.comments = list(comments)


class Tool(object):
    def __init__(self, uri: URIRef, comments: Iterable[str] = []):
        self.uri = uri
        self.name = shorten(uri)
        self.comments: list[str] = list(comments)

    @abstractmethod
    def to_graph(self, g: Graph) -> Graph:
        return NotImplemented


class Implementation(Tool):
    pass


class Unit(Implementation):
    """A basic concrete tool is a reference to a single implemented tool, as 
    implemented by, for example, ArcGIS or QGIS."""

    def __init__(self, uri: URIRef, url: Iterable[URIRef],
            comments: Iterable[str] = ()) -> None:
        super().__init__(uri, comments)
        self.url = list(url)

    @staticmethod
    def from_graph(graph: Graph) -> Iterator[Unit]:
        for tool in graph.subjects(RDF.type, TOOL.Unit):
            assert isinstance(tool, URIRef)

            urls = []
            for url in graph.objects(tool, RDFS.seeAlso):
                assert isinstance(url, URIRef)
                urls.append(url)

            yield Unit(tool, geturis(graph, tool, RDFS.seeAlso), 
                comments=getstrs(graph, tool, RDFS.comment))

    def to_graph(self, g: Graph) -> Graph:
        assert not (self.uri, RDF.type, TOOL.Unit) in g
        g.add((self.uri, RDF.type, TOOL.Unit))
        for url in self.url:
            g.add((self.uri, RDFS.seeAlso, url))
        for c in self.comments:
            g.add((self.uri, RDFS.comment, Literal(c)))
        return g


class Multi(Implementation):
    """A composite tool (also: supertool) is an *ensemble* of concrete tools; 
    in other words: a workflow schema."""

    def __init__(self, uri: URIRef, actions: Iterable[Action],
            inputs: Mapping[str, Artefact],
            output: Artefact | None = None,
            comments: Iterable[str] = ()) -> None:

        super().__init__(uri)

        self.actions: list[Action] = []
        self.comments: list[str] = list(comments)

        self.all_inputs: set[Artefact] = set()
        self.all_outputs: set[Artefact] = set()
        self.all_tools: set[URIRef] = set()

        for action in actions:
            self._add_action(action)

        self.inputs: dict[str, Artefact]
        self.output: Artefact
        self._set_inputs(inputs)
        self._set_output(output)

        self.min_graph = Graph()
        self.to_graph(self.min_graph, with_comments=False)

    def to_graph(self, g: Graph, with_comments: bool = True) -> Graph:
        assert not (self.uri, RDF.type, TOOL.Multi) in g
        g.add((self.uri, RDF.type, TOOL.Multi))

        m: Mapping[Artefact, BNode] = DefaultDict(
            lambda x: x.to_graph(g, with_comments=with_comments))
        for a in self.actions:
            action = BNode()
            g.add((self.uri, TOOL.action, action))
            g.add((action, TOOL.apply, a.tool))
            g.add((action, TOOL.output, m[a.output]))
            for input in a.inputs:
                g.add((action, TOOL.input, m[input]))
            if with_comments:
                for comment in a.comments:
                    g.add((action, RDFS.comment, Literal(comment)))

        if with_comments:
            for c in self.comments:
                g.add((self.uri, RDFS.comment, Literal(c)))
        return g

    @staticmethod
    def extract(wf: Workflow, action: Node) -> Multi:
        """Propose a multitool that corresponds to the subworkflow associated 
        with the given action."""

        m: MutableMapping[Node, Artefact] = defaultdict(Artefact)

        inputs = dict()
        for k, v in wf.inputs_labelled(action).items():
            inputs[k] = m[v] = Artefact(id=k)

        # Find the subworkflow node associated with this action.
        subwf = wf.subworkflow(action)
        return Multi(
            uri=MULTI[wf.label(subwf)],
            inputs=inputs,
            output=m[wf.output(action)],
            actions=(
                Action(wf.tool(a),
                    (m[x] for x in wf.inputs(a)),
                    m[wf.output(a)])
                for a in wf.low_level_actions(subwf)))

    @staticmethod
    def from_graph(g: Graph) -> Iterator[Multi]:
        for uri in g.subjects(RDF.type, TOOL.Multi):
            assert isinstance(uri, URIRef)

            m: Mapping[Node, Artefact] = DefaultDict(
                lambda node: Artefact.from_graph(g, node))

            global_inputs: dict[str, Artefact] = dict()
            actions: list[Action] = []
            for action_node in g.objects(uri, TOOL.action):
                tool = g.value(action_node, TOOL.apply, any=False)
                assert isinstance(tool, URIRef)

                out_node = g.value(action_node, TOOL.output, any=False)
                assert out_node is not None
                output = m[out_node]

                inputs: list[Artefact] = []
                for in_node in g.objects(action_node, TOOL.input):
                    input = m[in_node]
                    inputs.append(input)
                    if input.id:
                        assert global_inputs.get(input.id, input) == input
                        global_inputs[input.id] = input

                comments: list[str] = []
                for s in g.objects(action_node, RDFS.comment):
                    assert isinstance(s, Literal)
                    comments.append(s.value)

                actions.append(Action(tool, inputs, output, comments))

            yield Multi(uri=uri,
                inputs=global_inputs,
                actions=actions,
                comments=getstrs(g, uri, RDFS.comment))

    def _set_inputs(self, inputs: Mapping[str, Artefact]) -> None:
        # Sanity check: any artefact must be both the output and input of an 
        # action; or else, only one of these, in which case it must be 
        # accounted for as the input or output of the supertool.
        found_inputs = self.all_inputs - self.all_outputs
        real_inputs = set(inputs.values())

        if found_inputs != real_inputs:
            raise DisconnectedArtefactsError(
                f"Expected {len(real_inputs)} input(s) for {n3(self.uri)} but "
                f"found {len(found_inputs)} inside.")

        self.inputs = dict()
        for label, input in inputs.items():
            self.inputs[label] = input

    def _set_output(self, output: Artefact | None = None) -> None:
        found_outputs = list(self.all_outputs - self.all_inputs)

        if len(found_outputs) != 1:
            raise DisconnectedArtefactsError(
                f"Expected an output for {n3(self.uri)} but "
                f"found {len(found_outputs)} inside. This may be due to "
                f"a cycle in the workflow.")

        found_output = found_outputs[0]
        if output and not found_output == output:
            raise DisconnectedArtefactsError(
                f"The output for {n3(self.uri)} does not correspond to the "
                f"one found.")

        self.output = found_output

    def _add_action(self, action: Action) -> None:
        self.all_inputs.update(action.inputs)
        self.all_outputs.add(action.output)
        self.all_tools.add(action.tool)
        self.actions.append(action)

    def match(self, other: Multi) -> bool:
        return (self.all_tools == other.all_tools
            and isomorphic(self.min_graph, other.min_graph))


class Abstraction(Tool):
    """A tool abstraction holds the abstract "signature" of one or more tools, 
    or even of ensembles of tools (multitools). It must describe the format of 
    its input and output (ie the core concept datatypes) and it must describe 
    its purpose (in terms of a core concept transformation expression).

    A tool abstraction may be implemented by multiple (multi)tools, because, 
    for example, a tool could be implemented in both QGIS and ArcGIS. 
    Conversely, multiple abstractions may be implemented by the same 
    (multi)tool, if it can be used in multiple contexts --- in the same way 
    that a hammer can be used either to drive a nail into a plank of wood or to 
    break a piggy bank."""

    def __init__(self, uri: URIRef,
            inputs: dict[str, Artefact],
            output: Artefact,
            cct_expr: str,
            implementations: Iterable[URIRef] = (),
            comments: Iterable[str] = ()) -> None:
        super().__init__(uri)
        self.inputs: dict[str, Artefact] = inputs
        self.output: Artefact = output
        self.cct_expr: str = cct_expr
        self.comments: list[str] = list(comments)
        self.implementations: set[URIRef] = set(implementations)
        self.cct_p = cct.parse(cct_expr, defaults=True)

    @staticmethod
    def propose(wf: Workflow, action: Node) -> Abstraction:
        """Create a new abstraction proposal from a concrete tool 
        application."""
        impl = wf.impl(action)
        name = wf.label(impl)
        if isinstance(impl, URIRef):
            lbl = n3(impl)
        else:
            lbl = f"a subworkflow labelled '{name}'"

        cct_expr = wf.cct_expr(action)
        if not cct_expr:
            raise CCTError(
                f"Abstraction of {lbl} has no CCT expression")

        inputs = dict()
        for i, x in wf.inputs_labelled(action).items():
            t = inputs[i] = Artefact(id=i, type=gettype(wf, x))
            if t.type.empty():
                raise UntypedArtefactError(
                    f"The CCD type of the {i}'th input artefact of an "
                    f"action associated with {lbl} is empty or too general.")

        output_node = wf.output(action)
        output = Artefact(type=gettype(wf, output_node))
        if output.type.empty():
            raise UntypedArtefactError(
                f"The CCD type of the output artefact of an action "
                f"associated with {lbl} is empty or too general.")

        return Abstraction(ABSTR[name], inputs, output, cct_expr)

    @staticmethod
    def from_graph(graph: Graph) -> Iterator[Abstraction]:
        for sig in graph.subjects(RDF.type, TOOL.Abstraction):
            assert isinstance(sig, URIRef)

            cct_literal = graph.value(sig, CCT.expression, any=False)
            assert (isinstance(cct_literal, Literal)
                and isinstance(cct_literal.value, str))

            implementations: set[URIRef] = set(geturis(graph, sig, 
                TOOL.implementation))

            inputs: dict[str, Artefact] = dict()
            for x in graph.objects(sig, TOOL.input):
                input = Artefact.from_graph(graph, x)
                assert input.id, f"{n3(sig)} has no input id"
                inputs[input.id] = input

            output_node = graph.value(sig, TOOL.output, any=False)
            assert output_node
            output = Artefact.from_graph(graph, output_node)

            yield Abstraction(uri=sig,
                inputs=inputs,
                output=output,
                cct_expr=cct_literal.value,
                implementations=implementations,
                comments=getstrs(graph, sig, RDFS.comment)
            )

    def to_graph(self, g: Graph) -> Graph:
        assert isinstance(self.uri, URIRef)
        assert not (self.uri, RDF.type, TOOL.Abstraction) in g

        g.add((self.uri, RDF.type, TOOL.Abstraction))
        g.add((self.uri, CCT.expression, Literal(self.cct_expr)))

        for impl in self.implementations:
            g.add((self.uri, TOOL.implementation, impl))

        for _, x in self.inputs.items():
            g.add((self.uri, TOOL.input, x.to_graph(g)))

        g.add((self.uri, TOOL.output, self.output.to_graph(g)))

        for comment in self.comments:
            g.add((self.uri, RDFS.comment, Literal(comment)))

        return g

    def covers_implementation(self, candidate: Abstraction) -> bool:
        return (bool(candidate.implementations)
            and candidate.implementations.issubset(self.implementations))

    def matches_cct(self, candidate: Abstraction) -> bool:
        """Check that the expression of the candidate matches the expression 
        associated with this one. Note that a non-matching expression doesn't 
        mean that tools are actually semantically different, since there are 
        multiple ways to express the same idea (consider `compose f g x` vs 
        `f(g(x))`). Therefore, some manual intervention may be necessary."""
        return (self.cct_p and candidate.cct_p
            and self.cct_p.match(candidate.cct_p))

    def subsumes_input_datatype(self, candidate: Abstraction) -> bool:
        # For now, we do not take into account permutations. We probably 
        # should, since even in the one test that I did (wffood), we see that 
        # SelectLayerByLocationPointObjects has two variants with just the 
        # order of the inputs flipped.
        il1 = sorted(self.inputs.keys())
        il2 = sorted(candidate.inputs.keys())
        return (il1 == il2 and all(
            candidate.inputs[k1].type.subtype(self.inputs[k2].type)
            for k1, k2 in zip(il1, il2)))

    def subsumes_output_datatype(self, candidate: Abstraction) -> bool:
        return self.output.type.subtype(candidate.output.type)

    def subsumes_datatype(self, candidate: Abstraction) -> bool:
        """If the inputs in the candidate signature are subtypes of the ones in 
        this one (and the outputs are supertypes), then this signature *covers* 
        the other signature. If the reverse is true, then this signature is 
        narrower than what the candidate one requires, which suggests that it 
        should be generalized. If the candidate signature is neither covered by 
        this one nor generalizes it, then the two signatures are 
        independent."""
        return (self.subsumes_input_datatype(candidate) and 
            self.subsumes_output_datatype(candidate))
