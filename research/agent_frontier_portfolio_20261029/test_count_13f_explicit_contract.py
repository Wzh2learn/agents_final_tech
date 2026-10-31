from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile

from research.agent_frontier_portfolio_20261029.build_13f_conflict_tasks import make_instruction
from research.agent_frontier_portfolio_20261029.count_13f_explicit_contract import count_archive, policy_from_task


class ExplicitContractCountTest(unittest.TestCase):
    def test_counts_rows_only_for_exact_manager_period_and_classes(self):
        task = make_instruction("Example Manager", ["com", "adr"])
        classes, name, period = policy_from_task(task)
        with TemporaryDirectory() as tmp:
            archive = Path(tmp) / "data.zip"
            with ZipFile(archive, "w") as z:
                z.writestr("SUBMISSION.tsv", "ACCESSION_NUMBER\tPERIODOFREPORT\na\t30-SEP-2025\nb\t31-MAR-2025\n")
                z.writestr("COVERPAGE.tsv", "ACCESSION_NUMBER\tFILINGMANAGER_NAME\na\tEXAMPLE MANAGER\nb\tExample Manager\n")
                z.writestr("INFOTABLE.tsv", "ACCESSION_NUMBER\tTITLEOFCLASS\na\tCOM\na\tADR\na\t ADR\nb\tCOM\n")
            self.assertEqual(count_archive(archive, classes, name, period), 2)


if __name__ == "__main__":
    unittest.main()
