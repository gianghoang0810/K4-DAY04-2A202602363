import importlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

module = importlib.import_module("tools.detect_duplicate_ticket.tool")


class DuplicateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.patcher = patch.object(module, "TICKET_DIR", self.root)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def ticket(self, name="LAB-1234ABCD", summary="VPN lỗi kết nối", asset="LT-204"):
        (self.root / (name + ".json")).write_text(json.dumps({
            "ticket_id": name, "summary": summary, "asset_id": asset,
        }), encoding="utf-8")

    def test_exact_vietnamese_normalization_and_no_writes(self):
        self.ticket()
        before = {p.name: p.read_bytes() for p in self.root.iterdir()}
        result = module.detect_duplicate_ticket("vpn loi ket noi!", "lt-204")
        self.assertEqual(result["matches"][0]["similarity"], 1)
        self.assertNotIn("summary", result["matches"][0])
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.root.iterdir()})

    def test_same_words_different_asset_not_duplicate(self):
        self.ticket()
        self.assertEqual(module.detect_duplicate_ticket("VPN lỗi kết nối", "LT-318")["matches"], [])

    def test_similar_threshold_and_limit(self):
        self.ticket(summary="vpn error timeout")
        self.ticket("LAB-11111111", "vpn error timeout")
        result = module.detect_duplicate_ticket("vpn error timeout again", "LT-204", .7, 1)
        self.assertEqual(result["total_matches"], 2)
        self.assertEqual(len(result["matches"]), 1)
        self.assertEqual(result["matches"][0]["similarity"], .75)
        self.assertEqual(module.detect_duplicate_ticket("vpn error timeout again", "LT-204", .8)["matches"], [])

    def test_bad_records_and_missing_store(self):
        (self.root / "bad.json").write_text("{", encoding="utf-8")
        self.assertEqual(module.detect_duplicate_ticket("vpn")["skipped_records"], 1)
        with patch.object(module, "TICKET_DIR", self.root / "absent"):
            self.assertEqual(module.detect_duplicate_ticket("vpn")["matches"], [])

    def test_invalid_arguments(self):
        for kwargs in [{"summary": "!!!"}, {"summary": "x", "asset_id": "../a"},
                       {"summary": "x", "threshold": float("nan")},
                       {"summary": "x", "max_results": True}]:
            with self.subTest(kwargs=kwargs):
                self.assertIn("error", module.detect_duplicate_ticket(**kwargs))

    def test_no_asset_only_matches_no_asset(self):
        self.ticket(asset=None)
        self.assertEqual(module.detect_duplicate_ticket("VPN lỗi kết nối")["total_matches"], 1)


if __name__ == "__main__":
    unittest.main()
