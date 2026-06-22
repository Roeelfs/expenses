import unittest, threading, json
from http.server import BaseHTTPRequestHandler, HTTPServer
from engine import moneytor

class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if "Authorization" not in self.headers:
            self.send_response(401); self.end_headers(); self.wfile.write(b'{"ok":false}'); return
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
        self.wfile.write(json.dumps({"ok": True, "transactions": [{"id": "X", "amount": -5, "date": "2026-02-01"}]}).encode())
    def log_message(self, *a): pass

class MoneytorTest(unittest.TestCase):
    def test_rejects_non_https_base(self):
        with self.assertRaises(moneytor.MoneytorError):
            moneytor.fetch_transactions("http://app.moneytor.co.il/api/v1", "tok", "2026-02-01", "2026-02-28")

    def test_rejects_wrong_host(self):
        with self.assertRaises(moneytor.MoneytorError):
            moneytor.fetch_transactions("https://evil.example.com/api/v1", "tok", "2026-02-01", "2026-02-28")

    def test_parses_transactions_from_a_local_server(self):
        srv = HTTPServer(("127.0.0.1", 0), _Handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{srv.server_address[1]}/api/v1"
        rows = moneytor._fetch_raw(base, "tok", "2026-02-01", "2026-02-28", limit=2000)
        srv.shutdown()
        self.assertEqual(rows[0]["id"], "X")

    def test_maps_401_to_expired_error(self):
        srv = HTTPServer(("127.0.0.1", 0), _Handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{srv.server_address[1]}/api/v1"
        with self.assertRaises(moneytor.MoneytorAuthError):
            moneytor._fetch_raw(base, None, "2026-02-01", "2026-02-28", limit=2000)
        srv.shutdown()

if __name__ == "__main__":
    unittest.main()
