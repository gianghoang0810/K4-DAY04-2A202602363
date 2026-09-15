"""Offline probes of existing A–D code. Known gaps are expected failures."""
import importlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

web = importlib.import_module("tools.search_device_info.tool")
ticket = importlib.import_module("tools.create_ticket.tool")


class SecurityTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent)
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        p = patch.object(ticket, "TICKET_DIR", self.root)
        p.start()
        self.addCleanup(p.stop)
        p = patch.dict(os.environ, {"TAVILY_API_KEY": "offline-test-placeholder"})
        p.start()
        self.addCleanup(p.stop)
        response = Mock()
        response.json.return_value = {"results": []}
        p = patch.object(web.requests, "post", return_value=response)
        self.post = p.start()
        self.addCleanup(p.stop)

    def test_internal_id_blocked_before_network(self):
        self.assertEqual(web.search_device_info("Lenovo", "LT-204")["error"], "restricted_internal_identifier")
        self.post.assert_not_called()

    def test_public_query_payload(self):
        web.search_device_info("Lenovo", "ThinkPad T14 Gen 4")
        body = self.post.call_args.kwargs["json"]
        self.assertEqual(body["query"], "Lenovo ThinkPad T14 Gen 4 support documentation official")
        self.assertEqual(body["include_domains"], ["support.lenovo.com", "psref.lenovo.com"])

    def test_unconfirmed_ticket_does_not_write(self):
        result = ticket.create_ticket("VPN failure", confirmed=False)
        self.assertEqual(result["status"], "needs_confirmation")
        self.assertEqual(list(self.root.iterdir()), [])

    def test_sensitive_summary_does_not_write(self):
        result = ticket.create_ticket("password=FAKE_TEST_VALUE", confirmed=True)
        self.assertEqual(result["error"], "restricted_sensitive_data")
        self.assertEqual(list(self.root.iterdir()), [])

    @unittest.expectedFailure
    def test_gap_external_email_should_be_blocked(self):
        web.search_device_info("Lenovo", "ThinkPad assigned to demo@example.invalid")
        self.post.assert_not_called()

    @unittest.expectedFailure
    def test_gap_external_credential_should_be_blocked(self):
        web.search_device_info("Lenovo", "ThinkPad token=FAKE_TEST_VALUE")
        self.post.assert_not_called()

    @unittest.expectedFailure
    def test_gap_repeated_confirmed_request_should_not_duplicate(self):
        ticket.create_ticket("VPN failure", "high", "LT-204", True)
        ticket.create_ticket("VPN failure", "high", "LT-204", True)
        self.assertEqual(len(list(self.root.glob("*.json"))), 1)


if __name__ == "__main__":
    unittest.main()
