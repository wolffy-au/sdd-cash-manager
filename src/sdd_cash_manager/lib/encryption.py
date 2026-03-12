"""Encryption helpers for sensitive fields stored by sdd-cash-manager."""

from __future__ import annotations

import base64
import hashlib
from typing import Final

from cryptography.fernet import Fernet, InvalidToken

from sdd_cash_manager.core.config import settings


class SensitiveDataCipher:
    """Wraps Fernet so we can derive a stable key from the configured secret."""

    def __init__(self, key: str | None = None) -> None:
        secret = key or settings.encryption_key
        digest = hashlib.sha256(secret.encode("utf-8")).digest()
        self._fernet: Final[Fernet] = Fernet(base64.urlsafe_b64encode(digest))

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext string and return the token."""
        return self._fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")

    def decrypt(self, token: str) -> str:
        """Decrypt a token previously created by this cipher."""
        try:
            return self._fernet.decrypt(token.encode("utf-8")).decode("utf-8")
        except InvalidToken as exc:
            raise ValueError("Unable to decrypt sensitive value") from exc
