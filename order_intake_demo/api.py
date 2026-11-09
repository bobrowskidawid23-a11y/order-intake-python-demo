from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .pipeline import process_order


class OrderHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802 - required by BaseHTTPRequestHandler
        if self.path != "/orders/process":
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length))
            result = process_order(payload)
            status = HTTPStatus.OK if result["status"] == "ready" else HTTPStatus.UNPROCESSABLE_ENTITY
        except (ValueError, TypeError, json.JSONDecodeError):
            result = {"status": "invalid", "errors": ["invalid_json"]}
            status = HTTPStatus.BAD_REQUEST

        body = json.dumps(result, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run(host: str = "127.0.0.1", port: int = 8080) -> None:
    server = ThreadingHTTPServer((host, port), OrderHandler)
    print(f"Demo API: http://{host}:{port}/orders/process")
    server.serve_forever()


if __name__ == "__main__":
    run()
