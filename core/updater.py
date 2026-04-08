"""
SRK Boost - Auto Updater
GitHub Releases API üzerinden yeni sürüm kontrolü yapar.
"""

import logging
import subprocess
import sys
import os
import threading
import webbrowser
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

CURRENT_VERSION = "2.0.0"
GITHUB_REPO = "Srk3407/Srk-boost"
RELEASES_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
DOWNLOAD_PAGE = f"https://github.com/{GITHUB_REPO}/releases/latest"


def _parse_version(v: str) -> Tuple[int, ...]:
    """'2.0.1' → (2, 0, 1)"""
    try:
        return tuple(int(x) for x in v.lstrip('vV').split('.')[:3])
    except Exception:
        return (0, 0, 0)


def check_for_update(timeout: int = 8) -> Optional[dict]:
    """
    GitHub'dan son sürümü kontrol eder.
    Yeni sürüm varsa {'version': str, 'url': str, 'notes': str} döner.
    Yoksa veya hata varsa None döner.
    """
    try:
        import urllib.request
        import json

        req = urllib.request.Request(
            RELEASES_URL,
            headers={
                'User-Agent': f'SRKBoost/{CURRENT_VERSION}',
                'Accept': 'application/vnd.github.v3+json'
            }
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())

        latest_tag = data.get('tag_name', '').lstrip('vV')
        if not latest_tag:
            return None

        if _parse_version(latest_tag) > _parse_version(CURRENT_VERSION):
            # MSI asset bul
            assets = data.get('assets', [])
            msi_url = next(
                (a['browser_download_url'] for a in assets
                 if a['name'].lower().endswith('.msi')),
                DOWNLOAD_PAGE
            )
            return {
                'version': latest_tag,
                'url': msi_url,
                'notes': data.get('body', '')[:500] or 'Yeni sürüm mevcut.'
            }
    except Exception as e:
        logger.debug(f"Update check failed: {e}")
    return None


class UpdateChecker:
    """Arka planda güncelleme kontrolü yapan sınıf."""

    def __init__(self, on_update_found=None):
        self._callback = on_update_found
        self._thread: Optional[threading.Thread] = None

    def start(self):
        """Arka planda kontrol başlat (thread)."""
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        result = check_for_update()
        if result and self._callback:
            try:
                self._callback(result)
            except Exception as e:
                logger.error(f"Update callback error: {e}")

    @staticmethod
    def open_download(url: str = DOWNLOAD_PAGE):
        """Tarayıcıda indirme sayfasını aç."""
        webbrowser.open(url)
