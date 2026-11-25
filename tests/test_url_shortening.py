import io
import unittest
from urllib.error import URLError
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch

import URL_Shortening


class URLShorteningTests(unittest.TestCase):
    @patch("URL_Shortening.urllib.request.urlopen")
    def test_shortens_url_through_tinyurl(self, urlopen):
        original_url = "https://example.com/a path?value=hello world"
        urlopen.return_value = io.BytesIO(b"https://tinyurl.com/abc123\n")

        short_url = URL_Shortening.shorten_url(original_url)

        self.assertEqual(short_url, "https://tinyurl.com/abc123")
        request = urlopen.call_args.args[0]
        self.assertEqual(
            parse_qs(urlparse(request.full_url).query),
            {"url": [original_url]},
        )
        self.assertEqual(urlopen.call_args.kwargs, {"timeout": 4})

    @patch("URL_Shortening.urllib.request.urlopen")
    def test_rejects_service_error_text(self, urlopen):
        urlopen.return_value = io.BytesIO(b"Error: invalid URL")

        with self.assertRaisesRegex(
            ValueError, "shortening service returned an invalid response"
        ):
            URL_Shortening.shorten_url("https://example.com")

    @patch("URL_Shortening.urllib.request.urlopen")
    def test_reports_network_failure_without_making_a_fake_link(self, urlopen):
        urlopen.side_effect = URLError("offline")

        with self.assertRaises(URLError):
            URL_Shortening.shorten_url("https://example.com")


if __name__ == "__main__":
    unittest.main()
