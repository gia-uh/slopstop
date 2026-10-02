from slopstop import register, tells


def test_shipped_register_loads_and_covers_the_catalog():
    reg = register.load("apiad-blog-en")
    assert reg["lang"] == "en" and reg["texts"] > 100
    assert set(reg["tells"]) == set(tells.CATALOG)
    assert reg["false_positive_rate"] is not None
    assert 90 <= reg["tells"]["long-paragraph"]["p99"] <= 140
