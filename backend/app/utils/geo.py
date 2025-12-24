"""Geographic utilities for country detection."""

import pycountry
from typing import Optional
import re

# Common country name variations and their ISO codes
COUNTRY_ALIASES = {
    # Variations
    "usa": "US",
    "united states": "US",
    "united states of america": "US",
    "america": "US",
    "uk": "GB",
    "united kingdom": "GB",
    "britain": "GB",
    "great britain": "GB",
    "england": "GB",  # Not technically correct but commonly used
    "russia": "RU",
    "russian federation": "RU",
    "south korea": "KR",
    "korea": "KR",
    "north korea": "KP",
    "china": "CN",
    "peoples republic of china": "CN",
    "taiwan": "TW",
    "hong kong": "HK",
    "uae": "AE",
    "united arab emirates": "AE",
    "vietnam": "VN",
    "viet nam": "VN",
    "iran": "IR",
    "syria": "SY",
    "czech republic": "CZ",
    "czechia": "CZ",
    "netherlands": "NL",
    "holland": "NL",
}

# Subreddit to country mapping
SUBREDDIT_COUNTRIES = {
    "unitedkingdom": "GB",
    "ukpolitics": "GB",
    "casualuk": "GB",
    "france": "FR",
    "germany": "DE",
    "de": "DE",
    "india": "IN",
    "australia": "AU",
    "canada": "CA",
    "europe": "EU",  # Special case
    "japan": "JP",
    "korea": "KR",
    "china": "CN",
    "russia": "RU",
    "brazil": "BR",
    "mexico": "MX",
    "spain": "ES",
    "italy": "IT",
    "netherlands": "NL",
    "sweden": "SE",
    "norway": "NO",
    "denmark": "DK",
    "finland": "FI",
    "poland": "PL",
    "ukraine": "UA",
    "ireland": "IE",
    "newzealand": "NZ",
    "singapore": "SG",
    "philippines": "PH",
    "indonesia": "ID",
    "malaysia": "MY",
    "thailand": "TH",
    "vietnam": "VN",
    "southafrica": "ZA",
    "israel": "IL",
    "turkey": "TR",
    "egypt": "EG",
    "nigeria": "NG",
    "kenya": "KE",
    "argentina": "AR",
    "chile": "CL",
    "colombia": "CO",
    "peru": "PE",
    "worldnews": None,  # Global
    "news": "US",  # Default to US
    "politics": "US",
}

# News source to country mapping
SOURCE_COUNTRIES = {
    "bbc": "GB",
    "bbc news": "GB",
    "the guardian": "GB",
    "reuters": None,  # International
    "associated press": None,
    "ap news": None,
    "cnn": "US",
    "fox news": "US",
    "nbc news": "US",
    "abc news": "US",
    "new york times": "US",
    "washington post": "US",
    "wall street journal": "US",
    "al jazeera": "QA",
    "france 24": "FR",
    "le monde": "FR",
    "der spiegel": "DE",
    "deutsche welle": "DE",
    "times of india": "IN",
    "hindustan times": "IN",
    "ndtv": "IN",
    "south china morning post": "HK",
    "china daily": "CN",
    "nhk": "JP",
    "japan times": "JP",
    "abc australia": "AU",
    "sydney morning herald": "AU",
    "cbc": "CA",
    "globe and mail": "CA",
    "rt": "RU",  # Russia Today
}


def normalize_country_name(name: str) -> str:
    """Normalize country name for lookup."""
    return re.sub(r'[^a-z\s]', '', name.lower().strip())


def get_country_code(name: str) -> Optional[str]:
    """Get ISO 3166-1 alpha-2 country code from name."""
    if not name:
        return None
    
    normalized = normalize_country_name(name)
    
    # Check aliases first
    if normalized in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[normalized]
    
    # Try pycountry lookup
    try:
        country = pycountry.countries.lookup(name)
        return country.alpha_2
    except LookupError:
        pass
    
    # Try fuzzy search
    try:
        results = pycountry.countries.search_fuzzy(name)
        if results:
            return results[0].alpha_2
    except LookupError:
        pass
    
    return None


def get_country_name(code: str) -> str:
    """Get country name from ISO code."""
    if not code:
        return "Unknown"
    
    try:
        country = pycountry.countries.get(alpha_2=code.upper())
        if country:
            return country.name
    except (LookupError, AttributeError):
        pass
    
    return code.upper()


def get_country_from_subreddit(subreddit: str) -> Optional[str]:
    """Get country code from subreddit name."""
    normalized = subreddit.lower().replace("r/", "").strip()
    return SUBREDDIT_COUNTRIES.get(normalized)


def get_country_from_source(source_name: str) -> Optional[str]:
    """Get country code from news source name."""
    normalized = source_name.lower().strip()
    
    # Direct lookup
    if normalized in SOURCE_COUNTRIES:
        return SOURCE_COUNTRIES[normalized]
    
    # Partial match
    for source, code in SOURCE_COUNTRIES.items():
        if source in normalized or normalized in source:
            return code
    
    return None


def detect_country_from_text(text: str) -> Optional[str]:
    """Attempt to detect country from article text (basic implementation)."""
    if not text:
        return None
    
    text_lower = text.lower()
    
    # Check for country mentions (simple approach)
    for alias, code in COUNTRY_ALIASES.items():
        if alias in text_lower:
            return code
    
    return None


def get_all_country_codes() -> list[str]:
    """Get list of all valid ISO country codes."""
    return [country.alpha_2 for country in pycountry.countries]

