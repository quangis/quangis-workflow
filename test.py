#!/usr/bin/env python3
from __future__ import annotations
from rdflib import Graph, RDF, Namespace
from rdflib.term import Node
from pathlib import Path
from nose2.tools import params  # type: ignore

# Check whether the files are consistent with the workflow schema. Every tool
# must have a corresponding description. Every tool in a scenario workflow must
# exist in the tools ontology. Check whether blank nodes are never used in
# multiple tools. All blank nodes should only ever be reused in the same
# supertool workflow. Every signature should have at least one input and one
# output. Every abstract tool should either be implemented by a concrete tool,
# or it should be a supertool, or it should be implemented by a supertool. An
# abstract tool is a tool that has a semantics in terms of a CCD signature; a
# supertool might not have a CCD signature, in which case it must implement an
# abstract tool.


WF = Namespace('http://geographicknowledge.de/vocab/Workflow.rdf#')
root_path = Path(__file__).parent

tools = Graph()
tools.parse(root_path / "tools" / "tools.ttl")

workflows = Graph()
for path in root_path.glob("workflows/*.ttl"):
    workflows.parse(path)
wfs = list(workflows.subjects(RDF.type, WF.Workflow))
assert wfs


@params(*wfs)
def test_every_node_has_an_existing_tool(wf: Node):
    # Every node (indicated by wf:edge) in a workflow should have a tool
    # (indicated by wf:applicationOf). Each of those tools must exist in
    # the tool ontology.
    for step in workflows.objects(wf, WF.edge):
        tool = workflows.value(step, WF.applicationOf, any=False)
        assert tool is not None, f"{wf} has no tool"
        assert list(tools.predicate_objects(tool)), f"{tool} is unknown"


if __name__ == '__main__':
    import nose2  # type: ignore
    nose2.main()
