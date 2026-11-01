"""Public pages only, with DNS pinning and validation at every redirect."""

import http.client
import ipaddress
import socket
from html.parser import HTMLParser
from urllib.parse import quote, urljoin, urlsplit

MAX_PAGE_BYTES = 2 * 1024 * 1024


class LinkError(ValueError):
    pass


def validate_url(url: str):
    try:
        parsed = urlsplit(url)
        if (
            len(url) > 2048
            or any(ord(char) <= 32 or ord(char) == 127 for char in url)
            or "\\" in url
            or parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.port not in {None, 80 if parsed.scheme == "http" else 443}
        ):
            raise ValueError
        # Force IDNA validation before any connection is made.
        parsed.hostname.encode("idna")
        return parsed
    except ValueError, UnicodeError:
        raise LinkError(
            "Use a public HTTP(S) URL without credentials, on its standard port."
        ) from None


def public_addresses(host: str, port: int) -> list[str]:
    addresses = list(
        dict.fromkeys(
            item[4][0]
            for item in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        )
    )
    if not addresses:
        raise LinkError("The page address could not be resolved.")
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if (
            not ip.is_global
            or ip.is_multicast
            or ip.is_reserved
            or (ip.version == 6 and (ip.ipv4_mapped or ip.sixtofour or ip.teredo))
        ):
            raise LinkError(
                "Internal or special-use network destinations are not allowed."
            )
    return addresses


def pinned_connection(parsed, address: str):
    host = parsed.hostname.encode("idna").decode("ascii")
    port = 443 if parsed.scheme == "https" else 80
    cls = (
        http.client.HTTPSConnection
        if parsed.scheme == "https"
        else http.client.HTTPConnection
    )
    connection = cls(host, port, timeout=5)
    # HTTP Host and TLS SNI/certificate verification still use the original host.
    # The socket connects to the already validated literal IP, never re-resolving it.
    connection._create_connection = lambda _, timeout, source_address: (
        socket.create_connection((address, port), timeout, source_address)
    )
    return connection


class PageText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript", "template"}:
            self.hidden += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript", "template"}:
            self.hidden = max(0, self.hidden - 1)
        elif not self.hidden:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def fetch_public(url: str) -> str:
    for redirect in range(4):
        parsed = validate_url(url)
        addresses = public_addresses(
            parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80)
        )
        connection = pinned_connection(parsed, addresses[0])
        try:
            path = parsed.path or "/"
            if parsed.query:
                path += "?" + parsed.query
            path = quote(path, safe="/%?=&:@!$'()*+,;~-._")
            connection.request(
                "GET",
                path,
                headers={
                    "User-Agent": "CareerAssistant/0.1",
                    "Accept": "text/html,text/plain",
                    "Accept-Encoding": "identity",
                },
            )
            response = connection.getresponse()
            if response.status in {301, 302, 303, 307, 308}:
                location = response.getheader("Location")
                if not location or redirect == 3:
                    raise LinkError("The page has too many or invalid redirects.")
                url = urljoin(url, location)
                continue
            if response.status != 200:
                raise LinkError("The page is inaccessible or requires a login.")
            media_type = (
                (response.getheader("Content-Type") or "")
                .split(";", 1)[0]
                .strip()
                .lower()
            )
            if media_type not in {"text/html", "text/plain", "text/markdown"}:
                raise LinkError(
                    "This URL is not a text page. Upload the document instead."
                )
            if response.getheader("Content-Encoding", "identity").lower() != "identity":
                raise LinkError("The page requires unsupported compression.")
            content = response.read(MAX_PAGE_BYTES + 1)
            if len(content) > MAX_PAGE_BYTES:
                raise LinkError("The page exceeds the 2 MiB retrieval limit.")
            # Public sources may be English/Spanish; UTF-8 is the default.
            charset = response.headers.get_content_charset() or "utf-8"
            text = content.decode(charset, errors="replace")
            if media_type == "text/html":
                parser = PageText()
                parser.feed(text)
                text = " ".join(parser.parts)
            return text
        finally:
            connection.close()
    raise LinkError("The page could not be retrieved.")
