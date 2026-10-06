from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Union
from urllib.parse import parse_qs, urlparse
import re


STORE_ALIASES = {
    "apple-app-store": "apple_app_store",
    "apple-appstore": "apple_app_store",
    "app-store": "apple_app_store",
    "ios-app-store": "apple_app_store",
    "apple": "apple_app_store",
    "google-play": "google_play",
    "google-play-store": "google_play",
    "google-play-app-store": "google_play",
    "play-store": "google_play",
    "play": "google_play",
    "microsoft-store": "microsoft_store",
    "microsoft-store-app": "microsoft_store",
    "ms-store": "microsoft_store",
    "windows-store": "microsoft_store",
    "windows-app-store": "microsoft_store",
    "amazon-appstore": "amazon_appstore",
    "amazon-app-store": "amazon_appstore",
    "amazon": "amazon_appstore",
}


@dataclass(frozen=True)
class AppReference:
    store: str
    app_id: str
    package: Optional[str] = None
    source_url: Optional[str] = None

    def normalized_id(self) -> str:
        return self.app_id

    def support_url(self) -> str:
        return app_support_url(self)


class AppSupport:
    @staticmethod
    def parse(url: str) -> Optional[AppReference]:
        return parse_app_store_url(url)

    @staticmethod
    def detect(url: str) -> Optional[str]:
        return detect_app_store(url)

    @staticmethod
    def support_url(store: str, app_id: str) -> str:
        return app_support_url(store, app_id)


def normalize_app_store_name(name: str) -> str:
    value = (name or "").strip().lower().replace("_", "-")
    normalized = re.sub(r"\s+", "-", value)
    return STORE_ALIASES.get(normalized, normalized)


def _extract_netloc(hostname: Optional[str]) -> str:
    return (hostname or "").lower().replace("www.", "")


def detect_app_store(url: str) -> Optional[str]:
    if not url or not isinstance(url, str):
        return None
    value = url.strip()
    if not value:
        return None
    if "://" not in value and not value.startswith("market://"):
        return None

    parsed = urlparse(value)
    host = _extract_netloc(parsed.netloc or parsed.hostname)

    if host in {"apps.apple.com", "itunes.apple.com", "appstore.com"}:
        return "apple_app_store"
    if host in {"play.google.com", "market.android.com"}:
        return "google_play"
    if host == "apps.microsoft.com":
        return "microsoft_store"
    if host == "www.microsoft.com" and "/store/" in parsed.path.lower():
        return "microsoft_store"
    if host in {"amazon.com"}:
        return "amazon_appstore"
    if parsed.scheme == "market":
        return "google_play"
    if parsed.scheme in {"ms-windows-store"}:
        return "microsoft_store"
    return None


def _match_url(path: str, pattern: str) -> Optional[str]:
    match = re.search(pattern, path, flags=re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def parse_app_store_url(url: str) -> Optional[AppReference]:
    if not url or not isinstance(url, str):
        return None
    value = url.strip()
    if not value:
        return None

    if "://" not in value and not value.startswith("market://"):
        return None

    parsed = urlparse(value)
    store = detect_app_store(value)
    if store is None:
        return None

    if store == "apple_app_store":
        app_id = _match_url(parsed.path, r"/(?:app|apps)/[^/]+/id(\d+)")
        if app_id is None:
            app_id = _match_url(parsed.path, r"/(?:app|apps)/id(\d+)")
        if app_id is None:
            app_id = _match_url(parsed.path, r"/(?:app|apps)/[^/]+/(\d+)")
        if app_id is None:
            app_id = _match_url(parsed.path, r"/(?:id)(\d+)$")
        if app_id is None:
            app_id = parse_qs(parsed.query).get("id", [None])[0]
        if app_id is None:
            return None
        return AppReference(store=store, app_id=app_id, package=None, source_url=value)

    if store == "google_play":
        package = parse_qs(parsed.query).get("id", [None])[0]
        if package is None:
            return None
        return AppReference(store=store, app_id=package, package=package, source_url=value)

    if store == "microsoft_store":
        app_id = parse_qs(parsed.query).get("PFN", [None])[0]
        if app_id is None:
            app_id = parse_qs(parsed.query).get("id", [None])[0]
        if app_id is None:
            app_id = _match_url(parsed.path, r"/(?:detail|product|app)/(?:[^/]+/)?([^/?#]+)")
        if app_id is None:
            return None
        return AppReference(store=store, app_id=app_id, package=app_id, source_url=value)

    if store == "amazon_appstore":
        app_id = parse_qs(parsed.query).get("p", [None])[0]
        if app_id is None:
            return None
        return AppReference(store=store, app_id=app_id, package=app_id, source_url=value)

    return None


def is_supported_app_store_url(url: str) -> bool:
    return parse_app_store_url(url) is not None


def find_app_store(url: str) -> Optional[str]:
    return detect_app_store(url)


def app_support_url(store: Union[str, AppReference], app_id: Optional[str] = None) -> str:
    if isinstance(store, AppReference):
        ref = store
        store = ref.store
        app_id = ref.app_id or ref.package

    normalized = normalize_app_store_name(store)
    if not app_id:
        raise ValueError("An app identifier is required to generate a support URL.")

    app_id = str(app_id).strip()
    if not app_id:
        raise ValueError("An app identifier is required to generate a support URL.")

    if normalized == "apple_app_store":
        return f"https://apps.apple.com/app/id{app_id}"
    if normalized == "google_play":
        return f"https://play.google.com/store/apps/details?id={app_id}"
    if normalized == "microsoft_store":
        return f"https://apps.microsoft.com/detail/{app_id}"
    if normalized == "amazon_appstore":
        return f"https://www.amazon.com/gp/mas/dl/android?p={app_id}"

    raise ValueError(f"Unsupported app store: {store}")


def support_url_for_app(app: str, store: Optional[str] = None) -> str:
    if store is None:
        parsed = parse_app_store_url(app)
        if parsed is not None:
            return parsed.support_url()
        raise ValueError(f"Could not determine the app store for: {app}")
    return app_support_url(store, app)
