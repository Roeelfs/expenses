"""Moneytor HTTP client (stdlib only). Host-pinned HTTPS, no redirects, token never
logged. fetch_transactions() enforces the security pins; _fetch_raw() is the inner
call (localhost-testable). See spec sections 4.1, 7.
"""
from __future__ import annotations
import json, urllib.request, urllib.error
from urllib.parse import urlencode, urlsplit

ALLOWED_HOST = "app.moneytor.co.il"


class MoneytorError(Exception): pass
class MoneytorAuthError(MoneytorError): pass
class MoneytorRateLimit(MoneytorError): pass


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        raise MoneytorError("refusing to follow a redirect (token must not cross origins)")


def _fetch_raw(base_url: str, token, frm: str, to: str, limit: int) -> list:
    qs = urlencode({"from": frm, "to": to, "limit": limit})
    url = f"{base_url}/transactions?{qs}"
    req = urllib.request.Request(url, method="GET")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            raise MoneytorAuthError(f"Moneytor auth failed ({e.code}); token expired or not Premium")
        if e.code == 429:
            raise MoneytorRateLimit(f"rate limited; Retry-After={e.headers.get('Retry-After')}")
        raise MoneytorError(f"HTTP {e.code}")
    if not body.get("ok", True):
        raise MoneytorAuthError("Moneytor returned ok=false")
    return body.get("transactions", [])


def fetch_transactions(base_url: str, token: str, frm: str, to: str, limit: int = 2000) -> list:
    parts = urlsplit(base_url)
    if parts.scheme != "https":
        raise MoneytorError(f"refusing non-HTTPS base URL: {base_url}")
    if parts.hostname != ALLOWED_HOST:
        raise MoneytorError(f"refusing unexpected host: {parts.hostname}")
    return _fetch_raw(base_url, token, frm, to, limit)
