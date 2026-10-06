from appsupport import (
    AppReference,
    app_support_url,
    detect_app_store,
    is_supported_app_store_url,
    parse_app_store_url,
)


def test_detects_apple_store_url():
    url = "https://apps.apple.com/us/app/duolingo/id570060128"
    parsed = parse_app_store_url(url)

    assert parsed is not None
    assert isinstance(parsed, AppReference)
    assert parsed.store == "apple_app_store"
    assert parsed.app_id == "570060128"
    assert detect_app_store(url) == "apple_app_store"
    assert is_supported_app_store_url(url) is True


def test_detects_google_play_url():
    url = "https://play.google.com/store/apps/details?id=com.google.android.apps.translate&hl=en"
    parsed = parse_app_store_url(url)

    assert parsed is not None
    assert parsed.store == "google_play"
    assert parsed.package == "com.google.android.apps.translate"
    assert parsed.app_id == "com.google.android.apps.translate"


def test_detects_microsoft_store_url():
    url = "https://apps.microsoft.com/detail/9NBLGGH4NNS1"
    parsed = parse_app_store_url(url)

    assert parsed is not None
    assert parsed.store == "microsoft_store"
    assert parsed.app_id == "9NBLGGH4NNS1"


def test_builds_friendly_support_urls():
    assert app_support_url("apple_app_store", "570060128") == "https://apps.apple.com/app/id570060128"
    assert app_support_url("google_play", "com.example.app") == "https://play.google.com/store/apps/details?id=com.example.app"
    assert app_support_url("microsoft_store", "9NBLGGH4NNS1") == "https://apps.microsoft.com/detail/9NBLGGH4NNS1"
    assert app_support_url("amazon_appstore", "com.example.app") == "https://www.amazon.com/gp/mas/dl/android?p=com.example.app"


def test_app_support_url_rejects_unknown_store_and_accepts_reference():
    try:
        app_support_url("unknown-store", "abc")
    except ValueError:
        pass
    else:
        raise AssertionError("Unsupported stores should raise ValueError")

    ref = AppReference("apple_app_store", "570060128")
    assert app_support_url(ref) == "https://apps.apple.com/app/id570060128"


def test_unsupported_store_rejected():
    assert parse_app_store_url("https://example.com/app/123") is None
    assert is_supported_app_store_url("https://example.com/app/123") is False
