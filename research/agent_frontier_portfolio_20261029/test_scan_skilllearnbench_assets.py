from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from research.agent_frontier_portfolio_20261029.scan_skilllearnbench_assets import scan


class AssetScanTest(unittest.TestCase):
    def test_exact_contents_not_filename_define_overlap(self):
        with TemporaryDirectory() as tmp:
            tasks = Path(tmp)
            for family, instance, name, data in [
                ("a", "a-1", "one.csv", b"same"),
                ("a", "a-2", "two.csv", b"same"),
                ("b", "b-1", "one.csv", b"different"),
            ]:
                env = tasks / family / instance / "environment"
                env.mkdir(parents=True)
                (env / name).write_bytes(data)
                (env / "Dockerfile").write_text("FROM scratch")
                (env / ".gitkeep").write_bytes(b"")
            result = scan(tasks)
            self.assertEqual((result["task_families"], result["task_instances"]), (2, 3))
            self.assertEqual(result["shared_byte_hash_groups"], 1)
            self.assertEqual(result["shared_across_families_groups"], 0)
            self.assertEqual(result["skipped_empty_files"], 3)
            self.assertEqual(result["identical_nonempty_content_sets"], [["a/a-1", "a/a-2"]])


if __name__ == "__main__":
    unittest.main()
