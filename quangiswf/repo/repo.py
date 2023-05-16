
from __future__ import annotations
import sys
from rdflib.term import Node, URIRef, BNode
from rdflib import Graph
from rdflib.compare import isomorphic
from typing import Iterator
from transforge.list import GraphList
from itertools import count, repeat, chain
from pathlib import Path
from collections import defaultdict

from quangiswf.namespace import (bind_all, VOCAB, RDF, WF, CCT_, n3, ABSTR)
from quangiswf.repo.workflow import (Workflow)
from quangiswf.repo.tool import (Tool, ConcreteTool, SuperTool, AbstractTool)


class ToolAlreadyExistsError(Exception):
    pass

class ToolNotFoundError(KeyError):
    pass

class Repo(object):
    """A repository contains signatures and tools."""

    def __init__(self) -> None:
        self.abstract_tools: dict[URIRef, AbstractTool] = dict()
        self.concrete_tools: dict[URIRef, ConcreteTool] = dict()
        self.supertools: dict[URIRef, SuperTool] = dict()
        super().__init__()

    @staticmethod
    def from_file(file: Path, check_integrity: bool = True) -> Repo:
        g = Graph()
        g.parse(file)

        repo = Repo()
        for tool in ConcreteTool.from_graph(g):
            repo.add(tool)
        for sig in AbstractTool.from_graph(g):
            repo.add(sig)
        for supertool in SuperTool.from_graph(g):
            repo.add(supertool)

        if check_integrity:
            print(f"Checking integrity of {file}...", file=sys.stderr)
            if not isomorphic(g, repo.graph()):
                raise RuntimeError(
                    f"Integrity check failed for {file}. It may contain "
                    f"tuples that aren't interpreted by this program, "
                    f"which will be lost if you proceed.")
            else:
                print(f"File {file} passed check", file=sys.stderr)
        return repo

    def __getitem__(self, key: URIRef) -> Tool:
        return (self.concrete_tools.get(key)
            or self.abstract_tools.get(key)
            or self.supertools[key])

    def __contains__(self, tool: URIRef | Tool) -> bool:
        if isinstance(tool, URIRef):
            return (tool in self.abstract_tools
                or tool in self.concrete_tools
                or tool in self.supertools)
        else:
            return tool.uri in self

    def add(self, item: Tool) -> None:
        if isinstance(item, ConcreteTool):
            assert item.uri not in self.concrete_tools
            self.concrete_tools[item.uri] = item
        elif isinstance(item, SuperTool):
            assert item.uri not in self.supertools
            self.supertools[item.uri] = item
        else:
            assert isinstance(item, AbstractTool)
            assert item.uri not in self.abstract_tools
            self.abstract_tools[item.uri] = item

    def signed_actions(self, wf: Workflow, root: Node) \
            -> Iterator[tuple[Node, URIRef | SuperTool, AbstractTool]]:
        assert (root, RDF.type, WF.Workflow) in wf

        for action in wf.high_level_actions(root):
            _, impl = wf.impl(action)
            try:
                proposal_sig = AbstractTool.propose(wf, action)
                if impl in self.concrete_tools:
                    assert isinstance(impl, URIRef)
                    tool = impl
                else:
                    tool = self.find_supertool(
                        SuperTool.extract(wf, action)).uri
                proposal_sig.implementations.add(tool)
                sig = self.find_signature(proposal_sig)
            except ToolNotFoundError:
                if impl and (impl, RDF.type, WF.Workflow) in wf:
                    yield from self.signed_actions(wf, impl)
                else:
                    raise
            yield action, tool, sig

    def convert_to_signatures(self, wf: Workflow, root: Node) -> Graph:
        """Convert a (sub-)workflow that uses concrete tools to a workflow that 
        uses only signatures."""

        g = GraphList()
        bind_all(g, default=VOCAB)

        assert (root, RDF.type, WF.Workflow) in wf
        g.add((root, RDF.type, WF.Workflow))

        counter = count()
        map: dict[Node, BNode] = defaultdict(
            lambda: BNode(f"out{next(counter)}"))

        inputs, outputs = wf.io(root)
        for i, artefact in enumerate(inputs, start=1):
            map[artefact] = BNode(f"in{i}")
            g.add((root, WF.source, map[artefact]))
        for artefact in outputs:
            g.add((root, WF.target, map[artefact]))

        for orig_action, tool, sig in self.signed_actions(wf, root):
            assert sig.uri
            action = BNode()
            g.add((root, WF.edge, action))
            g.add((action, WF.applicationOf, sig.uri))
            for i, artefact in enumerate(
                    wf.inputs(orig_action, labelled=True), start=1):
                g.add((action, WF[f"input{i}"], map[artefact]))

            for pred, artefact in zip(repeat(WF.output),
                    wf.outputs(orig_action)):
                g.add((action, pred, map[artefact]))

        return g

    def update_action(self, wf: Workflow, action: Node) -> None:
        """Analyze a single action (application of a tool or workflow) and 
        figure out the (super)tool it uses, as well as the signature it belongs 
        to. Both will be created, if necessary. This must be done in tandem, 
        because a supertool need only be created when there's a signature with 
        which to associate it."""

        # Propose the tool and signature that would be created if no other 
        # tools or supertools existed in the repository yet
        proposal_sig = AbstractTool.propose(wf, action)

        _, impl = wf.impl(action)

        if impl in self.concrete_tools:
            assert isinstance(impl, URIRef)
        else:
            assert isinstance(impl, BNode), f"{n3(impl)} is not a known " \
                f"tool, but it is also not a supertool"
            supertool = SuperTool.extract(wf, action)
            try:
                supertool = self.find_supertool(supertool)
            except ToolNotFoundError:
                self.register_supertool(supertool)
            impl = supertool.uri
        proposal_sig.implementations.add(impl)

        # Find out how existing signatures relate to the proposed sig
        supersig: AbstractTool | None = None
        subsigs: list[AbstractTool] = []
        for uri, sig in self.abstract_tools.items():
            # Is the URI the same?
            if impl not in sig.implementations:
                continue

            # Is the CCT expression the same?
            if not proposal_sig.matches_cct(sig):
                continue

            # Is the CCD type the same?
            if proposal_sig.subsumes_datatype(sig):
                assert not supersig
                supersig = sig
            elif sig.subsumes_datatype(proposal_sig):
                subsigs.append(sig)

        assert not (supersig and subsigs), """If this assertion fails, the tool 
        repository already contains too many specs."""

        # If there is a signature that covers this action, we simply add the 
        # corresponding tool/workflow as one of its implementations
        if supersig:
            supersig.implementations.add(impl)

        # If the signature is a more general version of existing signature(s), 
        # then we must update the outdated specs.
        elif subsigs:
            assert len(subsigs) <= 1, """If there are multiple specs to 
            replace, we must merge specs and deal with changes to the abstract 
            workflow repository, so let's exclude that possibility for now."""
            subsigs[0].inputs = proposal_sig.inputs
            subsigs[0].output = proposal_sig.output

        # If neither is the case, the action merits an all-new signature
        else:
            self.register_signature(proposal_sig)

    def unique_uri(self, base: str) -> URIRef:
        """Generate a unique URI for a signature based on a name."""
        for i in chain([""], count(start=2)):
            uri = ABSTR[f"{base}{i}"]
            if uri not in self.abstract_tools:
                return uri
        raise RuntimeError("Unreachable")

    def find_signature(self, proposal: AbstractTool) -> AbstractTool:
        """Find a signature that matches the proposed signature."""
        for sig in self.abstract_tools.values():
            if (sig.covers_implementation(proposal)
                    and sig.subsumes_datatype(proposal)
                    and sig.matches_cct(proposal)):
                return sig

        # If we reach here, there was no signature found. Instead, we construct 
        # the error message
        sigs: set[AbstractTool] = set(s for s in self.abstract_tools.values()
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

        raise ToolNotFoundError(
            f"The repository contains no signature for an application of "
            f"{'/'.join(n3(impl) for impl in proposal.implementations)}. "
            "\n\t".join(reasons))

    def register_signature(self, proposal: AbstractTool) -> AbstractTool:
        """Register the proposed signature under a unique name."""
        proposal.uri = self.unique_uri(proposal.name)
        self.abstract_tools[proposal.uri] = proposal
        return proposal

    def find_supertool(self, supertool: SuperTool) -> SuperTool:
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

    def register_supertool(self, supertool: SuperTool) -> None:
        if supertool.uri in self:
            raise ToolAlreadyExistsError(
                f"The supertool {supertool.uri} already exists in the "
                f"repository.")
        self.supertools[supertool.uri] = supertool

    def check_supertool_composition(self):
        """Check that all tools in every supertool are concrete tools."""
        for supertool in self.concrete_supertools:
            if not all(tool in self.concrete_tools for tool in 
                    supertool.constituent_tools):
                raise RuntimeError(
                    "All tools in a supertool must be concrete tools")

    def update(self, wf: Workflow):
        for action, impl in wf.subject_objects(WF.applicationOf):
            if wf.value(action, CCT_.expression):
                self.update_action(wf, action)

    def graph(self) -> Graph:
        g = Graph()
        bind_all(g, default=VOCAB)
        for tool in chain(
                self.abstract_tools.values(),
                self.concrete_tools.values(),
                self.supertools.values()):
            assert isinstance(tool, Tool)
            tool.to_graph(g)
        return g
