"""GDELT Project collector - Global Database of Events, Language, and Tone.

GDELT monitors news from virtually every country in nearly every language,
providing one of the most comprehensive free datasets of global news.
"""

import httpx
import csv
import io
import zipfile
from typing import List, Optional
from datetime import datetime, timedelta

from app.collectors.base import BaseCollector, CollectedArticle
from app.utils.geo import get_country_code
from app.utils.logging import get_logger

logger = get_logger(__name__)

# GDELT GKG (Global Knowledge Graph) export URLs
GDELT_GKG_URL = "http://data.gdeltproject.org/gdeltv2/lastupdate.txt"
GDELT_EVENTS_URL = "http://data.gdeltproject.org/gdeltv2/lastupdate.txt"

# GDELT DOC API (free, no auth needed)
GDELT_DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"

# Country codes GDELT uses (FIPS to ISO mapping for common ones)
FIPS_TO_ISO = {
    "US": "US",
    "UK": "GB",
    "FR": "FR",
    "GM": "DE",
    "IT": "IT",
    "SP": "ES",
    "PO": "PT",
    "NL": "NL",
    "BE": "BE",
    "AU": "AT",
    "SZ": "CH",
    "SW": "SE",
    "NO": "NO",
    "DA": "DK",
    "FI": "FI",
    "PL": "PL",
    "EZ": "CZ",
    "HU": "HU",
    "RO": "RO",
    "BU": "BG",
    "GR": "GR",
    "TU": "TR",
    "RS": "RU",
    "UP": "UA",
    "BO": "BY",
    "LH": "LT",
    "LG": "LV",
    "EN": "EE",
    "JA": "JP",
    "KS": "KR",
    "CH": "CN",
    "TW": "TW",
    "HK": "HK",
    "IN": "IN",
    "PK": "PK",
    "BG": "BD",
    "CE": "LK",
    "NP": "NP",
    "AF": "AF",
    "IR": "IR",
    "IZ": "IQ",
    "IS": "IL",
    "JO": "JO",
    "LE": "LB",
    "SY": "SY",
    "SA": "SA",
    "AE": "AE",
    "QA": "QA",
    "KU": "KW",
    "BA": "BH",
    "MU": "OM",
    "YM": "YE",
    "EG": "EG",
    "LY": "LY",
    "AG": "DZ",
    "MO": "MA",
    "TS": "TN",
    "SF": "ZA",
    "NI": "NG",
    "KE": "KE",
    "ET": "ET",
    "GH": "GH",
    "TZ": "TZ",
    "UG": "UG",
    "ZI": "ZW",
    "ZA": "ZM",
    "AO": "AO",
    "MZ": "MZ",
    "CG": "CD",
    "CF": "CG",
    "RW": "RW",
    "SU": "SD",
    "SO": "SO",
    "SN": "SN",
    "IV": "CI",
    "CM": "CM",
    "BR": "BR",
    "AR": "AR",
    "CI": "CL",
    "CO": "CO",
    "PE": "PE",
    "VE": "VE",
    "EC": "EC",
    "BL": "BO",
    "UY": "UY",
    "PA": "PY",
    "MX": "MX",
    "GT": "GT",
    "HO": "HN",
    "ES": "SV",
    "NU": "NI",
    "CS": "CR",
    "PM": "PA",
    "CU": "CU",
    "DR": "DO",
    "HA": "HT",
    "JM": "JM",
    "TD": "TT",
    "AS": "AU",
    "NZ": "NZ",
    "FJ": "FJ",
    "PP": "PG",
    "ID": "ID",
    "MY": "MY",
    "SN": "SG",
    "TH": "TH",
    "VM": "VN",
    "RP": "PH",
    "BM": "MM",
    "CB": "KH",
    "LA": "LA",
    "BN": "BN",
    "MG": "MN",
    "KZ": "KZ",
    "UZ": "UZ",
    "TX": "TM",
    "TI": "TJ",
    "KG": "KG",
    "GG": "GE",
    "AM": "AM",
    "AJ": "AZ",
    "CA": "CA",
    "EI": "IE",
    "IC": "IS",
}


class GDELTCollector(BaseCollector):
    """Collector for GDELT Project news data."""

    source_type = "gdelt"

    def __init__(self, timeout: float = 60.0):
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    def is_configured(self) -> bool:
        """GDELT is free and doesn't require configuration."""
        return True

    async def collect(self) -> List[CollectedArticle]:
        """Collect recent articles from GDELT DOC API."""
        articles = []

        # Query different themes/topics for broader coverage
        queries = [
            {"query": "sourcecountry:US", "mode": "artlist"},
            {"query": "sourcecountry:UK", "mode": "artlist"},
            {"query": "sourcecountry:IN", "mode": "artlist"},
            {"query": "sourcecountry:BR", "mode": "artlist"},
            {"query": "sourcecountry:JP", "mode": "artlist"},
            {"query": "sourcecountry:DE", "mode": "artlist"},
            {"query": "sourcecountry:FR", "mode": "artlist"},
            {"query": "sourcecountry:RU", "mode": "artlist"},
            {"query": "sourcecountry:CN", "mode": "artlist"},
            {"query": "sourcecountry:AU", "mode": "artlist"},
            {"query": "sourcecountry:CA", "mode": "artlist"},
            {"query": "sourcecountry:ZA", "mode": "artlist"},
            {"query": "sourcecountry:NG", "mode": "artlist"},
            {"query": "sourcecountry:EG", "mode": "artlist"},
            {"query": "sourcecountry:SA", "mode": "artlist"},
            {"query": "sourcecountry:AE", "mode": "artlist"},
            {"query": "sourcecountry:IL", "mode": "artlist"},
            {"query": "sourcecountry:TR", "mode": "artlist"},
            {"query": "sourcecountry:ID", "mode": "artlist"},
            {"query": "sourcecountry:MX", "mode": "artlist"},
            {"query": "sourcecountry:AR", "mode": "artlist"},
            {"query": "sourcecountry:PK", "mode": "artlist"},
            {"query": "sourcecountry:KR", "mode": "artlist"},
            {"query": "sourcecountry:PL", "mode": "artlist"},
            {"query": "sourcecountry:UA", "mode": "artlist"},
            {"query": "sourcecountry:NL", "mode": "artlist"},
            {"query": "sourcecountry:SE", "mode": "artlist"},
            {"query": "sourcecountry:ES", "mode": "artlist"},
            {"query": "sourcecountry:IT", "mode": "artlist"},
            {"query": "sourcecountry:TH", "mode": "artlist"},
            {"query": "sourcecountry:MY", "mode": "artlist"},
            {"query": "sourcecountry:SG", "mode": "artlist"},
            {"query": "sourcecountry:PH", "mode": "artlist"},
            {"query": "sourcecountry:VN", "mode": "artlist"},
            {"query": "sourcecountry:KE", "mode": "artlist"},
            {"query": "sourcecountry:GH", "mode": "artlist"},
            {"query": "sourcecountry:CO", "mode": "artlist"},
            {"query": "sourcecountry:CL", "mode": "artlist"},
            {"query": "sourcecountry:PE", "mode": "artlist"},
            {"query": "sourcecountry:BD", "mode": "artlist"},
        ]

        for query_params in queries:
            try:
                query_articles = await self._fetch_articles(query_params)
                articles.extend(query_articles)
            except Exception as e:
                logger.debug(
                    "Failed to fetch GDELT query",
                    query=query_params.get("query"),
                    error=str(e),
                )

        logger.info("Fetched GDELT articles", count=len(articles))
        return articles

    async def _fetch_articles(self, params: dict) -> List[CollectedArticle]:
        """Fetch articles from GDELT DOC API."""
        articles = []

        # Set time range to last 24 hours
        now = datetime.utcnow()
        start = now - timedelta(hours=24)

        api_params = {
            "query": params.get("query", ""),
            "mode": params.get("mode", "artlist"),
            "maxrecords": 75,
            "format": "json",
            "startdatetime": start.strftime("%Y%m%d%H%M%S"),
            "enddatetime": now.strftime("%Y%m%d%H%M%S"),
            "sort": "datedesc",
        }

        try:
            response = await self.client.get(GDELT_DOC_API, params=api_params)
            response.raise_for_status()

            data = response.json()

            if "articles" in data:
                for article_data in data["articles"]:
                    article = self._parse_article(article_data)
                    if article:
                        articles.append(article)

        except Exception as e:
            raise Exception(f"GDELT API error: {e}")

        return articles

    def _parse_article(self, data: dict) -> Optional[CollectedArticle]:
        """Parse a GDELT article into a CollectedArticle."""
        try:
            url = data.get("url")
            title = data.get("title")

            if not url or not title:
                return None

            # Get country from source country or detect
            country_code = None
            source_country = data.get("sourcecountry")
            if source_country and source_country in FIPS_TO_ISO:
                country_code = FIPS_TO_ISO[source_country]
            elif source_country:
                country_code = get_country_code(source_country)

            # Parse date
            published_at = None
            seendate = data.get("seendate")
            if seendate:
                try:
                    published_at = datetime.strptime(seendate, "%Y%m%dT%H%M%SZ")
                except (ValueError, TypeError):
                    pass

            # Get domain as source name
            domain = data.get("domain", "GDELT")

            return CollectedArticle(
                source_type=self.source_type,
                source_name=domain,
                title=title,
                url=url,
                content=data.get("excerpt"),
                country_code=country_code,
                published_at=published_at,
            )

        except Exception as e:
            logger.debug("Failed to parse GDELT article", error=str(e))
            return None

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
