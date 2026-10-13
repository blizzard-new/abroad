"""Hash source files without retaining full PDFs or response archives in memory."""
import gzip
import hashlib


def file_sha256(path, *, compressed=False):
    opener = gzip.open if compressed else open
    with opener(path, "rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()
