import socket
from email.message import Message

import pytest

from career_assistant import public_links as links


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "ftp://example.com",
        "https://user:password@example.com",
        "https://example.com:8080",
        "https://example.com/\nheader",
        "https://example.com\\@127.0.0.1",
        "http://",
        "https://example.com:invalid",
    ],
)
def test_invalid_url_syntax_never_resolves(url):
    with pytest.raises(links.LinkError):
        links.validate_url(url)


@pytest.mark.parametrize(
    "address",
    [
        "127.0.0.1",
        "10.0.0.1",
        "169.254.169.254",
        "172.16.0.1",
        "192.168.1.1",
        "0.0.0.0",
        "224.0.0.1",
        "::1",
        "fc00::1",
        "fe80::1",
        "::ffff:8.8.8.8",
        "2002:0808:0808::1",
    ],
)
def test_internal_metadata_multicast_and_ipv6_transition_addresses_are_rejected(
    monkeypatch, address
):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [(None, None, None, None, (address, 443))],
    )
    with pytest.raises(links.LinkError, match="network destinations"):
        links.public_addresses("example.com", 443)


def test_mixed_public_private_dns_is_rejected(monkeypatch):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            (None, None, None, None, (address, 443))
            for address in ["8.8.8.8", "127.0.0.1"]
        ],
    )
    with pytest.raises(links.LinkError):
        links.public_addresses("example.com", 443)


def test_socket_is_pinned_while_http_host_and_tls_name_stay_original(monkeypatch):
    connections = []
    monkeypatch.setattr(
        socket, "create_connection", lambda *args: connections.append(args)
    )
    connection = links.pinned_connection(
        links.validate_url("https://example.com/profile"), "8.8.8.8"
    )
    connection._create_connection(("example.com", 443), 5, None)
    assert connection.host == "example.com"
    assert connections == [(("8.8.8.8", 443), 5, None)]


class FakeResponse:
    def __init__(self, *, status=200, body=b"Public profile", headers=None):
        self.status, self.body = status, body
        self.headers = Message()
        self.headers["Content-Type"] = "text/plain; charset=utf-8"
        for key, value in (headers or {}).items():
            if key in self.headers:
                del self.headers[key]
            self.headers[key] = value

    def getheader(self, name, default=None):
        return self.headers.get(name, default)

    def read(self, limit):
        return self.body[:limit]


def mocked_fetch(monkeypatch, responses):
    requests = []

    class Connection:
        def request(self, *args, **kwargs):
            requests.append((args, kwargs))

        def getresponse(self):
            return responses.pop(0)

        def close(self):
            pass

    monkeypatch.setattr(links, "pinned_connection", lambda *args: Connection())
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda host, *args, **kwargs: [
            (
                None,
                None,
                None,
                None,
                ("127.0.0.1" if host == "internal.invalid" else "8.8.8.8", 443),
            )
        ],
    )
    return requests


def test_public_html_removes_scripts_and_preserves_visible_content(monkeypatch):
    requests = mocked_fetch(
        monkeypatch,
        [
            FakeResponse(
                body=b"<p>Staff engineer</p><script>secret instruction</script>"
                b"<style>hidden</style><p>Madrid</p>",
                headers={"Content-Type": "text/html"},
            )
        ],
    )
    text = links.fetch_public("https://example.com/profile")
    assert "Staff engineer" in text and "Madrid" in text
    assert "secret" not in text and "hidden" not in text
    assert requests[0][1]["headers"]["Accept-Encoding"] == "identity"


def test_redirect_to_internal_destination_is_blocked_before_second_connection(
    monkeypatch,
):
    requests = mocked_fetch(
        monkeypatch,
        [
            FakeResponse(
                status=302, headers={"Location": "http://internal.invalid/admin"}
            )
        ],
    )
    with pytest.raises(links.LinkError, match="network destinations"):
        links.fetch_public("https://example.com")
    assert len(requests) == 1


@pytest.mark.parametrize(
    "response",
    [
        FakeResponse(status=403),
        FakeResponse(headers={"Content-Type": "application/pdf"}),
        FakeResponse(headers={"Content-Encoding": "gzip"}),
        FakeResponse(body=b"x" * (links.MAX_PAGE_BYTES + 1)),
    ],
)
def test_restricted_binary_compressed_or_large_pages_offer_a_safe_failure(
    monkeypatch, response
):
    mocked_fetch(monkeypatch, [response])
    with pytest.raises(links.LinkError):
        links.fetch_public("https://example.com")


def test_relative_redirect_and_redirect_limit(monkeypatch):
    mocked_fetch(
        monkeypatch,
        [FakeResponse(status=302, headers={"Location": "/profile"}), FakeResponse()],
    )
    assert links.fetch_public("https://example.com") == "Public profile"
    mocked_fetch(
        monkeypatch,
        [FakeResponse(status=302, headers={"Location": "/again"}) for _ in range(4)],
    )
    with pytest.raises(links.LinkError, match="redirects"):
        links.fetch_public("https://example.com")
