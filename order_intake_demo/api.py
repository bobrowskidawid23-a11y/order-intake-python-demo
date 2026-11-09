from __future__ import annotations

import json
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .pipeline import process_order

MAX_BODY_BYTES = 1_048_576


class OrderHandler(BaseHTTPRequestHandler):
    seen_source_ids: set[str] = set()
    seen_lock = threading.Lock()

    def _send_json(self, status: HTTPStatus, result: dict) -> None:
        body = json.dumps(result, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        if self.path != "/orders/process":
            self._send_json(HTTPStatus.NOT_FOUND, {"status": "invalid", "errors": ["route_not_found"]})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 0 or length > MAX_BODY_BYTES:
                self._send_json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"status": "invalid", "errors": ["request_too_large"]})
                return
            payload = json.loads(self.rfile.read(length))
            with self.seen_lock:
                result = process_order(payload, seen_source_ids=self.seen_source_ids)
                source_id = result.get("source_id")
                if result["status"] == "ready" and source_id:
                    self.seen_source_ids.add(source_id)
            status = HTTPStatus.OK if result["status"] in {"ready", "duplicate"} else HTTPStatus.UNPROCESSABLE_ENTITY
        except (ValueError, TypeError, json.JSONDecodeError):
            result = {"status": "invalid", "errors": ["invalid_json"]}
            status = HTTPStatus.BAD_REQUEST

        self._send_json(status, result)

    def log_message(self, format: str, *args) -> None:
        return


def run(host: str = "127.0.0.1", port: int = 8080) -> None:
    server = ThreadingHTTPServer((host, port), OrderHandler)
    print(f"Demo API: http://{host}:{port}/orders/process")
    server.serve_forever()


if __name__ == "__main__":
    run()
