from __future__ import annotations
from rdflib import Graph
from rdflib.term import Node, URIRef, BNode, Literal
from itertools import chain, count
from typing import Iterable, Iterator
from transforge.namespace import shorten

from quangiswf.types import Polytype
from quangiswf.repo.workflow import Workflow, dimensions
from quangiswf.namespace import (bind_all, n3, SIG, CCT, RDF,
    TOOLSCHEMA)
from cct import cct


class CCTError(Exception):
    pass

class UntypedArtefactError(Exception):
    pass

class SignatureNotFoundError(Exception):
    pass


class Signature(object):
    """A tool signature is an abstract specification of a tool. It may 
    correspond to one or more concrete tools, or even ensembles of tools. It 
    must describe the format of its input and output (ie the core concept 
    datatypes) and it must describe its purpose (in terms of a core concept 
    transformation expression).

    A signature may be implemented by multiple (super)tools, because, for 
    example, a tool could be implemented in both QGIS and ArcGIS. Conversely, 
    multiple signatures may be implemented by the same (super)tool, if it can 
    be used in multiple contexts --- in the same way that a hammer can be used 
    either to drive a nail into a plank of wood or to break a piggy bank."""

    def __init__(self, name: str,
            inputs: dict[str, Polytype],
            output: Polytype,
            cct_expr: str,
            implementations: Iterable[URIRef] = (),
            uri: URIRef | None = None) -> None:
        self.name = name
        self.uri: URIRef = uri or SIG[name]
        self.inputs: dict[str, Polytype] = inputs
        self.output: Polytype = output
        self.cct_expr: str = cct_expr
        self.description: str | None = None
        self.implementations: set[URIRef] = set(implementations)
        self.cct_p = cct.parse(cct_expr, defaults=True)

    @staticmethod
    def propose(wf: Workflow, action: Node) -> Signature:
        """Create a new signature proposal from a tool application."""
        name, impl = wf.impl(action)
        if isinstance(impl, URIRef):
            lbl = n3(impl)
        else:
            lbl = f"a subworkflow labelled '{name}'"

        cct_expr = wf.cct_expr(action)
        if not cct_expr:
            raise CCTError(
                f"Signature of {lbl} has no CCT expression")

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

        return Signature(name, inputs, output, cct_expr)

    @staticmethod
    def from_graph(graph: Graph) -> Iterator[Signature]:
        for sig in graph.subjects(RDF.type, TOOLSCHEMA.Signature):
            assert isinstance(sig, URIRef)

            cct_literal = graph.value(sig, CCT.expression, any=False)
            assert isinstance(cct_literal, Literal)

            implementations: set[URIRef] = set()
            for impl in graph.objects(sig, TOOLSCHEMA.implementation):
                assert isinstance(impl, URIRef)
                implementations.add(impl)

            inputs: dict[str, Polytype] = dict()
            for artefact in graph.objects(sig, TOOLSCHEMA.input):
                t = Polytype.assemble(dimensions,
                    graph.objects(artefact, RDF.type))
                id_literal = graph.value(artefact, TOOLSCHEMA.id, any=False)
                assert isinstance(id_literal, Literal)
                i = str(id_literal)
                assert i not in inputs
                inputs[i] = t

            output_artefact = graph.value(sig, TOOLSCHEMA.output, any=False)
            output = Polytype.assemble(dimensions,
                graph.objects(output_artefact, RDF.type))

            yield Signature(
                inputs=inputs,
                output=output,
                cct_expr=str(cct_literal),
                implementations=implementations,
                uri=sig,
                name=shorten(sig)
            )

    def graph(self) -> Graph:
        assert isinstance(self.uri, URIRef)
        g = Graph()

        g.add((self.uri, RDF.type, TOOLSCHEMA.Signature))
        g.add((self.uri, CCT.expression, Literal(self.cct_expr)))

        for impl in self.implementations:
            g.add((self.uri, TOOLSCHEMA.implementation, impl))

        for i, x in self.inputs.items():
            artefact = BNode()
            for uri in x.uris():
                g.add((artefact, RDF.type, uri))
            g.add((artefact, TOOLSCHEMA.id, Literal(i)))
            g.add((self.uri, TOOLSCHEMA.input, artefact))

        artefact = BNode()
        for uri in self.output.uris():
            g.add((artefact, RDF.type, uri))
        g.add((self.uri, TOOLSCHEMA.output, artefact))

        return g

    def covers_implementation(self, candidate: Signature) -> bool:
        return (bool(candidate.implementations)
            and candidate.implementations.issubset(self.implementations))

    def matches_cct(self, candidate: Signature) -> bool:
        """Check that the expression of the candidate matches the expression 
        associated with this one. Note that a non-matching expression doesn't 
        mean that tools are actually semantically different, since there are 
        multiple ways to express the same idea (consider `compose f g x` vs 
        `f(g(x))`). Therefore, some manual intervention may be necessary."""
        return (self.cct_p and candidate.cct_p
            and self.cct_p.match(candidate.cct_p))

    def subsumes_input_datatype(self, candidate: Signature) -> bool:
        # For now, we do not take into account permutations. We probably 
        # should, since even in the one test that I did (wffood), we see that 
        # SelectLayerByLocationPointObjects has two variants with just the 
        # order of the inputs flipped.
        il1 = list(self.inputs.keys())
        il2 = list(candidate.inputs.keys())
        return (il1 == il2 and all(
            candidate.inputs[k1].subtype(self.inputs[k2])
            for k1, k2 in zip(il1, il2)))

    def subsumes_output_datatype(self, candidate: Signature) -> bool:
        return self.output.subtype(candidate.output)

    def subsumes_datatype(self, candidate: Signature) -> bool:
        """If the inputs in the candidate signature are subtypes of the ones in 
        this one (and the outputs are supertypes), then this signature *covers* 
        the other signature. If the reverse is true, then this signature is 
        narrower than what the candidate one requires, which suggests that it 
        should be generalized. If the candidate signature is neither covered by 
        this one nor generalizes it, then the two signatures are 
        independent."""
        return (self.subsumes_input_datatype(candidate) and 
            self.subsumes_output_datatype(candidate))


class SignatureRepo(object):
    """
    A signature repository contains abstract versions of tools.
    """

    def __init__(self, *nargs, **kwargs) -> None:
        self.signatures: dict[URIRef, Signature] = dict()
        super().__init__(*nargs, **kwargs)

    def unique_uri(self, base: str) -> URIRef:
        """Generate a unique URI for a signature based on a name."""
        for i in chain([""], count(start=2)):
            uri = SIG[f"{base}{i}"]
            if uri not in self.signatures:
                return uri
        raise RuntimeError("Unreachable")

    def find_signature(self, proposal: Signature) -> Signature:
        """Find a signature that matches the proposed signature."""
        for sig in self.signatures.values():
            if (sig.covers_implementation(proposal)
                    and sig.subsumes_datatype(proposal)
                    and sig.matches_cct(proposal)):
                return sig

        # If we reach here, there was no signature found. Instead, we construct 
        # the error message
        sigs: set[Signature] = set(s for s in self.signatures.values()
            if s.covers_implementation(proposal))

        reasons = []
        if sigs:
            reasons.append("Some signatures implement this tool, but:")
            for sig in sigs:
                if not sig.subsumes_input_datatype(proposal):
                    reasons.append(
                        f"{n3(sig.uri)} input signature doesn't match."
                    )
                elif not sig.subsumes_output_datatype(proposal):
                    reasons.append(
                        f"{n3(sig.uri)} output signature doesn't match."
                    )
                elif not sig.matches_cct(proposal):
                    reasons.append(
                        f"{n3(sig.uri)} CCT expression doesn't match."
                    )
                else:
                    reasons.append(
                        f"{n3(sig.uri)} doesn't work for an unknown reason.")
        else:
            reasons.append("There are no signatures that implement this tool.")

        raise SignatureNotFoundError(
            f"The repository contains no signature for an application of "
            f"{'/'.join(n3(impl) for impl in proposal.implementations)}. "
            "\n\t".join(reasons))

    def register_signature(self, proposal: Signature) -> Signature:
        """Register the proposed signature under a unique name."""
        proposal.uri = self.unique_uri(proposal.name)
        self.signatures[proposal.uri] = proposal
        return proposal

    def graph(self) -> Graph:
        g = Graph()
        bind_all(g, TOOLSCHEMA)
        for sig in self.signatures.values():
            g += sig.graph()
        return g
