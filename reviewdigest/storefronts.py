"""App Store storefront country codes.

ISO 3166-1 alpha-2 codes for territories with an App Store storefront.
Used to validate config and to expand `countries: all`.
"""

# Major storefronts by App Store revenue/volume — used when `countries: all`
# would be overkill isn't set; also the recommended starter set in the README.
MAJOR = [
    "us", "cn", "jp", "gb", "kr", "de", "fr", "ca", "au", "tw",
    "it", "es", "br", "mx", "ru", "nl", "ch", "se", "hk", "sg",
]

# Full storefront list (App Store territories).
ALL = sorted(set(MAJOR + [
    "ae", "ag", "ai", "al", "am", "ao", "ar", "at", "az",
    "ba", "bb", "be", "bf", "bg", "bh", "bj", "bm", "bn", "bo",
    "bs", "bt", "bw", "by", "bz",
    "cg", "ci", "cl", "cm", "co", "cr", "cv", "cy", "cz",
    "de", "dk", "dm", "do", "dz",
    "ec", "ee", "eg",
    "fi", "fj", "fm",
    "ga", "gd", "ge", "gh", "gm", "gr", "gt", "gw", "gy",
    "hn", "hr", "hu",
    "id", "ie", "il", "in", "iq", "is",
    "jm", "jo",
    "ke", "kg", "kh", "kn", "kw", "ky", "kz",
    "la", "lb", "lc", "lk", "lr", "lt", "lu", "lv", "ly",
    "ma", "md", "me", "mg", "mk", "ml", "mm", "mn", "mo", "mr",
    "ms", "mt", "mu", "mv", "mw", "my", "mz",
    "na", "ne", "ng", "ni", "no", "np", "nz",
    "om",
    "pa", "pe", "pg", "ph", "pk", "pl", "pt", "py",
    "qa",
    "ro", "rs", "rw",
    "sa", "sb", "sc", "si", "sk", "sl", "sn", "sr", "st", "sv", "sz",
    "tc", "td", "th", "tj", "tm", "tn", "to", "tr", "tt", "tz",
    "ua", "ug", "uy", "uz",
    "vc", "ve", "vg", "vn", "vu",
    "xk",
    "ye",
    "za", "zm", "zw",
]))


def expand(countries) -> list[str]:
    """Expand the config `countries` value into a validated list of codes."""
    if countries in ("all", ["all"]):
        return list(ALL)
    if countries in ("major", ["major"]):
        return list(MAJOR)
    if not isinstance(countries, list):
        raise ValueError(
            f"`countries` must be a list of storefront codes, 'major', or 'all' — got {countries!r}"
        )
    result = []
    for c in countries:
        code = str(c).strip().lower()
        if code not in ALL:
            raise ValueError(
                f"Unknown App Store storefront code {code!r}. "
                f"Use ISO country codes like 'us', 'jp', 'de' (see reviewdigest/storefronts.py)."
            )
        result.append(code)
    if not result:
        raise ValueError("`countries` is empty — add at least one storefront code, e.g. [us].")
    return result
