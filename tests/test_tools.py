import unittest

from quangis.namespace import EX
from quangis.polytype import Polytype, Dimension
from quangis.tools.tool import Abstraction, Artefact


class TestPolytype(unittest.TestCase):

    def test_tool_permutation(self) -> None:
        dim = Dimension(EX.A, {EX.A: [EX.B, EX.C]})
        tool1 = Abstraction(
            uri=EX.tool1,
            inputs={
                "1": Artefact(Polytype([dim], [EX.B])),
                "2": Artefact(Polytype([dim], [EX.C]))
            },
            output=Artefact(Polytype([dim], [EX.A])),
            cct_expr="true"
        )
        tool2 = Abstraction(
            uri=EX.tool1,
            inputs={
                "1": Artefact(Polytype([dim], [EX.C])),
                "2": Artefact(Polytype([dim], [EX.B]))},
            output=Artefact(Polytype([dim], [EX.A])),
            cct_expr="true"
        )
        tool3 = Abstraction(
            uri=EX.tool1,
            inputs={
                "1": Artefact(Polytype([dim], [EX.A])),
                "2": Artefact(Polytype([dim], [EX.A]))},
            output=Artefact(Polytype([dim], [EX.A])),
            cct_expr="true"
        )

        self.assertFalse(tool1.subsumes_input_datatype(tool2))
        self.assertFalse(tool2.subsumes_input_datatype(tool1))
        self.assertTrue(tool3.subsumes_input_datatype(tool1))
        self.assertFalse(tool1.subsumes_input_datatype(tool3))

        self.assertTrue(tool1.subsumes_input_datatype_permutation(tool2))
        self.assertTrue(tool2.subsumes_input_datatype_permutation(tool1))
        self.assertTrue(tool3.subsumes_input_datatype_permutation(tool1))
        self.assertFalse(tool1.subsumes_input_datatype_permutation(tool3))


if __name__ == '__main__':
    unittest.main()
