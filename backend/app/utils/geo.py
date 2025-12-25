"""Geographic utilities for country detection."""

import pycountry
from typing import Optional, List, Tuple
import re

# Common country name variations and their ISO codes
COUNTRY_ALIASES = {
    # Variations
    "usa": "US",
    "u.s.": "US",
    "u.s.a.": "US",
    "united states": "US",
    "united states of america": "US",
    "america": "US",
    "american": "US",
    "washington": "US",  # DC context
    "uk": "GB",
    "u.k.": "GB",
    "united kingdom": "GB",
    "britain": "GB",
    "british": "GB",
    "great britain": "GB",
    "england": "GB",
    "scotland": "GB",
    "wales": "GB",
    "london": "GB",
    "russia": "RU",
    "russian": "RU",
    "russian federation": "RU",
    "moscow": "RU",
    "kremlin": "RU",
    "south korea": "KR",
    "korea": "KR",
    "korean": "KR",
    "seoul": "KR",
    "north korea": "KP",
    "pyongyang": "KP",
    "china": "CN",
    "chinese": "CN",
    "beijing": "CN",
    "peoples republic of china": "CN",
    "taiwan": "TW",
    "taiwanese": "TW",
    "taipei": "TW",
    "hong kong": "HK",
    "uae": "AE",
    "united arab emirates": "AE",
    "dubai": "AE",
    "abu dhabi": "AE",
    "vietnam": "VN",
    "vietnamese": "VN",
    "viet nam": "VN",
    "hanoi": "VN",
    "iran": "IR",
    "iranian": "IR",
    "tehran": "IR",
    "syria": "SY",
    "syrian": "SY",
    "damascus": "SY",
    "czech republic": "CZ",
    "czechia": "CZ",
    "prague": "CZ",
    "netherlands": "NL",
    "dutch": "NL",
    "holland": "NL",
    "amsterdam": "NL",
    "germany": "DE",
    "german": "DE",
    "berlin": "DE",
    "france": "FR",
    "french": "FR",
    "paris": "FR",
    "italy": "IT",
    "italian": "IT",
    "rome": "IT",
    "spain": "ES",
    "spanish": "ES",
    "madrid": "ES",
    "barcelona": "ES",
    "portugal": "PT",
    "portuguese": "PT",
    "lisbon": "PT",
    "poland": "PL",
    "polish": "PL",
    "warsaw": "PL",
    "ukraine": "UA",
    "ukrainian": "UA",
    "kyiv": "UA",
    "kiev": "UA",
    "zelenskyy": "UA",
    "zelensky": "UA",
    "japan": "JP",
    "japanese": "JP",
    "tokyo": "JP",
    "india": "IN",
    "indian": "IN",
    "delhi": "IN",
    "mumbai": "IN",
    "australia": "AU",
    "australian": "AU",
    "sydney": "AU",
    "melbourne": "AU",
    "canberra": "AU",
    "canada": "CA",
    "canadian": "CA",
    "ottawa": "CA",
    "toronto": "CA",
    "brazil": "BR",
    "brazilian": "BR",
    "brasilia": "BR",
    "sao paulo": "BR",
    "mexico": "MX",
    "mexican": "MX",
    "mexico city": "MX",
    "argentina": "AR",
    "argentine": "AR",
    "buenos aires": "AR",
    "chile": "CL",
    "chilean": "CL",
    "santiago": "CL",
    "colombia": "CO",
    "colombian": "CO",
    "bogota": "CO",
    "peru": "PE",
    "peruvian": "PE",
    "lima": "PE",
    "venezuela": "VE",
    "venezuelan": "VE",
    "caracas": "VE",
    "egypt": "EG",
    "egyptian": "EG",
    "cairo": "EG",
    "south africa": "ZA",
    "south african": "ZA",
    "johannesburg": "ZA",
    "pretoria": "ZA",
    "cape town": "ZA",
    "nigeria": "NG",
    "nigerian": "NG",
    "lagos": "NG",
    "kenya": "KE",
    "kenyan": "KE",
    "nairobi": "KE",
    "morocco": "MA",
    "moroccan": "MA",
    "rabat": "MA",
    "algeria": "DZ",
    "algerian": "DZ",
    "algiers": "DZ",
    "ethiopia": "ET",
    "ethiopian": "ET",
    "addis ababa": "ET",
    "ghana": "GH",
    "ghanaian": "GH",
    "accra": "GH",
    "tanzania": "TZ",
    "tanzanian": "TZ",
    "dar es salaam": "TZ",
    "uganda": "UG",
    "ugandan": "UG",
    "kampala": "UG",
    "turkey": "TR",
    "turkish": "TR",
    "ankara": "TR",
    "istanbul": "TR",
    "israel": "IL",
    "israeli": "IL",
    "tel aviv": "IL",
    "jerusalem": "IL",
    "palestine": "PS",
    "palestinian": "PS",
    "gaza": "PS",
    "west bank": "PS",
    "saudi arabia": "SA",
    "saudi": "SA",
    "riyadh": "SA",
    "iraq": "IQ",
    "iraqi": "IQ",
    "baghdad": "IQ",
    "lebanon": "LB",
    "lebanese": "LB",
    "beirut": "LB",
    "jordan": "JO",
    "jordanian": "JO",
    "amman": "JO",
    "qatar": "QA",
    "qatari": "QA",
    "doha": "QA",
    "kuwait": "KW",
    "kuwaiti": "KW",
    "bahrain": "BH",
    "bahraini": "BH",
    "oman": "OM",
    "omani": "OM",
    "muscat": "OM",
    "yemen": "YE",
    "yemeni": "YE",
    "sanaa": "YE",
    "afghanistan": "AF",
    "afghan": "AF",
    "kabul": "AF",
    "pakistan": "PK",
    "pakistani": "PK",
    "islamabad": "PK",
    "karachi": "PK",
    "bangladesh": "BD",
    "bangladeshi": "BD",
    "dhaka": "BD",
    "sri lanka": "LK",
    "sri lankan": "LK",
    "colombo": "LK",
    "nepal": "NP",
    "nepalese": "NP",
    "kathmandu": "NP",
    "myanmar": "MM",
    "burmese": "MM",
    "yangon": "MM",
    "thailand": "TH",
    "thai": "TH",
    "bangkok": "TH",
    "indonesia": "ID",
    "indonesian": "ID",
    "jakarta": "ID",
    "malaysia": "MY",
    "malaysian": "MY",
    "kuala lumpur": "MY",
    "singapore": "SG",
    "singaporean": "SG",
    "philippines": "PH",
    "filipino": "PH",
    "manila": "PH",
    "new zealand": "NZ",
    "kiwi": "NZ",
    "wellington": "NZ",
    "auckland": "NZ",
    "ireland": "IE",
    "irish": "IE",
    "dublin": "IE",
    "sweden": "SE",
    "swedish": "SE",
    "stockholm": "SE",
    "norway": "NO",
    "norwegian": "NO",
    "oslo": "NO",
    "denmark": "DK",
    "danish": "DK",
    "copenhagen": "DK",
    "finland": "FI",
    "finnish": "FI",
    "helsinki": "FI",
    "iceland": "IS",
    "icelandic": "IS",
    "reykjavik": "IS",
    "belgium": "BE",
    "belgian": "BE",
    "brussels": "BE",
    "austria": "AT",
    "austrian": "AT",
    "vienna": "AT",
    "switzerland": "CH",
    "swiss": "CH",
    "geneva": "CH",
    "zurich": "CH",
    "bern": "CH",
    "greece": "GR",
    "greek": "GR",
    "athens": "GR",
    "romania": "RO",
    "romanian": "RO",
    "bucharest": "RO",
    "bulgaria": "BG",
    "bulgarian": "BG",
    "sofia": "BG",
    "hungary": "HU",
    "hungarian": "HU",
    "budapest": "HU",
    "serbia": "RS",
    "serbian": "RS",
    "belgrade": "RS",
    "croatia": "HR",
    "croatian": "HR",
    "zagreb": "HR",
    "slovenia": "SI",
    "slovenian": "SI",
    "ljubljana": "SI",
    "slovakia": "SK",
    "slovak": "SK",
    "bratislava": "SK",
    "lithuania": "LT",
    "lithuanian": "LT",
    "vilnius": "LT",
    "latvia": "LV",
    "latvian": "LV",
    "riga": "LV",
    "estonia": "EE",
    "estonian": "EE",
    "tallinn": "EE",
    "belarus": "BY",
    "belarusian": "BY",
    "minsk": "BY",
    "moldova": "MD",
    "moldovan": "MD",
    "chisinau": "MD",
    "georgia": "GE",  # Country context
    "georgian": "GE",
    "tbilisi": "GE",
    "armenia": "AM",
    "armenian": "AM",
    "yerevan": "AM",
    "azerbaijan": "AZ",
    "azerbaijani": "AZ",
    "baku": "AZ",
    "kazakhstan": "KZ",
    "kazakh": "KZ",
    "astana": "KZ",
    "nur-sultan": "KZ",
    "uzbekistan": "UZ",
    "uzbek": "UZ",
    "tashkent": "UZ",
    "cuba": "CU",
    "cuban": "CU",
    "havana": "CU",
    "ecuador": "EC",
    "ecuadorian": "EC",
    "quito": "EC",
    "bolivia": "BO",
    "bolivian": "BO",
    "la paz": "BO",
    "paraguay": "PY",
    "paraguayan": "PY",
    "asuncion": "PY",
    "uruguay": "UY",
    "uruguayan": "UY",
    "montevideo": "UY",
    "costa rica": "CR",
    "costa rican": "CR",
    "san jose": "CR",
    "panama": "PA",
    "panamanian": "PA",
    "guatemala": "GT",
    "guatemalan": "GT",
    "honduras": "HN",
    "honduran": "HN",
    "el salvador": "SV",
    "salvadoran": "SV",
    "nicaragua": "NI",
    "nicaraguan": "NI",
    "dominican republic": "DO",
    "dominican": "DO",
    "puerto rico": "PR",
    "puerto rican": "PR",
    "haiti": "HT",
    "haitian": "HT",
    "jamaica": "JM",
    "jamaican": "JM",
    "trinidad": "TT",
    "tobago": "TT",
    "libya": "LY",
    "libyan": "LY",
    "tripoli": "LY",
    "tunisia": "TN",
    "tunisian": "TN",
    "tunis": "TN",
    "sudan": "SD",
    "sudanese": "SD",
    "khartoum": "SD",
    "zimbabwe": "ZW",
    "zimbabwean": "ZW",
    "harare": "ZW",
    "zambia": "ZM",
    "zambian": "ZM",
    "lusaka": "ZM",
    "mozambique": "MZ",
    "mozambican": "MZ",
    "maputo": "MZ",
    "angola": "AO",
    "angolan": "AO",
    "luanda": "AO",
    "cameroon": "CM",
    "cameroonian": "CM",
    "yaounde": "CM",
    "ivory coast": "CI",
    "cote divoire": "CI",
    "abidjan": "CI",
    "senegal": "SN",
    "senegalese": "SN",
    "dakar": "SN",
    "democratic republic of congo": "CD",
    "drc": "CD",
    "kinshasa": "CD",
    "republic of congo": "CG",
    "brazzaville": "CG",
    "rwanda": "RW",
    "rwandan": "RW",
    "kigali": "RW",
    "somalia": "SO",
    "somali": "SO",
    "mogadishu": "SO",
    "madagascar": "MG",
    "malagasy": "MG",
    "antananarivo": "MG",
    "botswana": "BW",
    "botswanan": "BW",
    "gaborone": "BW",
    "namibia": "NA",
    "namibian": "NA",
    "windhoek": "NA",
    "mauritius": "MU",
    "mauritian": "MU",
    "mongolia": "MN",
    "mongolian": "MN",
    "ulaanbaatar": "MN",
    "cambodia": "KH",
    "cambodian": "KH",
    "phnom penh": "KH",
    "laos": "LA",
    "laotian": "LA",
    "vientiane": "LA",
    "brunei": "BN",
    "bruneian": "BN",
    "fiji": "FJ",
    "fijian": "FJ",
    "papua new guinea": "PG",
    "maldives": "MV",
    "maldivian": "MV",
    "male": "MV",
    "bhutan": "BT",
    "bhutanese": "BT",
    "thimphu": "BT",
    "luxembourg": "LU",
    "luxembourgish": "LU",
    "malta": "MT",
    "maltese": "MT",
    "valletta": "MT",
    "cyprus": "CY",
    "cypriot": "CY",
    "nicosia": "CY",
    "montenegro": "ME",
    "montenegrin": "ME",
    "podgorica": "ME",
    "north macedonia": "MK",
    "macedonian": "MK",
    "skopje": "MK",
    "albania": "AL",
    "albanian": "AL",
    "tirana": "AL",
    "bosnia": "BA",
    "bosnian": "BA",
    "sarajevo": "BA",
    "kosovo": "XK",
    "kosovar": "XK",
    "pristina": "XK",
}

# Subreddit to country mapping
SUBREDDIT_COUNTRIES = {
    "unitedkingdom": "GB",
    "ukpolitics": "GB",
    "casualuk": "GB",
    "london": "GB",
    "scotland": "GB",
    "france": "FR",
    "germany": "DE",
    "de": "DE",
    "india": "IN",
    "indiaspeaks": "IN",
    "australia": "AU",
    "canada": "CA",
    "onguardforthee": "CA",
    "europe": None,  # Multi-country
    "japan": "JP",
    "korea": "KR",
    "hanguk": "KR",
    "china": "CN",
    "sino": "CN",
    "russia": "RU",
    "brazil": "BR",
    "brasil": "BR",
    "mexico": "MX",
    "spain": "ES",
    "es": "ES",
    "italy": "IT",
    "netherlands": "NL",
    "thenetherlands": "NL",
    "sweden": "SE",
    "norway": "NO",
    "norge": "NO",
    "denmark": "DK",
    "finland": "FI",
    "suomi": "FI",
    "poland": "PL",
    "polska": "PL",
    "ukraine": "UA",
    "ukraina": "UA",
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
    "venezuela": "VE",
    "pakistan": "PK",
    "bangladesh": "BD",
    "srilanka": "LK",
    "nepal": "NP",
    "iran": "IR",
    "saudiarabia": "SA",
    "iraq": "IQ",
    "lebanon": "LB",
    "jordan": "JO",
    "morocco": "MA",
    "algeria": "DZ",
    "tunisia": "TN",
    "greece": "GR",
    "romania": "RO",
    "hungary": "HU",
    "czech": "CZ",
    "austria": "AT",
    "switzerland": "CH",
    "belgium": "BE",
    "portugal": "PT",
    "croatia": "HR",
    "serbia": "RS",
    "bulgaria": "BG",
    "ukraine": "UA",
    "worldnews": None,  # Global
    "news": "US",  # Default to US
    "politics": "US",
    "usanews": "US",
    "conservative": "US",
    "democrats": "US",
    "liberal": "US",
}

# News source to country mapping
SOURCE_COUNTRIES = {
    "bbc": "GB",
    "bbc news": "GB",
    "the guardian": "GB",
    "sky news": "GB",
    "the telegraph": "GB",
    "the independent": "GB",
    "daily mail": "GB",
    "reuters": None,  # International
    "reuters world": None,
    "associated press": None,
    "ap news": None,
    "afp": None,
    "euronews": None,  # International
    "allafrica": None,  # International
    "cnn": "US",
    "fox news": "US",
    "nbc news": "US",
    "abc news": "US",
    "cbs news": "US",
    "npr": "US",
    "npr news": "US",
    "pbs": "US",
    "pbs newshour": "US",
    "new york times": "US",
    "washington post": "US",
    "wall street journal": "US",
    "usa today": "US",
    "los angeles times": "US",
    "chicago tribune": "US",
    "al jazeera": "QA",
    "france 24": "FR",
    "le monde": "FR",
    "le figaro": "FR",
    "der spiegel": "DE",
    "deutsche welle": "DE",
    "dw": "DE",
    "tagesschau": "DE",
    "ard": "DE",
    "zdf": "DE",
    "times of india": "IN",
    "hindustan times": "IN",
    "ndtv": "IN",
    "the hindu": "IN",
    "indian express": "IN",
    "south china morning post": "HK",
    "china daily": "CN",
    "xinhua": "CN",
    "cgtn": "CN",
    "nhk": "JP",
    "nhk world": "JP",
    "japan times": "JP",
    "abc australia": "AU",
    "abc news australia": "AU",
    "sydney morning herald": "AU",
    "the age": "AU",
    "cbc": "CA",
    "cbc news": "CA",
    "globe and mail": "CA",
    "toronto star": "CA",
    "rt": "RU",
    "tass": "RU",
    "ria novosti": "RU",
    "cna": "SG",
    "channel newsasia": "SG",
    "straits times": "SG",
    "yonhap": "KR",
    "korea herald": "KR",
    "korea times": "KR",
    "taipei times": "TW",
    "focus taiwan": "TW",
    "ansa": "IT",
    "la repubblica": "IT",
    "el pais": "ES",
    "el mundo": "ES",
    "rtve": "ES",
    "nos": "NL",
    "de telegraaf": "NL",
    "aftonbladet": "SE",
    "svt": "SE",
    "nrk": "NO",
    "vg": "NO",
    "dr": "DK",
    "yle": "FI",
    "rte": "IE",
    "irish times": "IE",
    "tvn24": "PL",
    "gazeta wyborcza": "PL",
    "ukrinform": "UA",
    "kyiv independent": "UA",
    "pravda": "UA",
    "globo": "BR",
    "folha": "BR",
    "televisa": "MX",
    "milenio": "MX",
    "el universal": "MX",
    "clarin": "AR",
    "la nacion": "AR",
    "el mercurio": "CL",
    "el comercio": "PE",
    "orf": "AT",
    "srf": "CH",
    "swissinfo": "CH",
    "rtbf": "BE",
    "vrt": "BE",
    "rtp": "PT",
    "ekathimerini": "GR",
    "digi24": "RO",
    "index.hu": "HU",
    "radio prague": "CZ",
    "aktualne": "CZ",
    "n1": "RS",
    "hrt": "HR",
    "nova tv": "BG",
    "lrt": "LT",
    "lsm": "LV",
    "err": "EE",
    "tut.by": "BY",
    "arabnews": "SA",
    "gulf news": "AE",
    "khaleej times": "AE",
    "daily star lebanon": "LB",
    "jordan times": "JO",
    "egypt independent": "EG",
    "ahram": "EG",
    "daily news egypt": "EG",
    "punch": "NG",
    "daily nation": "KE",
    "citizen": "KE",
    "news24": "ZA",
    "iol": "ZA",
    "eyewitness news": "ZA",
    "dawn": "PK",
    "geo": "PK",
    "express tribune": "PK",
    "daily star bd": "BD",
    "bdnews24": "BD",
    "bangkok post": "TH",
    "nation thailand": "TH",
    "jakarta post": "ID",
    "kompas": "ID",
    "vn express": "VN",
    "tuoi tre": "VN",
    "manila bulletin": "PH",
    "inquirer": "PH",
    "the star": "MY",
    "new straits times": "MY",
    "nzherald": "NZ",
    "stuff": "NZ",
    "haaretz": "IL",
    "jerusalem post": "IL",
    "times of israel": "IL",
    "hurriyet": "TR",
    "daily sabah": "TR",
    "tehran times": "IR",
    "press tv": "IR",
}


def normalize_country_name(name: str) -> str:
    """Normalize country name for lookup."""
    return re.sub(r"[^a-z\s]", "", name.lower().strip())


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


def detect_country_from_text(text: str, title: str = None) -> Optional[str]:
    """
    Detect country from article text and title.
    Uses a weighted approach - matches in title are prioritized.
    Returns the most likely country based on mentions.
    """
    if not text and not title:
        return None

    # Combine title (weighted more) and text
    combined = ""
    if title:
        combined += (title.lower() + " ") * 3  # Weight title 3x
    if text:
        combined += text.lower()

    # Count country mentions
    country_counts: dict[str, int] = {}

    # Sort aliases by length (longest first) to match longer phrases first
    sorted_aliases = sorted(
        COUNTRY_ALIASES.items(), key=lambda x: len(x[0]), reverse=True
    )

    for alias, code in sorted_aliases:
        if code is None:
            continue

        # Use word boundaries to avoid partial matches
        # e.g., "german" shouldn't match in "germander"
        pattern = r"\b" + re.escape(alias) + r"\b"
        matches = len(re.findall(pattern, combined, re.IGNORECASE))

        if matches > 0:
            country_counts[code] = country_counts.get(code, 0) + matches

    if not country_counts:
        return None

    # Return the country with most mentions
    return max(country_counts.items(), key=lambda x: x[1])[0]


def extract_all_countries_from_text(
    text: str, title: str = None
) -> List[Tuple[str, int]]:
    """
    Extract all countries mentioned in text with their mention counts.
    Returns list of (country_code, count) tuples sorted by count descending.
    """
    if not text and not title:
        return []

    combined = ""
    if title:
        combined += (title.lower() + " ") * 3
    if text:
        combined += text.lower()

    country_counts: dict[str, int] = {}

    sorted_aliases = sorted(
        COUNTRY_ALIASES.items(), key=lambda x: len(x[0]), reverse=True
    )

    for alias, code in sorted_aliases:
        if code is None:
            continue

        pattern = r"\b" + re.escape(alias) + r"\b"
        matches = len(re.findall(pattern, combined, re.IGNORECASE))

        if matches > 0:
            country_counts[code] = country_counts.get(code, 0) + matches

    return sorted(country_counts.items(), key=lambda x: x[1], reverse=True)


def get_all_country_codes() -> list[str]:
    """Get list of all valid ISO country codes."""
    return [country.alpha_2 for country in pycountry.countries]
