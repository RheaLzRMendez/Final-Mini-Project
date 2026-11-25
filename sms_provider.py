"""Twilio SMS API client implemented with the Python standard library."""

import base64
import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

API_BASE_URL = "https://api.twilio.com"
API_VERSION = "2010-04-01"
REQUEST_TIMEOUT = 15


class TwilioAPIError(Exception):
    """Raised when a Twilio API request fails or returns an invalid response."""


def is_configured(account_sid, auth_token, from_number):
    return all(
        isinstance(value, str) and value.strip()
        for value in (account_sid, auth_token, from_number)
    )


def _authorization_header(account_sid, auth_token):
    credentials = f"{account_sid}:{auth_token}".encode("utf-8")
    encoded_credentials = base64.b64encode(credentials).decode("ascii")
    return f"Basic {encoded_credentials}"


def _decode_json(response_body):
    try:
        result = json.loads(response_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise TwilioAPIError("Twilio returned an invalid JSON response.") from error
    if not isinstance(result, dict):
        raise TwilioAPIError("Twilio returned an unexpected response.")
    return result


def _request_json(account_sid, auth_token, url, method, form_data=None):
    headers = {
        "Accept": "application/json",
        "Authorization": _authorization_header(account_sid, auth_token),
    }
    data = None
    if form_data is not None:
        data = urlencode(form_data).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"

    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            return _decode_json(response.read())
    except HTTPError as error:
        try:
            response_body = error.read()
        finally:
            error.close()
        response_data = _decode_json_or_none(response_body)
        api_message = (
            response_data.get("message")
            if response_data else None
        )
        detail = api_message or error.reason
        raise TwilioAPIError(
            f"Twilio returned HTTP {error.code}: {detail}"
        ) from error
    except (URLError, TimeoutError, OSError, ValueError) as error:
        raise TwilioAPIError(f"Could not reach Twilio: {error}") from error


def _decode_json_or_none(response_body):
    try:
        result = json.loads(response_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return result if isinstance(result, dict) else None


def _message_url(account_sid, message_sid=None, base_url=API_BASE_URL):
    account_path = quote(account_sid, safe="")
    url = (
        f"{base_url.rstrip('/')}/{API_VERSION}/Accounts/"
        f"{account_path}/Messages"
    )
    if message_sid is None:
        return f"{url}.json"
    return f"{url}/{quote(message_sid, safe='')}.json"


def _require_message_fields(response):
    sid = response.get("sid")
    status = response.get("status")
    if not isinstance(sid, str) or not sid or not isinstance(status, str) or not status:
        raise TwilioAPIError("Twilio response is missing its message SID or status.")
    return sid, status


def send_sms(account_sid, auth_token, from_number, to_number, body,
             base_url=API_BASE_URL):
    """Create one SMS and return Twilio's message SID and initial status."""
    if not is_configured(account_sid, auth_token, from_number):
        raise TwilioAPIError("Twilio Account SID, Auth Token, and sender number are required.")
    if not isinstance(to_number, str) or not to_number.strip():
        raise TwilioAPIError("A recipient phone number is required.")
    if not isinstance(body, str) or not body.strip():
        raise TwilioAPIError("An SMS message body is required.")

    response = _request_json(
        account_sid,
        auth_token,
        _message_url(account_sid, base_url=base_url),
        "POST",
        {
            "From": from_number.strip(),
            "To": to_number.strip(),
            "Body": body,
        },
    )
    return _require_message_fields(response)


def get_message_status(account_sid, auth_token, message_sid,
                       base_url=API_BASE_URL):
    """Fetch the current delivery status for a previously created SMS."""
    if not isinstance(account_sid, str) or not account_sid.strip():
        raise TwilioAPIError("A Twilio Account SID is required.")
    if not isinstance(auth_token, str) or not auth_token.strip():
        raise TwilioAPIError("A Twilio Auth Token is required.")
    if not isinstance(message_sid, str) or not message_sid.strip():
        raise TwilioAPIError("A Twilio message SID is required.")

    response = _request_json(
        account_sid,
        auth_token,
        _message_url(account_sid, message_sid, base_url),
        "GET",
    )
    sid, status = _require_message_fields(response)
    if sid != message_sid:
        raise TwilioAPIError("Twilio returned a different message SID.")
    return status
