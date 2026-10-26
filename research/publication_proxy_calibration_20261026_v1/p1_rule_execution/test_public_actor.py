import json
import unittest
from pathlib import Path

from .public_actor import solve


TABLE = """columns: C0= | C1=SELF-INSURED RISKS | C2= | C3=OTHER | C4=
R1 [] C0= | C1=2019 | C2=2018 | C3=2019 | C4=2018
R2 [Current] C0=Current | C1=10 | C2=8 | C3=7 | C4=6
R3 [Non-current] C0=Non-current | C1=430 | C2=419 | C3=457 | C4=423
"""


class PublicActorTests(unittest.TestCase):
    def test_later_minus_earlier_and_visible_header_group(self):
        answer = solve(
            "What is the nominal difference of non-current self-insured risks between 2019 and 2018?",
            TABLE,
        )
        self.assertEqual(answer["evidence_refs"], ["R3:C1", "R3:C2"])
        self.assertEqual(
            answer["program"],
            {"left": {"ref": "R3:C1"}, "op": "sub", "right": {"ref": "R3:C2"}},
        )


    def test_after_change_of_control_scope_is_section_limited(self):
        table = """columns: C0= | C1=Chris | C2=Wister | C3=Robert
R1 [Termination after Change of Control:] C0=Termination after Change of Control: | C1= | C2= | C3=
R2 [Cash Severance(1)] C0=Cash Severance(1) | C1=$1,200,000 | C2=$450,000 | C3=$254,063
R3 [Total] C0=Total | C1= | C2= | C3=
R4 [Termination not in connection with Change of Control:] C0=Termination not in connection with Change of Control: | C1= | C2= | C3=
R5 [Cash Severance(2)] C0=Cash Severance(2) | C1=1 | C2=2 | C3=3
"""
        answer = solve(
            "What is the total cash severance paid by the company if they were to terminate Chris Lien, Wister Walcott and Robert Bertz after Change of Control?",
            table,
        )
        self.assertEqual(answer["evidence_refs"], ["R2:C1", "R2:C2", "R2:C3"])


    def test_direction_reference_conflict_preserves_later_minus_earlier(self):
        table = """columns: C0= | C1=2019 | C2=2018
R1 [Net assets] C0=Net assets | C1=3552 | C2=5507
"""
        answer = solve("What is the change in net assets between 2018 and 2019?", table)
        self.assertEqual(
            answer["program"],
            {"left": {"ref": "R1:C1"}, "op": "sub", "right": {"ref": "R1:C2"}},
        )

    def test_preserved_regression_separates_numeric_and_semantic_identity(self):
        path = Path(__file__).with_name("full_24_regression.json")
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = payload["rows"]
        self.assertEqual(len(rows), 24)
        self.assertEqual(sum(row["actor_numeric_correct"] for row in rows), 23)
        self.assertEqual(
            sum(row["actor"]["unit"] != "UNKNOWN" for row in rows), 14
        )
        self.assertEqual(
            sum(
                row["actor_numeric_correct"]
                and row["actor"]["unit"] != "UNKNOWN"
                and not row["direction_conflict"]
                for row in rows
            ),
            13,
        )
        self.assertEqual(sum(row["direction_conflict"] for row in rows), 1)


if __name__ == "__main__":
    unittest.main()
