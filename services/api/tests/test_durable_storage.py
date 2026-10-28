from scos import storage
from scos.config import RUNTIME


def test_hosted_reads_work_without_local_mirror(monkeypatch):
    file = RUNTIME / "remote-only.png"
    file.write_bytes(b"synthetic immutable original bytes")
    key, digest, size = storage.put(file)
    mirror = RUNTIME / key
    if mirror.exists():
        mirror.unlink()
    monkeypatch.setattr(storage, "HOSTED", True)
    assert storage.read(key, digest) == b"synthetic immutable original bytes"


def test_same_bytes_share_immutable_key():
    p = RUNTIME / "immutable.txt"
    p.write_bytes(b"one immutable upload")
    a = storage.put(p)
    b = storage.put(p)
    assert a == b
