"""AES-256-GCM encryption: password-protected .wtbackup files and field encryption."""
from __future__ import annotations

import base64
import os
import tempfile
from pathlib import Path
from typing import Union

from ..core.database import Database

MAGIC = b"WTB1"
SCRYPT_N, SCRYPT_R, SCRYPT_P = 2 ** 15, 8, 1


class DecryptError(Exception):
    """Wrong password or corrupted/tampered data."""


def _key(password: str, salt: bytes) -> bytes:
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
    if not password:
        raise ValueError("password required")
    return Scrypt(salt=salt, length=32, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P).derive(password.encode("utf-8"))


def encrypt_bytes(password: str, data: bytes) -> bytes:
    """Format: MAGIC | salt(16) | nonce(12) | ciphertext+tag. The header is authenticated."""
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    salt, nonce = os.urandom(16), os.urandom(12)
    return MAGIC + salt + nonce + AESGCM(_key(password, salt)).encrypt(nonce, data, MAGIC + salt)


def decrypt_bytes(password: str, blob: bytes) -> bytes:
    from cryptography.exceptions import InvalidTag
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    if len(blob) < 4 + 16 + 12 + 16 or blob[:4] != MAGIC:
        raise DecryptError("not a WorkTracker backup")
    salt, nonce, ct = blob[4:20], blob[20:32], blob[32:]
    try:
        return AESGCM(_key(password, salt)).decrypt(nonce, ct, MAGIC + salt)
    except InvalidTag:
        raise DecryptError("wrong password or corrupted file") from None


def encrypt_text(password: str, text: str) -> str:
    """For sensitive fields (e.g. private notes) stored as base64 text."""
    return base64.b64encode(encrypt_bytes(password, text.encode("utf-8"))).decode("ascii")


def decrypt_text(password: str, token: str) -> str:
    return decrypt_bytes(password, base64.b64decode(token)).decode("utf-8")


def encrypted_backup(db: Database, dest: Union[str, Path], password: str) -> Path:
    with tempfile.TemporaryDirectory() as d:
        raw = db.backup(Path(d) / "snap.db").read_bytes()
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(encrypt_bytes(password, raw))
    return dest


def restore_backup(src: Union[str, Path], dest_db: Union[str, Path], password: str) -> Database:
    """Decrypt into ``dest_db`` (refuses to overwrite) and open it, verifying integrity."""
    dest_db = Path(dest_db)
    if dest_db.exists():
        raise FileExistsError(dest_db)
    dest_db.write_bytes(decrypt_bytes(password, Path(src).read_bytes()))
    db = Database(dest_db)
    if not db.integrity_ok():
        db.close()
        dest_db.unlink()
        raise DecryptError("restored database failed integrity check")
    return db
