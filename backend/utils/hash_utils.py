import hashlib

def compute_sha256(file_path: str) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def compute_sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()