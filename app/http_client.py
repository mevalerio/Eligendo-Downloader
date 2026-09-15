from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import httpx


ALLOWED_HOSTS = {
    "elezionistorico.interno.gov.it",
    "dait.interno.gov.it",
}
REDIRECT_STATUSES = {301, 302, 303, 307, 308}


class UnsafeUrlError(ValueError):
    pass


class UpstreamError(RuntimeError):
    pass


@dataclass(frozen=True)
class Download:
    content: bytes
    final_url: str
    content_type: str | None


def validate_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise UnsafeUrlError("Only HTTPS URLs are allowed.")
    if parsed.username or parsed.password:
        raise UnsafeUrlError("The URL must not contain credentials.")
    if parsed.hostname not in ALLOWED_HOSTS:
        raise UnsafeUrlError(
            "Host not allowed. Use only the official "
            "elezionistorico.interno.gov.it or dait.interno.gov.it domains."
        )
    if parsed.port not in (None, 443):
        raise UnsafeUrlError("Port not allowed.")
    return url


class SafeHttpClient:
    """HTTP client with an allow-list, validated redirects, and rate limiting."""

    def __init__(self, *, timeout: float, interval: float) -> None:
        self.timeout = timeout
        self.interval = max(interval, 0.0)
        self._lock = threading.Lock()
        self._last_request = 0.0
        self._client = httpx.Client(
            timeout=timeout,
            follow_redirects=False,
            headers={
                "User-Agent": "eligendo-api/0.1 (local research; cached requests)",
                "Accept": "text/html,application/zip,text/csv,*/*;q=0.5",
            },
        )

    def close(self) -> None:
        self._client.close()

    def _wait_for_slot(self) -> None:
        with self._lock:
            elapsed = time.monotonic() - self._last_request
            if elapsed < self.interval:
                time.sleep(self.interval - elapsed)
            self._last_request = time.monotonic()

    def get(self, url: str, *, max_bytes: int | None = None) -> Download:
        current_url = validate_url(url)
        for _ in range(6):
            self._wait_for_slot()
            try:
                with self._client.stream("GET", current_url) as response:
                    if response.status_code in REDIRECT_STATUSES:
                        location = response.headers.get("location")
                        if not location:
                            raise UpstreamError("Redirect response has no destination.")
                        current_url = validate_url(urljoin(current_url, location))
                        continue

                    if not 200 <= response.status_code < 300:
                        raise UpstreamError(
                            f"The portal returned HTTP {response.status_code}."
                        )

                    declared_length = response.headers.get("content-length")
                    if (
                        max_bytes
                        and declared_length
                        and int(declared_length) > max_bytes
                    ):
                        raise UpstreamError(
                            "The file exceeds the configured maximum size."
                        )
                    chunks: list[bytes] = []
                    received = 0
                    for chunk in response.iter_bytes():
                        received += len(chunk)
                        if max_bytes and received > max_bytes:
                            raise UpstreamError(
                                "The file exceeds the configured maximum size."
                            )
                        chunks.append(chunk)
                    return Download(
                        content=b"".join(chunks),
                        final_url=str(response.url),
                        content_type=response.headers.get("content-type"),
                    )
            except httpx.HTTPError as exc:
                raise UpstreamError(f"Error connecting to {current_url}: {exc}") from exc
        raise UpstreamError("The portal response contains too many redirects.")
