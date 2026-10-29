import os
import pytest
from cryptography.exceptions import InvalidTag
from scos.backup_crypto import encrypt, decrypt, key_from_env


def test_backup_tampering_wrong_key_and_namespace_are_rejected():
    key = os.urandom(32)
    data = b"private owner data and independently retained media"
    sealed = encrypt(data, key, "staging:database")
    assert data not in sealed and decrypt(sealed, key, "staging:database") == data
    for envelope, trial_key, label in (
        (sealed[:-1] + bytes([sealed[-1] ^ 1]), key, "staging:database"),
        (sealed, os.urandom(32), "staging:database"),
        (sealed, key, "production:database"),
    ):
        with pytest.raises(InvalidTag):
            decrypt(envelope, trial_key, label)


def test_backup_requires_a_separate_valid_key(monkeypatch):
    monkeypatch.delenv("SCOS_BACKUP_ENCRYPTION_KEY", raising=False)
    with pytest.raises(RuntimeError):
        key_from_env()
    monkeypatch.setenv("SCOS_BACKUP_ENCRYPTION_KEY", "invalid")
    with pytest.raises(RuntimeError):
        key_from_env()
