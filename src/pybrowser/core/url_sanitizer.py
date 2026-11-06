"""URL parsing, sanitization, and omnibar search query resolution."""

from __future__ import annotations

import re
import urllib.parse
from typing import Final

from pybrowser.core.logger import get_logger

logger = get_logger(__name__)

# RFC-compliant domain name & IP regex patterns
_DOMAIN_REGEX: Final[re.Pattern[str]] = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,63}(?::\d{1,5})?(?:/.*)?$",
    re.IGNORECASE,
)

_IPV4_REGEX: Final[re.Pattern[str]] = re.compile(
    r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
    r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(?::\d{1,5})?(?:/.*)?$"
)

_LOCALHOST_REGEX: Final[re.Pattern[str]] = re.compile(
    r"^localhost(?::\d{1,5})?(?:/.*)?$",
    re.IGNORECASE,
)

_SCHEME_REGEX: Final[re.Pattern[str]] = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://")


class URLSanitizer:
    """Sanitizes user omnibar input into validated URLs or web searches."""

    def __init__(self, search_template: str = "https://duckduckgo.com/?q={query}") -> None:
        """Initialize the sanitizer.

        Args:
            search_template: URL template with '{query}' placeholder for search fallback.
        """
        self._search_template = search_template

    def resolve(self, input_text: str) -> str:
        """Convert omnibar input into an absolute URL or search engine query.

        Args:
            input_text: Raw string entered by user.

        Returns:
            Resolved absolute URL string.
        """
        cleaned = input_text.strip()
        if not cleaned:
            return "about:blank"

        # Check for internal or special schemes
        if cleaned.lower() in ("about:blank", "about:config"):
            return cleaned.lower()

        # If already has a scheme, validate and return
        if _SCHEME_REGEX.match(cleaned):
            parsed = urllib.parse.urlsplit(cleaned)
            if parsed.scheme.lower() in ("http", "https", "file", "data", "view-source"):
                return cleaned
            # Unknown or unsafe scheme -> fallback to search
            return self._build_search_url(cleaned)

        # Check if the input contains spaces -> treat as search query
        if " " in cleaned:
            return self._build_search_url(cleaned)

        # Check for localhost with optional port/path
        if _LOCALHOST_REGEX.match(cleaned):
            return f"http://{cleaned}"

        # Check for direct IPv4 address
        if _IPV4_REGEX.match(cleaned):
            return f"http://{cleaned}"

        # Check for standard domain name
        if _DOMAIN_REGEX.match(cleaned):
            return f"https://{cleaned}"

        # Otherwise fallback to web search
        return self._build_search_url(cleaned)

    def _build_search_url(self, query: str) -> str:
        """Build search engine URL with safely encoded query parameters."""
        encoded_query = urllib.parse.quote_plus(query)
        return self._search_template.format(query=encoded_query)

    @staticmethod
    def is_secure(url: str) -> bool:
        """Check whether the given URL uses a secure encrypted protocol.

        Args:
            url: Target URL string.

        Returns:
            True if HTTPS or local internal page, False otherwise.
        """
        if not url:
            return False
        parsed = urllib.parse.urlsplit(url)
        return parsed.scheme.lower() in ("https", "about")

    @staticmethod
    def extract_domain(url: str) -> str:
        """Extract clean hostname from URL for display.

        Args:
            url: Absolute URL string.

        Returns:
            Domain hostname or raw URL if parsing fails.
        """
        try:
            parsed = urllib.parse.urlsplit(url)
            return parsed.netloc or parsed.path
        except Exception:
            return url
