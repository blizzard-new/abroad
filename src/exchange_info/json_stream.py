"""Incremental readers for reviewed, immutable source bundles."""
import json


def json_array_items(handle, chunk_size=256 * 1024):
    """Incrementally decode a top-level array, rejecting truncation/trailing data."""
    decoder = json.JSONDecoder()
    buffer = ""

    def more():
        nonlocal buffer
        chunk = handle.read(chunk_size)
        buffer += chunk
        return bool(chunk)

    def whitespace():
        nonlocal buffer
        buffer = buffer.lstrip()
        while not buffer and more():
            buffer = buffer.lstrip()

    whitespace()
    if not buffer.startswith("["):
        raise json.JSONDecodeError("Expected an array", buffer, 0)
    buffer = buffer[1:]
    whitespace()
    if not buffer.startswith("]"):
        while True:
            while True:
                try:
                    row, end = decoder.raw_decode(buffer)
                    break
                except json.JSONDecodeError:
                    if not more():
                        raise
            buffer = buffer[end:]
            yield row
            whitespace()
            if buffer.startswith("]"):
                break
            if not buffer.startswith(","):
                raise json.JSONDecodeError("Expected comma or closing bracket", buffer, 0)
            buffer = buffer[1:]
            whitespace()
    buffer = buffer[1:]
    whitespace()
    if buffer:
        raise json.JSONDecodeError("Unexpected trailing data", buffer, 0)

