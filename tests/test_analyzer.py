import unittest
from analyzer_core import analyze_options


class TestAnalyzer(unittest.TestCase):
    def test_basic_recs(self):
        opts = {"hostname": "R1", "interfaces": "GigabitEthernet0/0 10.0.0.1/24"}
        res = analyze_options(opts)
        self.assertIn("recommendations", res)
        self.assertIsInstance(res["recommendations"], list)
        # Should suggest loopback (because none provided)
        titles = [t for t, _ in res["recommendations"]]
        self.assertIn("Add loopback0", titles)


if __name__ == "__main__":
    unittest.main()
