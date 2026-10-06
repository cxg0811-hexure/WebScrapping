# Generated with GitHub Copilot - [Tracking ID: Hexure-Copilot]
"""Heuristics that keep genuine iPhone / Samsung Galaxy phones and drop accessories."""
import re

CATEGORIES = ("iPhone", "Samsung")

# Category -> (title prefix required, extra keyword required)
_BRAND_RULES = {
    "iPhone": ("apple", "iphone"),
    "Samsung": ("samsung", "galaxy"),
}

EXCLUDE_PATTERNS = re.compile(
    r"(?<!charging )(?<!magsafe )(?<!wireless )\bcase\b|\b(cover|tempered|screen guard|screen protector|"
    r"protector|skin|sleeve|pouch|compatible|holder|charger|adapter|cable|stand|tablet|tab|watch|buds|"
    r"ring|book|fit|band|earbuds|earphones|headphones|refurbished|renewed|pre-owned|unboxed|"
    r"for (?:apple|iphone|samsung|galaxy|pixel))\b|magsafe battery|battery pack|power bank|extended warranty|warranty plan|applecare|protect\+",
    re.IGNORECASE,
)
_INVISIBLE = re.compile(r"[\u200b-\u200f\u2060\ufeff]")


def clean(title: str) -> str:
    return re.sub(r"\s+", " ", _INVISIBLE.sub("", title)).strip()


def categorize(title: str, default: str = "") -> str:
    t = clean(title).lower()
    for category, (prefix, keyword) in _BRAND_RULES.items():
        if t.startswith(prefix) and keyword in t:
            return category
    return default


def is_target_phone(title: str) -> bool:
    t = clean(title).lower()
    if not categorize(t):
        return False
    return not EXCLUDE_PATTERNS.search(t)


def normalize_name(title: str) -> str:
    """Trim long marketing titles to a compact product name, always prefixed with the brand."""
    title = clean(title)
    for sep in (" | ", ": "):
        if sep in title and title.index(sep) > 8:
            title = title.split(sep)[0]
    return title.strip(" ,-")
