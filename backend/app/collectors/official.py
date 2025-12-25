"""Official news sources collector - UN, WHO, World Bank, Government press releases.

Collects news from international organizations and official government sources
for comprehensive global coverage.
"""

import feedparser
import httpx
from typing import List, Optional
from datetime import datetime
from time import mktime

from app.collectors.base import BaseCollector, CollectedArticle
from app.utils.geo import detect_country_from_text
from app.utils.logging import get_logger

logger = get_logger(__name__)


# Official RSS feeds from international organizations and governments
OFFICIAL_FEEDS = [
    # ============================================
    # INTERNATIONAL ORGANIZATIONS
    # ============================================
    # United Nations
    {
        "name": "UN News",
        "url": "https://news.un.org/feed/subscribe/en/news/all/rss.xml",
        "country": None,
    },
    {
        "name": "UN News Africa",
        "url": "https://news.un.org/feed/subscribe/en/news/region/africa/feed/rss.xml",
        "country": None,
    },
    {
        "name": "UN News Americas",
        "url": "https://news.un.org/feed/subscribe/en/news/region/americas/feed/rss.xml",
        "country": None,
    },
    {
        "name": "UN News Asia Pacific",
        "url": "https://news.un.org/feed/subscribe/en/news/region/asia-pacific/feed/rss.xml",
        "country": None,
    },
    {
        "name": "UN News Europe",
        "url": "https://news.un.org/feed/subscribe/en/news/region/europe/feed/rss.xml",
        "country": None,
    },
    {
        "name": "UN News Middle East",
        "url": "https://news.un.org/feed/subscribe/en/news/region/middle-east/feed/rss.xml",
        "country": None,
    },
    {
        "name": "UN Security Council",
        "url": "https://www.un.org/securitycouncil/rss.xml",
        "country": None,
    },
    {"name": "UNHCR", "url": "https://www.unhcr.org/rss/news.xml", "country": None},
    {
        "name": "UNICEF",
        "url": "https://www.unicef.org/press-releases/rss.xml",
        "country": None,
    },
    # World Health Organization
    {
        "name": "WHO News",
        "url": "https://www.who.int/feeds/entity/news/en/rss.xml",
        "country": None,
    },
    {
        "name": "WHO Disease Outbreaks",
        "url": "https://www.who.int/feeds/entity/csr/don/en/rss.xml",
        "country": None,
    },
    # World Bank
    {
        "name": "World Bank",
        "url": "https://www.worldbank.org/en/news/all.rss",
        "country": None,
    },
    {"name": "IMF News", "url": "https://www.imf.org/en/news/rss", "country": None},
    # European Union
    {
        "name": "EU News",
        "url": "https://ec.europa.eu/commission/presscorner/rss/news.xml",
        "country": None,
    },
    {
        "name": "European Parliament",
        "url": "https://www.europarl.europa.eu/rss/en/news.xml",
        "country": None,
    },
    {
        "name": "EU External Action",
        "url": "https://www.eeas.europa.eu/eeas/rss_en",
        "country": None,
    },
    # NATO
    {
        "name": "NATO News",
        "url": "https://www.nato.int/cps/en/natolive/news.xml",
        "country": None,
    },
    # African Union
    {"name": "African Union", "url": "https://au.int/rss.xml", "country": None},
    # ASEAN
    {"name": "ASEAN Secretariat", "url": "https://asean.org/feed/", "country": None},
    # OECD
    {
        "name": "OECD Newsroom",
        "url": "https://www.oecd.org/newsroom/index.xml",
        "country": None,
    },
    # WTO
    {
        "name": "WTO News",
        "url": "https://www.wto.org/english/res_e/news_e/news_e.rss",
        "country": None,
    },
    # Red Cross
    {"name": "ICRC", "url": "https://www.icrc.org/en/rss", "country": None},
    # Amnesty International
    {
        "name": "Amnesty International",
        "url": "https://www.amnesty.org/en/feed/",
        "country": None,
    },
    # Human Rights Watch
    {
        "name": "Human Rights Watch",
        "url": "https://www.hrw.org/rss/news",
        "country": None,
    },
    # ============================================
    # GOVERNMENT SOURCES - NORTH AMERICA
    # ============================================
    # United States
    {"name": "White House", "url": "https://www.whitehouse.gov/feed/", "country": "US"},
    {
        "name": "State Department",
        "url": "https://www.state.gov/rss-feed/",
        "country": "US",
    },
    {
        "name": "Department of Defense",
        "url": "https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?ContentType=1",
        "country": "US",
    },
    {
        "name": "Voice of America",
        "url": "https://www.voanews.com/api/zq$omekgqy",
        "country": "US",
    },
    # Canada
    {
        "name": "Canada.ca News",
        "url": "https://www.canada.ca/en/news/web-feeds/news.atom.xml",
        "country": "CA",
    },
    {
        "name": "Global Affairs Canada",
        "url": "https://www.international.gc.ca/rss/news-nouvelles-en.xml",
        "country": "CA",
    },
    # ============================================
    # GOVERNMENT SOURCES - EUROPE
    # ============================================
    # United Kingdom
    {
        "name": "GOV.UK News",
        "url": "https://www.gov.uk/government/announcements.atom",
        "country": "GB",
    },
    {
        "name": "UK Foreign Office",
        "url": "https://www.gov.uk/government/organisations/foreign-commonwealth-development-office.atom",
        "country": "GB",
    },
    # Germany
    {
        "name": "German Government",
        "url": "https://www.bundesregierung.de/breg-de/feed.rss",
        "country": "DE",
    },
    # France
    {
        "name": "France Diplomacy",
        "url": "https://www.diplomatie.gouv.fr/spip.php?page=backend&lang=en",
        "country": "FR",
    },
    {"name": "Elysee", "url": "https://www.elysee.fr/flux-rss", "country": "FR"},
    # Netherlands
    {
        "name": "Netherlands Gov",
        "url": "https://www.government.nl/rss/news",
        "country": "NL",
    },
    # Sweden
    {
        "name": "Swedish Government",
        "url": "https://www.government.se/rss/news/",
        "country": "SE",
    },
    # Norway
    {
        "name": "Norwegian Government",
        "url": "https://www.regjeringen.no/en/rss/",
        "country": "NO",
    },
    # Poland
    {
        "name": "Polish Government",
        "url": "https://www.gov.pl/rss/premier",
        "country": "PL",
    },
    # Ukraine
    {
        "name": "Ukraine Gov",
        "url": "https://www.president.gov.ua/en/rss",
        "country": "UA",
    },
    {"name": "Ukraine MFA", "url": "https://mfa.gov.ua/en/rss", "country": "UA"},
    # Russia
    {
        "name": "Kremlin",
        "url": "http://kremlin.ru/events/president/news/rss",
        "country": "RU",
    },
    {"name": "Russia MFA", "url": "https://www.mid.ru/en/rss/", "country": "RU"},
    # ============================================
    # GOVERNMENT SOURCES - ASIA
    # ============================================
    # Japan
    {
        "name": "Japan PM Office",
        "url": "https://japan.kantei.go.jp/rss/rss_e_main.xml",
        "country": "JP",
    },
    {
        "name": "Japan MOFA",
        "url": "https://www.mofa.go.jp/rss/index.xml",
        "country": "JP",
    },
    # South Korea
    {"name": "Korea.net", "url": "https://www.korea.net/rss/news.xml", "country": "KR"},
    # China
    {
        "name": "Xinhua",
        "url": "http://www.xinhuanet.com/english/rss/worldrss.xml",
        "country": "CN",
    },
    {
        "name": "China MFA",
        "url": "https://www.fmprc.gov.cn/mfa_eng/rss/",
        "country": "CN",
    },
    # India
    {
        "name": "PIB India",
        "url": "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3",
        "country": "IN",
    },
    {"name": "India MEA", "url": "https://www.mea.gov.in/rss_en.xml", "country": "IN"},
    # Singapore
    {"name": "Singapore Gov", "url": "https://www.gov.sg/rss", "country": "SG"},
    # Indonesia
    {"name": "Indonesia MFA", "url": "https://kemlu.go.id/rss/news", "country": "ID"},
    # Thailand
    {"name": "Thailand Gov", "url": "https://www.thaigov.go.th/rss/", "country": "TH"},
    # Philippines
    {"name": "Philippines Gov", "url": "https://pcoo.gov.ph/feed/", "country": "PH"},
    # Pakistan
    {
        "name": "Pakistan Gov",
        "url": "https://www.pakistan.gov.pk/rss.html",
        "country": "PK",
    },
    # Bangladesh
    {"name": "Bangladesh Gov", "url": "https://bangladesh.gov.bd/rss", "country": "BD"},
    # ============================================
    # GOVERNMENT SOURCES - MIDDLE EAST
    # ============================================
    # Israel
    {
        "name": "Israel MFA",
        "url": "https://www.gov.il/en/departments/news/rss",
        "country": "IL",
    },
    {"name": "Israel GPO", "url": "https://www.gov.il/en/rss", "country": "IL"},
    # Saudi Arabia
    {
        "name": "Saudi Press Agency",
        "url": "https://www.spa.gov.sa/rss/2",
        "country": "SA",
    },
    # UAE
    {"name": "WAM UAE", "url": "https://www.wam.ae/en/rss/economy", "country": "AE"},
    # Turkey
    {
        "name": "Anadolu Agency",
        "url": "https://www.aa.com.tr/en/rss/default?cat=world",
        "country": "TR",
    },
    # Egypt
    {"name": "Egypt SIS", "url": "https://www.sis.gov.eg/rss/", "country": "EG"},
    # Iran
    {"name": "IRNA", "url": "https://en.irna.ir/rss", "country": "IR"},
    # Qatar
    {
        "name": "Qatar News Agency",
        "url": "https://www.qna.org.qa/en/News-Area/RSS",
        "country": "QA",
    },
    # ============================================
    # GOVERNMENT SOURCES - AFRICA
    # ============================================
    # South Africa
    {
        "name": "SA Gov News",
        "url": "https://www.sanews.gov.za/rss.xml",
        "country": "ZA",
    },
    {
        "name": "South Africa GCIS",
        "url": "https://www.gcis.gov.za/rss.xml",
        "country": "ZA",
    },
    # Nigeria
    {"name": "Nigeria NAN", "url": "https://nannews.ng/feed/", "country": "NG"},
    # Kenya
    {
        "name": "Kenya State House",
        "url": "https://www.president.go.ke/feed/",
        "country": "KE",
    },
    # Ethiopia
    {"name": "Ethiopia MFA", "url": "https://www.mfa.gov.et/rss/", "country": "ET"},
    # ============================================
    # GOVERNMENT SOURCES - LATIN AMERICA
    # ============================================
    # Brazil
    {"name": "Brazil Gov", "url": "https://www.gov.br/rss/", "country": "BR"},
    {
        "name": "Agencia Brasil",
        "url": "https://agenciabrasil.ebc.com.br/rss/ultimasnoticias/feed.xml",
        "country": "BR",
    },
    # Mexico
    {"name": "Mexico Presidency", "url": "https://www.gob.mx/rss/", "country": "MX"},
    # Argentina
    {"name": "Telam", "url": "https://www.telam.com.ar/rss2/", "country": "AR"},
    {
        "name": "Argentina Casa Rosada",
        "url": "https://www.casarosada.gob.ar/rss/",
        "country": "AR",
    },
    # Chile
    {"name": "Chile Gov", "url": "https://www.gob.cl/rss/", "country": "CL"},
    # Colombia
    {
        "name": "Colombia Presidency",
        "url": "https://www.presidencia.gov.co/rss/",
        "country": "CO",
    },
    # Peru
    {"name": "Andina Peru", "url": "https://andina.pe/agencia/rss/", "country": "PE"},
    # ============================================
    # GOVERNMENT SOURCES - OCEANIA
    # ============================================
    # Australia
    {
        "name": "Australia DFAT",
        "url": "https://www.dfat.gov.au/rss.xml",
        "country": "AU",
    },
    {
        "name": "Australian Government",
        "url": "https://www.pm.gov.au/rss.xml",
        "country": "AU",
    },
    # New Zealand
    {
        "name": "NZ Government",
        "url": "https://www.beehive.govt.nz/rss.xml",
        "country": "NZ",
    },
    {"name": "NZ MFAT", "url": "https://www.mfat.govt.nz/rss.xml", "country": "NZ"},
    # ============================================
    # THINK TANKS & RESEARCH
    # ============================================
    {"name": "Brookings", "url": "https://www.brookings.edu/feed/", "country": "US"},
    {"name": "CSIS", "url": "https://www.csis.org/feed", "country": "US"},
    {
        "name": "Council on Foreign Relations",
        "url": "https://www.cfr.org/rss.xml",
        "country": "US",
    },
    {
        "name": "RAND Corporation",
        "url": "https://www.rand.org/news/press.xml",
        "country": "US",
    },
    {
        "name": "Chatham House",
        "url": "https://www.chathamhouse.org/rss",
        "country": "GB",
    },
    {"name": "IISS", "url": "https://www.iiss.org/rss/", "country": "GB"},
    {
        "name": "Carnegie Endowment",
        "url": "https://carnegieendowment.org/rss/solr?sortBy=created",
        "country": "US",
    },
    {
        "name": "Atlantic Council",
        "url": "https://www.atlanticcouncil.org/feed/",
        "country": "US",
    },
    {
        "name": "Foreign Policy",
        "url": "https://foreignpolicy.com/feed/",
        "country": "US",
    },
    {"name": "The Diplomat", "url": "https://thediplomat.com/feed/", "country": "US"},
    {
        "name": "War on the Rocks",
        "url": "https://warontherocks.com/feed/",
        "country": "US",
    },
    {"name": "Lawfare", "url": "https://www.lawfareblog.com/rss.xml", "country": "US"},
]


class OfficialSourcesCollector(BaseCollector):
    """Collector for official news sources - UN, WHO, governments, think tanks."""

    source_type = "official"

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout, follow_redirects=True)

    def is_configured(self) -> bool:
        """Official RSS feeds are public."""
        return True

    async def collect(self) -> List[CollectedArticle]:
        """Collect articles from official sources."""
        articles = []

        for feed_config in OFFICIAL_FEEDS:
            try:
                feed_articles = await self._fetch_feed(feed_config)
                articles.extend(feed_articles)
                logger.debug(
                    "Fetched official feed",
                    feed=feed_config["name"],
                    count=len(feed_articles),
                )
            except Exception as e:
                logger.debug(
                    "Failed to fetch official feed",
                    feed=feed_config["name"],
                    error=str(e),
                )

        logger.info("Fetched official source articles", count=len(articles))
        return articles

    async def _fetch_feed(self, feed_config: dict) -> List[CollectedArticle]:
        """Fetch and parse an official RSS feed."""
        articles = []

        try:
            response = await self.client.get(feed_config["url"])
            response.raise_for_status()

            feed = feedparser.parse(response.text)

            for entry in feed.entries[:25]:  # Limit per feed
                article = self._parse_entry(entry, feed_config)
                if article:
                    articles.append(article)

        except Exception as e:
            raise Exception(f"Failed to fetch {feed_config['url']}: {e}")

        return articles

    def _parse_entry(self, entry, feed_config: dict) -> Optional[CollectedArticle]:
        """Parse a feed entry into a CollectedArticle."""
        try:
            # Get URL
            url = getattr(entry, "link", None)
            if not url:
                return None

            # Get title
            title = getattr(entry, "title", None)
            if not title:
                return None

            # Get content/description
            content = None
            if hasattr(entry, "summary"):
                content = entry.summary
            elif hasattr(entry, "description"):
                content = entry.description

            # Parse published date
            published_at = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published_at = datetime.fromtimestamp(mktime(entry.published_parsed))
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                published_at = datetime.fromtimestamp(mktime(entry.updated_parsed))

            # Get country
            country_code = feed_config.get("country")
            if not country_code:
                # Try to detect from content for international sources
                country_code = detect_country_from_text(content, title)

            return CollectedArticle(
                source_type=self.source_type,
                source_name=feed_config["name"],
                title=title.strip(),
                url=url,
                content=content,
                country_code=country_code,
                published_at=published_at,
            )

        except Exception as e:
            logger.debug("Failed to parse official feed entry", error=str(e))
            return None

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
