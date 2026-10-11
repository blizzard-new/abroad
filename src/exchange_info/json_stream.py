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


def read_json_object_array(handle, array_key, on_item, chunk_size=256 * 1024):
    """Return other fields, visiting each selected-array item without retaining it.

    Reject a missing/non-array selected field, duplicate object keys, truncation,
    and trailing content. The visitor must not publish its result before return.
    """
    if chunk_size < 1:
        raise ValueError('chunk_size must be positive')
    decoder = json.JSONDecoder()
    buffer = ''
    eof = False

    def more():
        nonlocal buffer, eof
        chunk = handle.read(chunk_size)
        buffer += chunk
        eof = not chunk
        return bool(chunk)

    def whitespace():
        nonlocal buffer
        buffer = buffer.lstrip(' \t\r\n')
        while not buffer and not eof and more():
            buffer = buffer.lstrip(' \t\r\n')

    def consume(token):
        nonlocal buffer
        whitespace()
        if not buffer.startswith(token):
            raise json.JSONDecodeError(f'Expected {token}', buffer, 0)
        buffer = buffer[len(token):]

    def value():
        nonlocal buffer
        whitespace()
        while True:
            try:
                item, end = decoder.raw_decode(buffer)
            except json.JSONDecodeError:
                if not more():
                    raise
                continue
            # A numeric token can decode successfully before its last digit or
            # exponent arrives. Read enough to establish its actual boundary.
            if end == len(buffer) and not eof:
                more()
                continue
            if end < len(buffer) and buffer[end] not in ' \t\r\n,]}:':
                if more():
                    continue
                raise json.JSONDecodeError('Invalid value boundary', buffer, end)
            buffer = buffer[end:]
            return item

    consume('{')
    summary, seen = {}, set()
    whitespace()
    if not buffer.startswith('}'):
        while True:
            key = value()
            if not isinstance(key, str):
                raise json.JSONDecodeError('Object key must be a string', buffer, 0)
            if key in seen:
                raise json.JSONDecodeError('Duplicate object key', buffer, 0)
            seen.add(key)
            consume(':')
            if key == array_key:
                consume('[')
                whitespace()
                if not buffer.startswith(']'):
                    while True:
                        on_item(value())
                        whitespace()
                        if buffer.startswith(']'):
                            break
                        consume(',')
                consume(']')
            else:
                summary[key] = value()
            whitespace()
            if buffer.startswith('}'):
                break
            consume(',')
    consume('}')
    whitespace()
    if buffer:
        raise json.JSONDecodeError('Unexpected trailing data', buffer, 0)
    if array_key not in seen:
        raise json.JSONDecodeError('Required array is missing', buffer, 0)
    return summary

