import http.client
import json
import threading
import unittest

from order_intake_demo.api import MAX_BODY_BYTES, OrderHandler
from http.server import ThreadingHTTPServer


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        OrderHandler.seen_source_ids = set()
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), OrderHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.port = cls.server.server_address[1]

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def setUp(self):
        OrderHandler.seen_source_ids.clear()

    def post(self, payload):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=2)
        body = json.dumps(payload).encode("utf-8")
        connection.request("POST", "/orders/process", body=body, headers={"Content-Type": "application/json"})
        response = connection.getresponse()
        result = json.loads(response.read())
        connection.close()
        return response.status, result

    def test_rejects_valid_json_with_invalid_shape_without_crashing(self):
        status, result = self.post([])
        self.assertEqual(status, 422)
        self.assertEqual(result["status"], "invalid")

        status, result = self.post({"customer": "Demo", "lines": ["not-an-object"]})
        self.assertEqual(status, 422)
        self.assertEqual(result["review_items"][0]["reason"], "invalid_line")

        status, result = self.post(
            {
                "source_id": ["not", "hashable"],
                "customer": "Demo",
                "lines": [{"sku": "PANEL-WHITE-18", "quantity": 1}],
            }
        )
        self.assertEqual(status, 422)
        self.assertEqual(result["errors"], ["source_id_must_be_a_non_empty_string"])

    def test_repeated_source_id_is_idempotent_through_http(self):
        payload = {
            "source_id": "mail-http-001",
            "customer": "Firma Demo",
            "lines": [{"sku": "PANEL-WHITE-18", "quantity": 1}],
        }
        first_status, first = self.post(payload)
        second_status, second = self.post(payload)

        self.assertEqual(first_status, 200)
        self.assertEqual(first["status"], "ready")
        self.assertEqual(second_status, 200)
        self.assertEqual(second["status"], "duplicate")

    def test_rejects_oversized_body(self):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=2)
        connection.putrequest("POST", "/orders/process")
        connection.putheader("Content-Type", "application/json")
        connection.putheader("Content-Length", str(MAX_BODY_BYTES + 1))
        connection.endheaders()
        response = connection.getresponse()
        result = json.loads(response.read())
        connection.close()

        self.assertEqual(response.status, 413)
        self.assertEqual(result["status"], "invalid")
        self.assertEqual(result["errors"], ["request_too_large"])


if __name__ == "__main__":
    unittest.main()
