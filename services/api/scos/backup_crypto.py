"""Authenticated backup envelopes. Keys stay outside both the archive and source control."""

import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAGIC = b"SCOSBACKUP1\x00"


def key_from_env():
    try:
        key = base64.b64decode(os.environ["SCOS_BACKUP_ENCRYPTION_KEY"], validate=True)
        if len(key) != 32:
            raise ValueError("Invalid key length")
        return key
    except (KeyError, ValueError):
        raise RuntimeError("A dedicated base64-encoded 32-byte SCOS backup encryption key is required")


def encrypt(data, key, label):
    nonce = os.urandom(12)
    return MAGIC + nonce + AESGCM(key).encrypt(nonce, data, label.encode())


def decrypt(envelope, key, label):
    if not envelope.startswith(MAGIC):
        raise ValueError("Invalid backup envelope")
    payload = envelope[len(MAGIC) :]
    return AESGCM(key).decrypt(payload[:12], payload[12:], label.encode())
