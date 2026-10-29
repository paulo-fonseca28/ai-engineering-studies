import json
import unittest
from supportops.api import app


async def request(method, path, payload=None):
    messages = []
    body = json.dumps(payload).encode() if payload is not None else b""
    scope = {"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
             "method": method, "scheme": "http", "path": path, "raw_path": path.encode(),
             "query_string": b"", "headers": [(b"content-type", b"application/json")],
             "client": ("127.0.0.1", 1), "server": ("testserver", 80), "root_path": ""}
    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}
    async def send(message):
        messages.append(message)
    await app(scope, receive, send)
    status = next(m["status"] for m in messages if m["type"] == "http.response.start")
    content = b"".join(m.get("body", b"") for m in messages if m["type"] == "http.response.body")
    return status, json.loads(content)


class ApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_health(self):
        status, body = await request("GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "ok")

    async def test_ticket_contract(self):
        status, body = await request("POST", "/tickets", {"question": "reembolso"})
        self.assertEqual(status, 200)
        self.assertTrue(body["sources"])
        self.assertIn(body["inference_status"], {"demo", "completed", "failed"})
        self.assertTrue(set(body["citations"]) <= {s["id"] for s in body["sources"]})

    async def test_rejects_invalid_question(self):
        for payload in [{}, {"question": "   "}, {"question": "x" * 4001}, {"question": 123}]:
            status, _ = await request("POST", "/tickets", payload)
            self.assertEqual(status, 422)

    async def test_unknown_topic_requires_review(self):
        status, body = await request("POST", "/tickets", {"question": "astronomia galáxia"})
        self.assertEqual(status, 200)
        self.assertTrue(body["needs_review"])
        self.assertEqual(body["inference_status"], "skipped_no_sources")
