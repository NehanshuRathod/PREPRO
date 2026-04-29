from __future__ import annotations

import json
import mimetypes
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.feature_engineering import engineer_features
from backend.model import BehavioralModel, write_jsonl


FRONTEND_DIR = ROOT / "frontend"
DATA_DIR = ROOT / "data"
MODEL = BehavioralModel(DATA_DIR / "models")


class AppHandler(BaseHTTPRequestHandler):
    server_version = "BehavioralAssessment/1.0"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/api/health":
            self._send_json(
                {
                    "ok": True,
                    "model_mode": MODEL.mode,
                    "message": "Behavioral assessment server is running.",
                }
            )
            return

        self._serve_static(parsed.path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path != "/api/score":
            self._send_json({"error": "Not found"}, status=404)
            return

        try:
            payload = self._read_json()
            events = payload.get("events", [])
            if not isinstance(events, list):
                raise ValueError("events must be a list")

            user_id = str(payload.get("user_id") or f"user-{int(time.time())}")
            features = engineer_features(events)
            scoring = MODEL.score(features)
            response = {
                "user_id": user_id,
                "features": features,
                **scoring,
                "created_at": int(time.time()),
            }

            write_jsonl(DATA_DIR / "events.jsonl", {"user_id": user_id, "events": events})
            write_jsonl(DATA_DIR / "scores.jsonl", response)
            self._send_json(response)
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=400)

    def _serve_static(self, request_path: str) -> None:
        clean_path = request_path.lstrip("/")
        if clean_path == "":
            clean_path = "index.html"

        target = (FRONTEND_DIR / clean_path).resolve()
        if not str(target).startswith(str(FRONTEND_DIR.resolve())) or not target.exists():
            target = FRONTEND_DIR / "index.html"

        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        self.wfile.write(target.read_bytes())

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        if not body:
            return {}
        return json.loads(body)

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        print("%s - %s" % (self.address_string(), format % args))


def main() -> None:
    host = "127.0.0.1"
    port = 8000
    server = ThreadingHTTPServer((host, port), AppHandler)
    print(f"Server running at http://{host}:{port}")
    print(f"Model mode: {MODEL.mode}")
    server.serve_forever()


if __name__ == "__main__":
    main()

