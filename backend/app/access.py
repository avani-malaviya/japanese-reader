"""An optional password for the whole app, for sharing a running copy over a public link.

Set READER_PASSWORD to turn it on. The browser asks once (HTTP Basic: any user name, this
password) and then sends it with every request, so the frontend needs no changes.
"""

import base64
import binascii
import os
import secrets

from fastapi import Request
from fastapi.responses import Response

PASSWORD_ENV = "READER_PASSWORD"


def _password_from(header: str) -> str | None:
    scheme, _, encoded = header.partition(" ")
    if scheme.lower() != "basic":
        return None
    try:
        decoded = base64.b64decode(encoded).decode()
    except (binascii.Error, UnicodeDecodeError):
        return None
    return decoded.partition(":")[2]


def password_gate(password: str):
    """Middleware that answers 401 unless the request carries `password`."""

    async def gate(request: Request, call_next):
        given = _password_from(request.headers.get("authorization", ""))
        if given is None or not secrets.compare_digest(given.encode(), password.encode()):
            return Response(
                "Password required",
                status_code=401,
                headers={"WWW-Authenticate": 'Basic realm="Japanese Reader"'},
            )
        return await call_next(request)

    return gate


def configured_password() -> str | None:
    return os.environ.get(PASSWORD_ENV) or None
