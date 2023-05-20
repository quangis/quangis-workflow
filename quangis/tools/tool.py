from __future__ import annotations
from rdflib import Graph
from rdflib.term import URIRef, Node, BNode, Literal
from rdflib.compare import isomorphic
from typing import Iterator, Iterable, Hashable, Mapping
from abc import abstractmethod
from transforge.namespace import shorten

from quangis.defaultdict import DefaultDict
from quangis.workflow import Workflow
from quangis.polytype import Polytype
from quangis.namespace import (
    n3, RDF, RDFS, TOOL, WF, MULTI, ABSTR, CCT)
from quangis.cctrans import cct
from quangis.ccdata import dimensions

class CCTError(Exception):
    pass

class UntypedArtefactError(Exception):
    pass

class DisconnectedArtefactsError(Exception):
    pass


class Artefact(object):
    def __init__(self, type: Polytype,
            id: str | None = None,
            comments: Iterable[str] = ()):
        self.type = type
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
    def from_graph(g: Graph, artefact: Node, with_type: bool = True,
            with_comments: bool = True) -> Artefact:
        if with_type:
            type = Polytype.assemble(dimensions, g.objects(artefact, RDF.type))
        else:
            type = Polytype(dimensions)

        id_node = g.value(artefact, TOOL.id, any=False)
        id = id_node.value if isinstance(id_node, Literal) else None

        comments: list[str] = []
        if with_comments:
            for comment in g.objects(artefact, RDFS.comment):
                assert isinstance(comment, Literal)
                comments.append(comment.value)

        return Artefact(type=type, id=id, comments=comments)


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
    def __init__(self, uri: URIRef, comments: list[str] = []):
        self.uri = uri
        self.name = shorten(uri)
        self.comments: list[str] = comments

    @abstractmethod
    def to_graph(self, g: Graph) -> Graph:
        return NotImplemented

    @staticmethod
    def comments_from_graph(uri: URIRef, g: Graph) -> Iterator[str]:
        for comment in g.objects(uri, RDFS.comment):
            assert isinstance(comment, Literal)
            yield comment.value

class Implementation(Tool):
    pass


class Unit(Implementation):
    """A basic concrete tool is a reference to a single implemented tool, as 
    implemented by, for example, ArcGIS or QGIS."""

    def __init__(self, uri: URIRef, url: URIRef, comments: list[str] = []) -> None:
        super().__init__(uri, comments)
        self.url = url

    @staticmethod
    def from_graph(graph: Graph) -> Iterator[Unit]:
        for tool in graph.subjects(RDF.type, TOOL.Unit):
            assert isinstance(tool, URIRef)
            url = graph.value(tool, RDFS.seeAlso, any=False)
            assert isinstance(url, URIRef)
            comments = list(Tool.comments_from_graph(tool, graph))
            yield Unit(tool, url, comments=comments)

    def to_graph(self, g: Graph) -> Graph:
        assert not (self.uri, RDF.type, TOOL.Unit) in g
        g.add((self.uri, RDF.type, TOOL.Unit))
        g.add((self.uri, RDFS.seeAlso, self.url))
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

        self.inputs: dict[str, Artefact] = dict()
        self.output: Artefact | None = None
        self.actions: list[Action] = []
        self.comments: list[str] = list(comments)

        self.all_inputs: set[Artefact] = set()
        self.all_outputs: set[Artefact] = set()
        self.all_tools: set[URIRef] = set()

        for action in actions:
            self._add_action(action)
        self._add_io(inputs, output)

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
        """Propose a composite tool that corresponds to the subworkflow 
        associated with the given action."""

        m: Mapping[Node, Artefact] = DefaultDict(
            lambda n: Artefact.from_graph(wf, n, with_type=False, 
                with_comments=False))
        subwf = wf.subworkflow(action)
        return Multi(
            uri=MULTI[wf.label(subwf)],
            inputs={k: m[v] for k, v in wf.inputs_labelled(action).items()},
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

            comments = []
            for comment in g.objects(uri, RDFS.comment):
                assert isinstance(comment, Literal)
                comments.append(comment.value)

            yield Multi(uri=uri,
                inputs=global_inputs,
                actions=actions,
                comments=comments)

    def _add_io(self, inputs: Mapping[str, Artefact],
            output: Artefact | None = None) -> None:
        # Sanity check: any artefact must be both the output and input of an 
        # action; or else, only one of these, in which case it must be 
        # accounted for as the input or output of the supertool.
        found_inputs = self.all_inputs - self.all_outputs
        real_inputs = set(inputs.values())

        if found_inputs != real_inputs:
            raise DisconnectedArtefactsError(
                f"Expected {len(real_inputs)} input(s) for {n3(self.uri)} but "
                f"found {len(found_inputs)} inside.")

        for label, input in inputs.items():
            self.inputs[label] = input

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
        """Create a new signature proposal from a tool application."""
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
        for i, x in enumerate(wf.inputs(action, labelled=True), start=1):
            t = inputs[str(i)] = Artefact.from_graph(wf, x)
            if t.type.empty():
                raise UntypedArtefactError(
                    f"The CCD type of the {i}'th input artefact of an "
                    f"action associated with {lbl} is empty or too general.")

        outputs = [Artefact.from_graph(wf, x) for x in wf.outputs(action)]
        assert len(outputs) == 1
        output = outputs[0]
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
            assert isinstance(cct_literal, Literal)

            implementations: set[URIRef] = set()
            for impl in graph.subjects(TOOL.implements, sig):
                assert isinstance(impl, URIRef)
                implementations.add(impl)

            inputs: dict[str, Artefact] = dict()
            for x in graph.objects(sig, TOOL.input):
                input = Artefact.from_graph(graph, x)
                assert input.id
                inputs[input.id] = input

            output_node = graph.value(sig, TOOL.output, any=False)
            assert output_node
            output = Artefact.from_graph(graph, output_node)

            comments = []
            for comment in graph.objects(sig, RDFS.comment):
                assert isinstance(comment, Literal)
                comments.append(comment.value)

            yield Abstraction(uri=sig,
                inputs=inputs,
                output=output,
                cct_expr=str(cct_literal),
                implementations=implementations,
                comments=comments
            )

    def to_graph(self, g: Graph) -> Graph:
        assert isinstance(self.uri, URIRef)
        assert not (self.uri, RDF.type, TOOL.Abstraction) in g

        g.add((self.uri, RDF.type, TOOL.Abstraction))
        g.add((self.uri, CCT.expression, Literal(self.cct_expr)))

        for impl in self.implementations:
            g.add((impl, TOOL.implements, self.uri))

        for _, x in self.inputs.items():
            g.add((self.uri, TOOL.input, x.to_graph(g)))

        for comment in self.comments:
            g.add((self.uri, RDFS.comment, Literal(comment)))

        g.add((self.uri, TOOL.output, self.output.to_graph(g)))

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
        il1 = list(self.inputs.keys())
        il2 = list(candidate.inputs.keys())
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
