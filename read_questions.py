"""This module connects the full pipeline for transforming a natural language
question into a transformation query. In dire need of modularisation."""

from rdflib.term import BNode, Literal
from pathlib import Path
from transforge.namespace import TF, RDF, RDFS
from transforge.graph import TransformationGraph
from transforge.query import TransformationQuery
from transforge.type import Product, TypeOperation
from quangis.cct import cct, R3, R2, Obj, Reg

# TODO until it gets turned into a module...
ROOT = Path(__file__).parent
QUESTION_PARSER = ROOT.parent / "geo-question-parser"

import sys
sys.path.append(str(QUESTION_PARSER))
from QuestionParser import QuestionParser
from TypesToQueryConverter import TQConverter


def question2query(queryEx: dict) -> TransformationQuery:
    """
    Converts a query formatted as a dictionary into a `TransformationQuery`,
    which can be in turn translated to a SPARQL query.
    """
    # This should probably go in a more sane place eventually, when the
    # structure of the modules is more stable

    g = TransformationGraph(cct)
    task = BNode()
    g.add((task, RDF.type, TF.Task))

    def f(q: dict) -> BNode:
        node = BNode()
        t = cct.parse_type(q['after']['cct']).concretize(replace=True)

        # This is a temporary solution: R(x * z, y) is for now converted to the
        # old-style R3(x, y, z)
        if isinstance(t.params[0], TypeOperation) and \
                t.params[0].operator == Product:
            t = R3(t.params[0].params[0], t.params[1], t.params[0].params[1])

        # Another temporary solution. the question parser often returns `R(Obj,
        # x)` where the manually constructed queries ("gold standard") would
        # use `R(Obj, Reg * x)`. So, whenever we encounter the former, we will
        # manually also allow the latter, cf.
        # <https://github.com/quangis/transformation-algebra/issues/79#issuecomment-1210661153>
        if isinstance(t.params[0], TypeOperation) and \
                t.operator == R2 and \
                t.params[0].operator == Obj and \
                t.params[1].operator != Product:
            g.add((node, TF.type, cct.uri(R2(t.params[0], Reg * t.params[1]))))

        g.add((node, TF.type, cct.uri(t)))
        for b in q.get('before', ()):
            g.add((node, TF['from'], f(b)))

        return node

    g.add((task, TF.output, f(queryEx)))
    return TransformationQuery(cct, g)


def parse_question(questionBlock: dict) -> TransformationQuery:
    """Parse a natural language question into a `TransformationQuery` 
    object."""

    # This is opaque and unpythonic and nonmodular
    parser = QuestionParser()
    qParsed = parser.parseQuestionBlock(questionBlock)
    cctAnnotator = TQConverter()
    cctAnnotator.cctToQuery(qParsed, True, True)
    cctAnnotator.cctToExpandedQuery(qParsed, False, False)
    return question2query(qParsed['queryEx'])


def parse_all(file: Path): # -> Iterator[TransformationQuery]:
    import json
    with open(file, 'r') as f:
        objs = json.load(f)
    for obj in objs:
        q = parse_question(obj)
        g = q.graph
        g.add((q.root, RDFS.comment, Literal(obj['question'])))
        print(g.serialize())


parse_all(QUESTION_PARSER / "Data" / "blocklyoutput_retri.json")
