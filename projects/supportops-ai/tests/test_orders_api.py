from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from test_api import request


class OrderApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_order_found_and_not_found(self):
        status, body = await request("GET", "/orders/DEMO-1003")
        self.assertEqual(status, 200)
        self.assertEqual(body["order"]["status"], "out_for_delivery")
        self.assertTrue(body["synthetic"])
        self.assertIsInstance(body["source"]["snapshot_at"], str)
        status, body = await request("GET", "/orders/DEMO-9999")
        self.assertEqual(status, 404)
        self.assertEqual(body["outcome"], "not_found")
        self.assertIsNone(body["order"])

    async def test_invalid_id_is_rejected(self):
        for path in ["/orders/not-an-id", "/orders/DEMO-12", "/orders/DEMO-10001"]:
            status, _ = await request("GET", path)
            self.assertEqual(status, 422)

    async def test_unavailable_dataset_has_503(self):
        with tempfile.TemporaryDirectory() as folder, patch("supportops.orders.ORDERS_PATH", Path(folder) / "missing"):
            status, body = await request("GET", "/orders/DEMO-1001")
        self.assertEqual(status, 503)
        self.assertEqual(body["outcome"], "unavailable")

    async def test_no_mutation_route(self):
        for method in ["POST", "PUT", "PATCH", "DELETE"]:
            status, _ = await request(method, "/orders/DEMO-1001", {"status": "cancelled"})
            self.assertEqual(status, 405)

    async def test_ticket_status_serializes_snapshot(self):
        with patch("supportops.api.MODE", "demo"), patch("supportops.api.STRATEGY", "lexical"):
            status, body = await request("POST", "/tickets", {"question": "Como está o pedido?", "request_type": "order_status", "order_id": "DEMO-1004"})
        self.assertEqual(status, 200)
        self.assertEqual(body["answer_kind"], "order_status")
        self.assertEqual(body["order_lookup"]["order"]["status"], "delivered")
        self.assertIsInstance(body["order_lookup"]["source"]["snapshot_at"], str)

    async def test_combined_ticket_and_missing_order(self):
        with patch("supportops.api.MODE", "demo"), patch("supportops.api.STRATEGY", "lexical"):
            for order_id in ["DEMO-1002", "DEMO-9999"]:
                status, body = await request("POST", "/tickets", {"question": "cancelamento", "request_type": "order_policy", "order_id": order_id})
                self.assertEqual(status, 200)
                if order_id == "DEMO-1002":
                    self.assertEqual(body["answer_kind"], "order_and_policy")
                    self.assertTrue(body["policy_section"]["citations"])
                else:
                    self.assertEqual(body["inference_status"], "skipped_order_lookup")
                    self.assertIsNone(body["policy_section"])

    async def test_invalid_ticket_scope_is_422(self):
        for extra in [{"request_type": "order_status"}, {"order_id": "DEMO-1001"},
                      {"request_type": "cancel_order", "order_id": "DEMO-1001"},
                      {"request_type": "order_status", "order_id": "DEMO-1001", "action": "cancel"}]:
            status, _ = await request("POST", "/tickets", {"question": "pedido", **extra})
            self.assertEqual(status, 422)

    async def test_freeform_order_policy_returns_422(self):
        with patch("supportops.api.MODE", "ollama"):
            status, _ = await request("POST", "/tickets", {"question": "reembolso", "request_type": "order_policy", "order_id": "DEMO-1001"})
        self.assertEqual(status, 422)
