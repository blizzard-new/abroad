from __future__ import annotations

from functools import lru_cache
from urllib.parse import urlsplit


@lru_cache(maxsize=4096)
def canonical_source_url_identity(source_url: str) -> str:
    """Normalize only URL components whose identity is case-insensitive."""

    if any(ord(character) < 0x20 or ord(character) == 0x7F for character in source_url):
        return source_url
    value = source_url.strip()
    if not value:
        return ""
    try:
        parsed = urlsplit(value)
    except ValueError:
        return value
    if not parsed.scheme or not parsed.netloc:
        return value

    userinfo, separator, host_and_port = parsed.netloc.rpartition("@")
    userinfo_prefix = f"{userinfo}@" if separator else ""
    if not separator:
        host_and_port = parsed.netloc

    if host_and_port.startswith("["):
        closing_bracket = host_and_port.find("]")
        if closing_bracket < 0:
            return value
        host = host_and_port[1:closing_bracket]
        port_literal = host_and_port[closing_bracket + 1 :]
        if port_literal:
            if not port_literal.startswith(":"):
                return value
            port = port_literal[1:]
            if port and (
                not port.isascii()
                or not port.isdigit()
                or int(port) > 65535
            ):
                return value
        normalized_host_and_port = f"[{host.lower()}]{port_literal}"
    else:
        if host_and_port.count(":") > 1:
            return value
        host, colon, port = host_and_port.rpartition(":")
        if not colon:
            host = host_and_port
            port_literal = ""
        else:
            if port and (
                not port.isascii()
                or not port.isdigit()
                or int(port) > 65535
            ):
                return value
            port_literal = f":{port}"
        if not host:
            return value
        normalized_host_and_port = f"{host.lower()}{port_literal}"

    before_fragment, fragment_separator, _ = value.partition("#")
    query_separator = "?" if "?" in before_fragment else ""
    return (
        f"{parsed.scheme.lower()}://{userinfo_prefix}{normalized_host_and_port}"
        f"{parsed.path}{query_separator}{parsed.query}"
        f"{fragment_separator}{parsed.fragment}"
    )
