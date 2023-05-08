from __future__ import annotations
from rdflib import Graph
from rdflib.term import Node, URIRef, BNode, Literal
from transforge.list import GraphList
from itertools import chain, count

from quangiswf.types import Polytype
from quangiswf.repo.workflow import Workflow
from quangiswf.namespace import (bind_all, n3, SIG, CCT, RDF,
    TOOLSCHEMA)
from cct import cct

cctlang = cct


class SignatureNotFoundError(Exception):
    pass


class Signature(object):
    """A tool signature is an abstract specification of a tool. It may 
    correspond to one or more concrete tools, or even ensembles of tools. It 
    must describe the format of its input and output (ie the core concept 
    datatypes) and it may describe its purpose (in terms of a core concept 
    transformation expression).

    A signature may be implemented by multiple (super)tools, because, for 
    example, a tool could be implemented in both QGIS and ArcGIS. Conversely, 
    multiple signatures may be implemented by the same (super)tool, if it can 
    be used in multiple contexts --- in the same way that a hammer can be used 
    either to drive a nail into a plank of wood or to break a piggy bank."""

    def __init__(self, name: str,
            inputs: list[Polytype],
            outputs: list[Polytype],
            cct: str | None) -> None:
        self.name = name
        self.uri: URIRef = SIG[name]
        self.inputs: list[Polytype] = inputs
        self.outputs: list[Polytype] = outputs
        self.cct: str | None = cct
        self.description: str | None = None
        self.implementations: set[URIRef] = set()
        self.cct_p = cctlang.parse(cct, defaults=True) if cct else None

    @staticmethod
    def propose(wf: Workflow, action: Node,
            cct_mandatory: bool = False) -> Signature:
        """Create a new signature proposal from a tool application."""
        name, impl = wf.impl(action)
        cct = wf.cct(action)
        if not cct and cct_mandatory:
            raise RuntimeError("Signature has no cct expression")

        # inputs = []
        # for a in wf.inputs(action, labelled=True):
        #     t = wf.type(a)
        #     if t.empty():

        inputs = [wf.type(a) for a in wf.inputs(action, labelled=True)]
        outputs = [wf.type(a) for a in wf.outputs(action)]

        for t in chain(inputs, outputs):
            if t.empty():
                raise RuntimeError(
                    f"The CCD type of an artefact associated with an "
                    f"an action labelled '{name}' is empty or too general.")

        return Signature(name=name, inputs=inputs, outputs=outputs, cct=cct)

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

    def subsumes_datatype(self, candidate: Signature) -> bool:
        """If the inputs in the candidate signature are subtypes of the ones in 
        this one (and the outputs are supertypes), then this signature *covers* 
        the other signature. If the reverse is true, then this signature is 
        narrower than what the candidate one requires, which suggests that it 
        should be generalized. If the candidate signature is neither covered by 
        this one nor generalizes it, then the two signatures are 
        independent."""

        # For now, we do not take into account permutations. We probably 
        # should, since even in the one test that I did (wffood), we see that 
        # SelectLayerByLocationPointObjects has two variants with just the 
        # order of the inputs flipped.
        il = len(self.inputs)
        ol = len(self.outputs)
        if il != ol:
            return False

        return (
            all(candidate.inputs[k1].subtype(self.inputs[k2])
                for k1, k2 in zip(range(il), range(il)))
            and all(self.outputs[k1].subtype(candidate.outputs[k2])
                for k1, k2 in zip(range(ol), range(ol)))
        )


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

        sigs: set[Node] = set(s.uri for s in self.signatures.values()
            if s.covers_implementation(proposal) if s.uri)
        raise SignatureNotFoundError(
            f"The repository contains no signature for an application of "
            f"{'/'.join(n3(impl) for impl in proposal.implementations)}. "
            f"The following signatures exist for other applications of this "
            f"tool: {n3(sigs)}")

    def register_signature(self, proposal: Signature) -> Signature:
        """Register the proposed signature under a unique name."""
        proposal.uri = self.unique_uri(proposal.name)
        self.signatures[proposal.uri] = proposal
        return proposal

    def graph(self) -> Graph:
        g = GraphList()
        bind_all(g, TOOLSCHEMA)

        for sig in self.signatures.values():
            assert isinstance(sig.uri, URIRef)

            g.add((sig.uri, RDF.type, TOOLSCHEMA.Signature))
            g.add((sig.uri, CCT.expression, Literal(sig.cct)))

            for impl in sig.implementations:
                g.add((sig.uri, TOOLSCHEMA.implementation, impl))

            for i, x in enumerate(sig.inputs, start=1):
                artefact = BNode()
                for uri in x.uris():
                    g.add((artefact, RDF.type, uri))
                g.add((artefact, TOOLSCHEMA.id, Literal(i)))
                g.add((sig.uri, TOOLSCHEMA.input, artefact))

            for x in sig.outputs:
                artefact = BNode()
                for uri in x.uris():
                    g.add((artefact, RDF.type, uri))
                g.add((sig.uri, TOOLSCHEMA.output, artefact))

        return g
