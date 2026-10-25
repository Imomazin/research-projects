"""Polite HTTP client for SEC EDGAR and public index providers.

SEC fair-access rules: declared User-Agent with contact, at most ten requests
per second, back off on 403/429/5xx. Responses are cached on disk so that a
re-run never re-requests a document already retrieved.
"""
from __future__ import annotations

import hashlib
import os
import time
from pathlib import Path

import requests

SEC_USER_AGENT = os.environ.get(
    "SEC_USER_AGENT", "Imo Enang strategic risk research imomazin.ae@gmail.com"
)
BROWSER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36 academic-research"
)
MIN_INTERVAL = 0.125  # eight requests per second, below the SEC ceiling of ten


class Client:
    def __init__(self, cache_dir: Path):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self._last = 0.0
        self.log: list[str] = []

    def _key(self, url: str) -> Path:
        return self.cache_dir / hashlib.sha256(url.encode()).hexdigest()

    def get(self, url: str, sec: bool = True, retries: int = 6, use_cache: bool = True) -> bytes | None:
        path = self._key(url)
        if use_cache and path.exists():
            return path.read_bytes()
        headers = {"User-Agent": SEC_USER_AGENT if sec else BROWSER_AGENT,
                   "Accept-Encoding": "gzip, deflate"}
        delay = 1.0
        for attempt in range(retries):
            wait = MIN_INTERVAL - (time.time() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.time()
            try:
                r = self.session.get(url, headers=headers, timeout=60)
            except requests.RequestException as exc:
                self.log.append(f"ERROR {url} {exc}")
                time.sleep(delay)
                delay *= 2
                continue
            if r.status_code == 200:
                path.write_bytes(r.content)
                return r.content
            if r.status_code == 404:
                self.log.append(f"404 {url}")
                return None
            self.log.append(f"HTTP {r.status_code} {url} attempt {attempt}")
            time.sleep(delay)
            delay = min(delay * 2, 60)
        return None


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
