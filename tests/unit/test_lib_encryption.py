from __future__ import annotations

import pytest

from sdd_cash_manager.lib.encryption import SensitiveDataCipher


def test_sensitive_data_cipher_roundtrip():
    cipher = SensitiveDataCipher(key="benchmark-key")
    plaintext = "sensitive notes"
    token = cipher.encrypt(plaintext)
    assert token != plaintext
    assert cipher.decrypt(token) == plaintext
    with pytest.raises(ValueError):
        cipher.decrypt("invalid-token")
