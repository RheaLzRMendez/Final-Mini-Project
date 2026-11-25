import os
import smtplib
import unittest
from unittest.mock import ANY, patch

import SMS_and_Email
import email_provider


class GmailSMTPTests(unittest.TestCase):
    @patch("email_provider.smtplib.SMTP_SSL")
    def test_sends_message_over_gmail_ssl(self, smtp_factory):
        smtp = smtp_factory.return_value.__enter__.return_value

        result = email_provider.send_email(
            "sender@gmail.com",
            "abcd efgh ijkl mnop",
            "recipient@example.com",
            "Test subject",
            "Test body",
        )

        self.assertEqual(result, (True, "Accepted by Gmail SMTP", ""))
        smtp_factory.assert_called_once_with(
            "smtp.gmail.com",
            465,
            timeout=15,
            context=ANY,
        )
        smtp.login.assert_called_once_with("sender@gmail.com", "abcdefghijklmnop")
        message = smtp.send_message.call_args.args[0]
        self.assertEqual(message["From"], "sender@gmail.com")
        self.assertEqual(message["To"], "recipient@example.com")
        self.assertEqual(message["Subject"], "Test subject")
        self.assertEqual(message.get_content().strip(), "Test body")

    @patch("email_provider.smtplib.SMTP_SSL")
    def test_smtp_authentication_failure_is_reported(self, smtp_factory):
        smtp = smtp_factory.return_value.__enter__.return_value
        smtp.login.side_effect = smtplib.SMTPAuthenticationError(
            535, b"Authentication failed"
        )

        success, status, detail = email_provider.send_email(
            "sender@gmail.com",
            "test-app-password",
            "recipient@example.com",
            "Subject",
            "Body",
        )

        self.assertFalse(success)
        self.assertEqual(status, "Failed via Gmail SMTP")
        self.assertIn("Authentication failed", detail)
        smtp.send_message.assert_not_called()

    @patch("email_provider.smtplib.SMTP_SSL")
    def test_invalid_subject_is_reported_without_connecting(self, smtp_factory):
        success, status, detail = email_provider.send_email(
            "sender@gmail.com",
            "test-app-password",
            "recipient@example.com",
            "Subject\nBcc: other@example.com",
            "Body",
        )

        self.assertFalse(success)
        self.assertEqual(status, "Failed via Gmail SMTP")
        self.assertIn("header", detail.lower())
        smtp_factory.assert_not_called()

    @patch.dict(os.environ, {}, clear=True)
    @patch("SMS_and_Email.email_provider.send_email")
    def test_missing_email_credentials_use_simulator(self, send_email):
        result = SMS_and_Email.dispatch_email(
            "", "", "recipient@example.com", "Subject", "Body"
        )

        self.assertTrue(result[0])
        self.assertTrue(result[1].startswith("SIMULATED"))
        send_email.assert_not_called()


if __name__ == "__main__":
    unittest.main()
