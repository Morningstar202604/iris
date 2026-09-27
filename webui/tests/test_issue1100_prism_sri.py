"""Tests for #1100 — Prism.js SRI integrity check no longer blocks theme CSS."""
import re


def test_prism_theme_link_has_no_integrity():
    """The prism-tomorrow.min.css link must not have an integrity attribute."""
    with open("static/index.html") as f:
        src = f.read()
    # Find the prism-theme link tag
    m = re.search(
        r'<link[^>]*id="prism-theme"[^>]*>',
        src
    )
    assert m, "prism-theme link must exist"
    link_tag = m.group(0)
    assert "integrity=" not in link_tag, \
        "prism-theme link must not have integrity attribute (causes intermittent failures)"


def test_prism_theme_link_is_local_vendor():
    """The prism-theme stylesheet must be served from the local vendor bundle.

    Front-end assets were localized off the jsdelivr CDN so the UI stays
    reachable in mainland China; the link therefore has no crossorigin/SRI
    attributes (both only apply to cross-origin fetches).
    """
    with open("static/index.html") as f:
        src = f.read()
    m = re.search(
        r'<link[^>]*id="prism-theme"[^>]*>',
        src
    )
    assert m, "prism-theme link must exist"
    link_tag = m.group(0)
    assert "static/vendor/prism-tomorrow.min.css" in link_tag, \
        f"prism-theme must load the local vendor stylesheet, got: {link_tag}"
    assert "jsdelivr" not in link_tag, \
        "prism-theme must not reference the jsdelivr CDN"


def test_prism_theme_version_pinned():
    """The prism CSS must resolve to a pinned local vendor file, not a floating CDN URL."""
    with open("static/index.html") as f:
        src = f.read()
    m = re.search(
        r'<link[^>]*id="prism-theme"[^>]*href="([^"]*)"[^>]*>',
        src
    )
    assert m, "prism-theme link must have href"
    href = m.group(1)
    assert href == "static/vendor/prism-tomorrow.min.css", \
        f"Prism CSS must be a pinned local asset, found href: {href}"


def test_prism_js_is_local_vendor():
    """Prism JS bundles must be served from the local vendor directory."""
    with open("static/index.html") as f:
        src = f.read()
    assert re.search(r'static/vendor/prism-core\.min\.js', src), \
        "prism-core.min.js must load from static/vendor"
    assert re.search(r'static/vendor/prism-autoloader\.min\.js', src), \
        "prism-autoloader.min.js must load from static/vendor"


def test_boot_js_set_resolved_theme_no_integrity():
    """_setResolvedTheme in boot.js must not re-apply integrity on theme switch."""
    with open("static/boot.js") as f:
        src = f.read()
    # _setResolvedTheme function must exist
    assert "_setResolvedTheme" in src, "_setResolvedTheme function must exist"
    # Must NOT assign link.integrity with a hash value
    assert not re.search(r'link\.integrity\s*=\s*["\']sha', src), \
        "_setResolvedTheme must not set link.integrity to an SRI hash"
    # Must NOT have a wantIntegrity variable
    assert "wantIntegrity" not in src, \
        "wantIntegrity variable should be removed from _setResolvedTheme"
    # Should clear integrity (set to empty) when switching theme
    assert re.search(r"link\.integrity\s*=\s*['\"]", src), \
        "_setResolvedTheme should clear link.integrity on theme switch"
