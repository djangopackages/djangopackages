from package.utils import normalize_license, uniquer


def test_uniquer():
    items = ["apple", "apple", "apple", "banana", "cherry"]
    unique_items = ["apple", "banana", "cherry"]
    assert uniquer(items), unique_items


def test_normalize_license():
    assert normalize_license(None) == "UNKNOWN"
    assert (
        normalize_license(
            """License :: OSI Approved :: MIT License
            """
        )
        == "License :: OSI Approved :: MIT License"
    )
    assert normalize_license("Pow" * 80) == "Custom"
    assert normalize_license("MIT") == "MIT"
