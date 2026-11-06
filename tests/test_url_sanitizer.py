"""Unit tests for URLSanitizer."""

from __future__ import annotations

import pytest

from pybrowser.core.url_sanitizer import URLSanitizer


@pytest.fixture
def sanitizer() -> URLSanitizer:
    return URLSanitizer("https://duckduckgo.com/?q={query}")


def test_empty_input_resolves_to_blank(sanitizer: URLSanitizer) -> None:
    assert sanitizer.resolve("") == "about:blank"
    assert sanitizer.resolve("   ") == "about:blank"


def test_about_schemes_preserved(sanitizer: URLSanitizer) -> None:
    assert sanitizer.resolve("about:blank") == "about:blank"
    assert sanitizer.resolve("about:config") == "about:config"


def test_https_urls_preserved(sanitizer: URLSanitizer) -> None:
    url = "https://github.com/python/cpython"
    assert sanitizer.resolve(url) == url


def test_plain_domain_upgraded_to_https(sanitizer: URLSanitizer) -> None:
    assert sanitizer.resolve("github.com") == "https://github.com"
    assert sanitizer.resolve("example.org/docs/page") == "https://example.org/docs/page"
    assert sanitizer.resolve("sub.domain.co.uk") == "https://sub.domain.co.uk"


def test_localhost_and_ports(sanitizer: URLSanitizer) -> None:
    assert sanitizer.resolve("localhost") == "http://localhost"
    assert sanitizer.resolve("localhost:8000") == "http://localhost:8000"
    assert sanitizer.resolve("localhost:3000/api") == "http://localhost:3000/api"


def test_ipv4_addresses(sanitizer: URLSanitizer) -> None:
    assert sanitizer.resolve("127.0.0.1") == "http://127.0.0.1"
    assert sanitizer.resolve("192.168.1.10:8080") == "http://192.168.1.10:8080"


def test_search_query_with_spaces(sanitizer: URLSanitizer) -> None:
    result = sanitizer.resolve("pyside6 qt6 tutorial")
    assert result == "https://duckduckgo.com/?q=pyside6+qt6+tutorial"


def test_plain_word_falls_back_to_search(sanitizer: URLSanitizer) -> None:
    result = sanitizer.resolve("python")
    assert result == "https://duckduckgo.com/?q=python"


def test_is_secure(sanitizer: URLSanitizer) -> None:
    assert sanitizer.is_secure("https://example.com") is True
    assert sanitizer.is_secure("about:blank") is True
    assert sanitizer.is_secure("http://example.com") is False
    assert sanitizer.is_secure("file:///home/user/doc.html") is False


def test_extract_domain(sanitizer: URLSanitizer) -> None:
    assert (
        sanitizer.extract_domain("https://news.ycombinator.com/item?id=123")
        == "news.ycombinator.com"
    )
    assert sanitizer.extract_domain("http://localhost:8080/test") == "localhost:8080"
