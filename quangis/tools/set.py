
from __future__ import annotations
import sys
from rdflib.term import Node, URIRef, BNode
from rdflib import Graph
from rdflib.compare import isomorphic
from typing import Iterator
from transforge.list import GraphList
from itertools import count, repeat, chain, combinations, product, permutations
from pathlib import Path
from collections import defaultdict

from quangis.namespace import (bind_all, TOOL, RDF, WF, CCT_, n3, ABSTR)
from quangis.workflow import (Workflow)
from quangis.tools.tool import (Tool, Unit, Multi, Abstraction)


class InputHackError(Exception):
    pass

class IntegrityError(Exception):
    """Tool repository does not satisfy expectations."""
    pass

class ToolAlreadyExistsError(Exception):
    pass

class ToolNotFoundError(KeyError):
    pass

class ToolSet(object):
    """A toolset contains abstractions and tools."""

    def __init__(self) -> None:
        self.unit: dict[URIRef, Unit] = dict()
        self.multi: dict[URIRef, Multi] = dict()
        self.abstract: dict[URIRef, Abstraction] = dict()
        self._original: Graph = Graph()
        super().__init__()

    @staticmethod
    def from_file(*files: Path,
            check_integrity: bool = True) -> ToolSet:
        repo = ToolSet()
        for file in files:
            repo._original.parse(file)

        for tool in Unit.from_graph(repo._original):
            repo.add(tool)
        for sig in Abstraction.from_graph(repo._original):
            repo.add(sig)
        for multitool in Multi.from_graph(repo._original):
            repo.add(multitool)

        if check_integrity:
            print(f"Checking integrity of {files}...", file=sys.stderr)
            if not isomorphic(repo._original, repo.graph()):
                raise RuntimeError(
                    f"Integrity check failed for {files}. It may contain "
                    f"tuples that aren't interpreted by this program, "
                    f"which will be lost if you proceed.")
            else:
                print(f"Files {files} passed check", file=sys.stderr)
        return repo

    # @deprecated
    @property
    def composites(self) -> dict[URIRef, Multi]:
        return self.multi

    # @deprecated
    @property
    def units(self) -> dict[URIRef, Unit]:
        return self.unit

    # @deprecated
    @property
    def abstractions(self) -> dict[URIRef, Abstraction]:
        return self.abstract

    def __getitem__(self, key: URIRef) -> Tool:
        return (self.units.get(key)
            or self.abstractions.get(key)
            or self.composites[key])

    def __contains__(self, tool: URIRef | Tool) -> bool:
        if isinstance(tool, URIRef):
            return (tool in self.abstractions
                or tool in self.units
                or tool in self.composites)
        else:
            return tool.uri in self

    def add(self, item: Tool) -> None:
        if isinstance(item, Unit):
            assert item.uri not in self.units
            self.units[item.uri] = item
        elif isinstance(item, Multi):
            assert item.uri not in self.composites
            self.composites[item.uri] = item
        else:
            assert isinstance(item, Abstraction)
            assert item.uri not in self.abstractions
            self.abstractions[item.uri] = item

    def signed_actions(self, wf: Workflow, root: Node) \
            -> Iterator[tuple[Node, URIRef | Multi, Abstraction]]:
        assert (root, RDF.type, WF.Workflow) in wf

        for action in wf.high_level_actions(root):
            impl = wf.impl(action)
            try:
                proposal_sig = Abstraction.propose(wf, action)
                if impl in self.units:
                    assert isinstance(impl, URIRef)
                    tool = impl
                else:
                    tool = self.find_multitool(
                        Multi.extract(wf, action)).uri
                proposal_sig.implementations.add(tool)
                sig = self.find_abstraction(proposal_sig)
            except ToolNotFoundError:
                if impl and (impl, RDF.type, WF.Workflow) in wf:
                    # print(f"Descending into {wf.value(impl, RDFS.label)}")
                    yield from self.signed_actions(wf, impl)
                else:
                    raise
            else:
                yield action, tool, sig

    def convert_to_abstractions(self, wf: Workflow, root: Node) -> Graph:
        """Convert a (sub-)workflow that uses concrete tools to a workflow that 
        uses only abstractions."""

        g = GraphList()
        bind_all(g, default=TOOL)

        assert (root, RDF.type, WF.Workflow) in wf

        # This is because the root workflow is itself an 'application of' 
        # (subworkflow of) another workflow in Eric's usage
        if isinstance(root, URIRef):
            root_real = root
        else:
            root2 = wf.value(None, WF.applicationOf, root, any=False)
            assert isinstance(root2, URIRef)
            root_real = root2

        g.add((root_real, RDF.type, WF.Workflow))

        counter = count()
        map: dict[Node, BNode] = defaultdict(
            lambda: BNode(f"out{next(counter)}"))

        inputs, outputs = wf.io(root)
        for i, artefact in enumerate(inputs, start=1):
            map[artefact] = BNode(f"in{i}")
            g.add((root_real, WF.source, map[artefact]))
        for artefact in outputs:
            g.add((root_real, WF.target, map[artefact]))

        for orig_action, tool, sig in self.signed_actions(wf, root):
            assert sig.uri
            action = BNode()
            g.add((root_real, WF.edge, action))
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
        figure out the (multi)tool it uses, as well as the abstraction it 
        belongs to. Both will be created, if necessary. This must be done in 
        tandem, because a multitool need only be created when there's a 
        abstraction with which to associate it."""

        # Propose the tool and abstraction that would be created if no other 
        # tools or multitools existed in the repository yet
        proposal_sig = Abstraction.propose(wf, action)

        impl = wf.impl(action)

        if impl in self.units:
            assert isinstance(impl, URIRef)
        else:
            assert isinstance(impl, BNode), f"{n3(impl)} is not a known " \
                f"tool, but it is also not a multitool"
            multitool = Multi.extract(wf, action)
            try:
                multitool = self.find_multitool(multitool)
            except ToolNotFoundError:
                self.register_multitool(multitool)
            impl = multitool.uri
        proposal_sig.implementations.add(impl)

        # Find out how existing abstractions relate to the proposed sig
        supersig: Abstraction | None = None
        subsigs: list[Abstraction] = []
        for uri, sig in self.abstractions.items():
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

        # If there is a abstraction that covers this action, we simply add the 
        # corresponding tool/workflow as one of its implementations
        if supersig:
            supersig.implementations.add(impl)

        # If the abstraction is a more general version of existing 
        # abstraction(s), then we must update the outdated specs.
        elif subsigs:
            assert len(subsigs) <= 1, """If there are multiple specs to 
            replace, we must merge specs and deal with changes to the abstract 
            workflow repository, so let's exclude that possibility for now."""
            subsigs[0].inputs = proposal_sig.inputs
            subsigs[0].output = proposal_sig.output

        # If neither is the case, the action merits an all-new abstraction
        else:
            self.register_abstraction(proposal_sig)

    def unique_uri(self, base: str) -> URIRef:
        """Generate a unique URI for a abstraction based on a name."""
        for i in chain([""], count(start=2)):
            uri = ABSTR[f"{base}{i}"]
            if uri not in self.abstractions:
                return uri
        raise RuntimeError("Unreachable")

    def find_abstraction(self, proposal: Abstraction) -> Abstraction:
        """Find a abstraction that matches the proposed abstraction."""

        for sig in self.abstractions.values():
            if (sig.covers_implementation(proposal)
                    and sig.subsumes_datatype(proposal)
                    and sig.matches_cct(proposal)):
                return sig

        # If we reach here, there was no abstraction found. Instead, we 
        # construct the error message
        sigs: set[Abstraction] = set(s for s in self.abstractions.values()
            if s.covers_implementation(proposal))

        msg = (f"The repository contains no abstraction for an application of "
            f"{'/'.join(n3(impl) for impl in proposal.implementations)}. ")
        if sigs:
            msg += ("The following abstractions for this tool are "
                "insufficient: ")
            attempts = []
            for sig in sigs:
                reasons = []
                if not sig.subsumes_datatype(proposal):
                    reasons.append("CCD mismatch")
                if not sig.matches_cct(proposal):
                    reasons.append("CCT mismatch")
                attempts.append(
                    f"{n3(sig.uri)} ({', '.join(reasons)})")
            msg += "; ".join(attempts)
        else:
            msg += "No abstractions cover this implementation."
        raise ToolNotFoundError(msg)

    def register_abstraction(self, proposal: Abstraction) -> Abstraction:
        """Register the proposed abstraction under a unique name."""
        proposal.uri = self.unique_uri(proposal.name)
        self.abstractions[proposal.uri] = proposal
        return proposal

    def find_multitool(self, multitool: Multi) -> Multi:
        """Find a (super)tool in this tool repository that matches the given 
        one. This is an expensive operation because we have to check for 
        isomorphism with existing multitools."""
        if multitool.uri in self.composites:
            if multitool.match(self.composites[multitool.uri]):
                return multitool
            else:
                raise ToolNotFoundError(
                    f"{n3(multitool.uri)} can be found, but it does not match"
                    f"the given multitool of the same name.")

        for candidate in self.composites.values():
            if multitool.match(candidate):
                return candidate

        raise ToolNotFoundError(
            f"There is no multitool like {n3(multitool.uri)} in the tool "
            f"repository.")

    def register_multitool(self, multitool: Multi) -> None:
        if multitool.uri in self:
            raise ToolAlreadyExistsError(
                f"The multitool {multitool.uri} already exists in the "
                f"repository.")
        self.composites[multitool.uri] = multitool

    def update(self, wf: Workflow):
        for action, impl in wf.subject_objects(WF.applicationOf):
            if wf.value(action, CCT_.expression):
                self.update_action(wf, action)

    def graph(self) -> Graph:
        g = Graph()
        bind_all(g, default=TOOL)
        for tool in chain(
                self.abstractions.values(),
                self.units.values(),
                self.composites.values()):
            assert isinstance(tool, Tool)
            tool.to_graph(g)
        return g

    def input_permutation_hack(self, g: Graph) -> Workflow:
        """See issue #18: Actions in the workflows generated by APE do not 
        preserve the order of the input artefacts as specified in the 
        corresponding tools. This is a limitation of APE.

        We can hack around it by reordering the inputs in a workflow. This 
        method gives a variation of a workflow with inputs ordered so that they 
        match again. Unfortunately, if there are multiple ways in which we can 
        do this ordering, we can't find out which is the 'correct' way."""

        wf = Workflow()
        wf += g

        # Elsewhere I assumed that `Workflow` should contain only one workflow, 
        # but that assumption isn't going to hold here. Just makign a note in 
        # case it comes back to haunt
        for root in g.subjects(RDF.type, WF.Workflow):
            for action in g.objects(root, WF.edge):
                # Collect original inputs and remove them from the workflow
                orig_app_inputs = list(g.objects(action, WF.inputx))
                wf.remove((action, WF.inputx, None))

                # Find tool
                tool = g.value(action, WF.applicationOf, any=False)
                assert isinstance(tool, URIRef)
                abstr = self.abstract[tool]

                # This is a hack within a hack, see issue #23. Sometimes APE uses 
                # the same input multiple times, in which case it does not 
                # duplicate the node. We forcibly duplicate the first input in that 
                # case, which should work at least for the tool for which this 
                # occurred. 
                while len(orig_app_inputs) < len(abstr.inputs):
                    orig_app_inputs.append(orig_app_inputs[0])

                if len(abstr.inputs) != len(orig_app_inputs):
                    raise RuntimeError(
                        f"Number of inputs doesn't correspond for {n3(tool)}")

                # Find tool inputs
                tool_labels, tool_types = zip(*(
                    (label,
                     artefact.type.projection().normalize(clear_empty=True))
                    for label, artefact in abstr.inputs.items()
                ))

                # Find a permutation of inputs that works
                orig_app_nodes_types = [
                    (x, wf.type(x).normalize(clear_empty=True))
                    for x in orig_app_inputs]
                for app_nodes_types in permutations(orig_app_nodes_types):
                    app_nodes, app_types = zip(*app_nodes_types)
                    if all(app_type.subtype(tool_type, full=False)
                           for tool_type, app_type in zip(tool_types, app_types)):
                        for label, node in zip(tool_labels, app_nodes):
                            wf.add((action, WF[f"input{label}"], node))
                        break
                else:

                    msg = [
                        f"No permutations for an application of {tool}.\n",
                        "App uses inputs :\n\t- ",
                        '\n\t- '.join(str(y) for x, y in orig_app_nodes_types),
                        "\nTool uses inputs: \n\t- ",
                        '\n\t- '.join(str(x) for x in tool_types)
                    ]
                    raise InputHackError(''.join(msg))

        return wf

    def check_multi_composed_of_unit_tools(self) -> None:
        """All tools in every multitool are concrete tools."""
        conflicts: set[Node] = set()
        for uri, multitool in self.multi.items():
            for tool in multitool.all_tools:
                if tool not in self.unit:
                    conflicts.add(uri)

        if conflicts:
            raise IntegrityError(
                f"All constituents of a multitool must themselves "
                f"be known concrete unit tools, but this is not the case "
                f"for {n3(conflicts)}.")

    def check_duplicate_unittools(self) -> None:
        """No two unit tools may refer to the same URL."""

        conflicts: set[tuple[Node, Node]] = set()

        for n, m in combinations(self.unit.values(), 2):
            for s, u in product(n.url, m.url):
                if s == u:
                    conflicts.add((n.uri, m.uri))

        if conflicts:
            raise IntegrityError(
                "The following unit tools refer to the same URL: "
                + "; ".join(f"{n3(c[0])} and {n3(c[1])}" for c in conflicts))

    def check_duplicate_multitools(self) -> None:
        """No two multitools may be isomorphic to one another (disregarding 
        IDs)."""
        conflicts: set[tuple[Node, Node]] = set()
        for n, m in combinations(self.multi.values(), 2):
            if n.match(m):
                conflicts.add((n.uri, m.uri))

        if conflicts:
            raise IntegrityError("; ".join(
                f"{n3(c[0])} and {n3(c[1])} are isomorphic."
                for c in conflicts))

    def check_abstractions_are_coupled_to_implementations(self) -> None:
        """All abstractions must have at least one implementation; all 
        multitools must implement at least one abstraction; all unit tools must 
        implement at least one abstraction or occur in at least one 
        multitool."""

        has_abstract: set[URIRef] = set()
        for abstr in self.abstract.values():
            if not abstr.implementations:
                raise IntegrityError(
                    f"{n3(abstr.uri)} has no implementation.")
            has_abstract.update(abstr.implementations)

        # All multitools implement at least one abstraction
        occurs_in_multi: set[URIRef] = set()
        for multi in self.multi.values():
            if multi not in has_abstract:
                raise IntegrityError(
                    f"{n3(multi.uri)} has no abstract counterpart.")
            occurs_in_multi.update(multi.all_tools)

        # All unit tools must either implement an abstraction or occur in a 
        # multitool
        for unit in self.unit.values():
            if unit not in has_abstract and unit not in occurs_in_multi:
                raise IntegrityError(
                    f"{n3(unit.uri)} has no abstraction and does not occur "
                    f"in another tool.")

    def check_empty_ccd(self) -> None:
        """Abstractions must have a non-empty CCD signature (see issue #6), and 
        each of its rdf:types must be part of at least one CCD dimension."""
        for abstr in self.abstract.values():
            for artefact in chain(abstr.inputs.values(), [abstr.output]):
                if artefact.type.empty():
                    raise IntegrityError(
                        f"The CCD type of an artefact associated with " 
                        f"{n3(abstr.uri)}, if any, is too general.")

    def check_subsuming_ccd_signatures(self) -> None:
        """Any pair of abstractions must have at least a differing CCT 
        signature or an independent CCD signature (ie a CCD type that neither 
        subsumes nor is subsumed by the other)."""
        abstrs = list(self.abstract.values())
        for a, b in product(abstrs, abstrs):
            if a != b and a.subsumes_datatype_permutation(b):
                msg = (f"CCD type for {n3(a.uri)} subsumes that "
                    f"of {n3(b.uri)}")
                if a.matches_cct(b):
                    raise IntegrityError(f"CCT expression matches and {msg}")
                else:
                    sys.stderr.write(f"Warning: {msg}\n")

    def check_multitools_input_labels(self) -> None:
        """The IDs of any abstraction that is implemented by a multitool must 
        correspond exactly to the IDs of said multitool. Note that this does 
        NOT check whether the right labels are assigned to the right artefacts: 
        they may still be mixed up."""
        # TODO check whether correct artefacts are labelled
        for abstr in self.abstract.values():
            input_labels = set(abstr.inputs.keys())
            for tool in abstr.implementations:
                if tool in self.multi:
                    input_labels2 = set(self.multi[tool].inputs)
                    if input_labels != input_labels2:
                        raise IntegrityError(
                            f"{input_labels} != {input_labels2}")
