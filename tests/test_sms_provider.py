import base64
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs
from unittest.mock import patch

import SMS_and_Email
import sms_provider


class TwilioProviderTests(unittest.TestCase):
    def setUp(self):
        class FakeTwilioHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(length).decode("utf-8")
                self.server.requests.append({
                    "method": "POST",
                    "path": self.path,
                    "authorization": self.headers.get("Authorization"),
                    "content_type": self.headers.get("Content-Type"),
                    "form": parse_qs(body),
                })
                self._respond(
                    self.server.post_status,
                    self.server.post_response,
                )

            def do_GET(self):
                self.server.requests.append({
                    "method": "GET",
                    "path": self.path,
                    "authorization": self.headers.get("Authorization"),
                })
                self._respond(
                    self.server.get_status,
                    self.server.get_response,
                )

            def _respond(self, status_code, body):
                encoded = json.dumps(body).encode("utf-8")
                self.send_response(status_code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

            def log_message(self, format_string, *args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), FakeTwilioHandler)
        self.server.requests = []
        self.server.post_status = 201
        self.server.post_response = {"sid": "SM123", "status": "queued"}
        self.server.get_status = 200
        self.server.get_response = {"sid": "SM123", "status": "delivered"}
        self.server_thread = threading.Thread(
            target=self.server.serve_forever,
            daemon=True,
        )
        self.server_thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.server_thread.join(timeout=2)

    @patch("SMS_and_Email.sms_provider.send_sms")
    def test_missing_credentials_use_simulator_without_api_call(self, send_sms):
        result = SMS_and_Email.dispatch_sms(
            "", "", "", "+15550000002", "Hello"
        )

        self.assertTrue(result[0])
        self.assertTrue(result[1].startswith("SIMULATED"))
        send_sms.assert_not_called()

    def test_create_and_check_sms_use_twilio_rest_requests(self):
        sid, initial_status = sms_provider.send_sms(
            "AC123",
            "test-token",
            "+15550000001",
            "+15550000002",
            "Hello from local test",
            base_url=self.base_url,
        )
        delivery_status = sms_provider.get_message_status(
            "AC123",
            "test-token",
            sid,
            base_url=self.base_url,
        )

        self.assertEqual((sid, initial_status), ("SM123", "queued"))
        self.assertEqual(delivery_status, "delivered")
        self.assertEqual(len(self.server.requests), 2)

        post, get = self.server.requests
        account_path = "/2010-04-01/Accounts/AC123/Messages"
        authorization = "Basic " + base64.b64encode(
            b"AC123:test-token"
        ).decode("ascii")
        self.assertEqual(post["method"], "POST")
        self.assertEqual(post["path"], account_path + ".json")
        self.assertEqual(post["authorization"], authorization)
        self.assertEqual(
            post["content_type"],
            "application/x-www-form-urlencoded",
        )
        self.assertEqual(
            post["form"],
            {
                "From": ["+15550000001"],
                "To": ["+15550000002"],
                "Body": ["Hello from local test"],
            },
        )
        self.assertEqual(get["method"], "GET")
        self.assertEqual(get["path"], account_path + "/SM123.json")
        self.assertEqual(get["authorization"], authorization)

    def test_api_error_is_reported_without_hiding_response_message(self):
        self.server.post_status = 400
        self.server.post_response = {
            "code": 21211,
            "message": "Invalid 'To' Phone Number",
        }

        with self.assertRaisesRegex(
            sms_provider.TwilioAPIError,
            "HTTP 400: Invalid 'To' Phone Number",
        ):
            sms_provider.send_sms(
                "AC123",
                "test-token",
                "+15550000001",
                "invalid",
                "Hello",
                base_url=self.base_url,
            )

        self.assertEqual(len(self.server.requests), 1)


if __name__ == "__main__":
    unittest.main()
