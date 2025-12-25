"""Google News RSS collector - Country-specific news from Google News.

Google News provides RSS feeds for different countries and languages,
offering broad global coverage of news from trusted sources.
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


# Google News RSS feeds by country/language
# Format: https://news.google.com/rss?hl={lang}&gl={country}&ceid={country}:{lang}
GOOGLE_NEWS_FEEDS = [
    # North America
    {"name": "Google News US", "url": "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en", "country": "US"},
    {"name": "Google News Canada EN", "url": "https://news.google.com/rss?hl=en-CA&gl=CA&ceid=CA:en", "country": "CA"},
    {"name": "Google News Canada FR", "url": "https://news.google.com/rss?hl=fr-CA&gl=CA&ceid=CA:fr", "country": "CA"},
    {"name": "Google News Mexico", "url": "https://news.google.com/rss?hl=es-419&gl=MX&ceid=MX:es-419", "country": "MX"},
    
    # Europe - Western
    {"name": "Google News UK", "url": "https://news.google.com/rss?hl=en-GB&gl=GB&ceid=GB:en", "country": "GB"},
    {"name": "Google News France", "url": "https://news.google.com/rss?hl=fr&gl=FR&ceid=FR:fr", "country": "FR"},
    {"name": "Google News Germany", "url": "https://news.google.com/rss?hl=de&gl=DE&ceid=DE:de", "country": "DE"},
    {"name": "Google News Italy", "url": "https://news.google.com/rss?hl=it&gl=IT&ceid=IT:it", "country": "IT"},
    {"name": "Google News Spain", "url": "https://news.google.com/rss?hl=es&gl=ES&ceid=ES:es", "country": "ES"},
    {"name": "Google News Portugal", "url": "https://news.google.com/rss?hl=pt-PT&gl=PT&ceid=PT:pt-150", "country": "PT"},
    {"name": "Google News Netherlands", "url": "https://news.google.com/rss?hl=nl&gl=NL&ceid=NL:nl", "country": "NL"},
    {"name": "Google News Belgium FR", "url": "https://news.google.com/rss?hl=fr&gl=BE&ceid=BE:fr", "country": "BE"},
    {"name": "Google News Belgium NL", "url": "https://news.google.com/rss?hl=nl&gl=BE&ceid=BE:nl", "country": "BE"},
    {"name": "Google News Switzerland DE", "url": "https://news.google.com/rss?hl=de&gl=CH&ceid=CH:de", "country": "CH"},
    {"name": "Google News Switzerland FR", "url": "https://news.google.com/rss?hl=fr&gl=CH&ceid=CH:fr", "country": "CH"},
    {"name": "Google News Austria", "url": "https://news.google.com/rss?hl=de&gl=AT&ceid=AT:de", "country": "AT"},
    {"name": "Google News Ireland", "url": "https://news.google.com/rss?hl=en-IE&gl=IE&ceid=IE:en", "country": "IE"},
    
    # Europe - Nordic
    {"name": "Google News Sweden", "url": "https://news.google.com/rss?hl=sv&gl=SE&ceid=SE:sv", "country": "SE"},
    {"name": "Google News Norway", "url": "https://news.google.com/rss?hl=no&gl=NO&ceid=NO:no", "country": "NO"},
    {"name": "Google News Denmark", "url": "https://news.google.com/rss?hl=da&gl=DK&ceid=DK:da", "country": "DK"},
    {"name": "Google News Finland", "url": "https://news.google.com/rss?hl=fi&gl=FI&ceid=FI:fi", "country": "FI"},
    
    # Europe - Eastern & Central
    {"name": "Google News Poland", "url": "https://news.google.com/rss?hl=pl&gl=PL&ceid=PL:pl", "country": "PL"},
    {"name": "Google News Czech", "url": "https://news.google.com/rss?hl=cs&gl=CZ&ceid=CZ:cs", "country": "CZ"},
    {"name": "Google News Hungary", "url": "https://news.google.com/rss?hl=hu&gl=HU&ceid=HU:hu", "country": "HU"},
    {"name": "Google News Romania", "url": "https://news.google.com/rss?hl=ro&gl=RO&ceid=RO:ro", "country": "RO"},
    {"name": "Google News Bulgaria", "url": "https://news.google.com/rss?hl=bg&gl=BG&ceid=BG:bg", "country": "BG"},
    {"name": "Google News Greece", "url": "https://news.google.com/rss?hl=el&gl=GR&ceid=GR:el", "country": "GR"},
    {"name": "Google News Ukraine", "url": "https://news.google.com/rss?hl=uk&gl=UA&ceid=UA:uk", "country": "UA"},
    {"name": "Google News Russia", "url": "https://news.google.com/rss?hl=ru&gl=RU&ceid=RU:ru", "country": "RU"},
    {"name": "Google News Latvia", "url": "https://news.google.com/rss?hl=lv&gl=LV&ceid=LV:lv", "country": "LV"},
    {"name": "Google News Lithuania", "url": "https://news.google.com/rss?hl=lt&gl=LT&ceid=LT:lt", "country": "LT"},
    {"name": "Google News Serbia", "url": "https://news.google.com/rss?hl=sr&gl=RS&ceid=RS:sr", "country": "RS"},
    {"name": "Google News Croatia", "url": "https://news.google.com/rss?hl=hr&gl=HR&ceid=HR:hr", "country": "HR"},
    {"name": "Google News Slovenia", "url": "https://news.google.com/rss?hl=sl&gl=SI&ceid=SI:sl", "country": "SI"},
    {"name": "Google News Slovakia", "url": "https://news.google.com/rss?hl=sk&gl=SK&ceid=SK:sk", "country": "SK"},
    
    # Asia - East
    {"name": "Google News Japan", "url": "https://news.google.com/rss?hl=ja&gl=JP&ceid=JP:ja", "country": "JP"},
    {"name": "Google News South Korea", "url": "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko", "country": "KR"},
    {"name": "Google News China", "url": "https://news.google.com/rss?hl=zh-CN&gl=CN&ceid=CN:zh-Hans", "country": "CN"},
    {"name": "Google News Taiwan", "url": "https://news.google.com/rss?hl=zh-TW&gl=TW&ceid=TW:zh-Hant", "country": "TW"},
    {"name": "Google News Hong Kong", "url": "https://news.google.com/rss?hl=zh-HK&gl=HK&ceid=HK:zh-Hant", "country": "HK"},
    
    # Asia - Southeast
    {"name": "Google News Singapore", "url": "https://news.google.com/rss?hl=en-SG&gl=SG&ceid=SG:en", "country": "SG"},
    {"name": "Google News Malaysia", "url": "https://news.google.com/rss?hl=ms&gl=MY&ceid=MY:ms", "country": "MY"},
    {"name": "Google News Indonesia", "url": "https://news.google.com/rss?hl=id&gl=ID&ceid=ID:id", "country": "ID"},
    {"name": "Google News Thailand", "url": "https://news.google.com/rss?hl=th&gl=TH&ceid=TH:th", "country": "TH"},
    {"name": "Google News Vietnam", "url": "https://news.google.com/rss?hl=vi&gl=VN&ceid=VN:vi", "country": "VN"},
    {"name": "Google News Philippines", "url": "https://news.google.com/rss?hl=en-PH&gl=PH&ceid=PH:en", "country": "PH"},
    
    # Asia - South
    {"name": "Google News India EN", "url": "https://news.google.com/rss?hl=en-IN&gl=IN&ceid=IN:en", "country": "IN"},
    {"name": "Google News India HI", "url": "https://news.google.com/rss?hl=hi&gl=IN&ceid=IN:hi", "country": "IN"},
    {"name": "Google News India TA", "url": "https://news.google.com/rss?hl=ta&gl=IN&ceid=IN:ta", "country": "IN"},
    {"name": "Google News India TE", "url": "https://news.google.com/rss?hl=te&gl=IN&ceid=IN:te", "country": "IN"},
    {"name": "Google News India BN", "url": "https://news.google.com/rss?hl=bn&gl=IN&ceid=IN:bn", "country": "IN"},
    {"name": "Google News India MR", "url": "https://news.google.com/rss?hl=mr&gl=IN&ceid=IN:mr", "country": "IN"},
    {"name": "Google News Pakistan", "url": "https://news.google.com/rss?hl=en-PK&gl=PK&ceid=PK:en", "country": "PK"},
    {"name": "Google News Bangladesh", "url": "https://news.google.com/rss?hl=bn&gl=BD&ceid=BD:bn", "country": "BD"},
    {"name": "Google News Sri Lanka", "url": "https://news.google.com/rss?hl=si&gl=LK&ceid=LK:si", "country": "LK"},
    
    # Middle East
    {"name": "Google News Israel HE", "url": "https://news.google.com/rss?hl=he&gl=IL&ceid=IL:he", "country": "IL"},
    {"name": "Google News Israel EN", "url": "https://news.google.com/rss?hl=en-IL&gl=IL&ceid=IL:en", "country": "IL"},
    {"name": "Google News UAE", "url": "https://news.google.com/rss?hl=ar&gl=AE&ceid=AE:ar", "country": "AE"},
    {"name": "Google News Saudi Arabia", "url": "https://news.google.com/rss?hl=ar&gl=SA&ceid=SA:ar", "country": "SA"},
    {"name": "Google News Egypt", "url": "https://news.google.com/rss?hl=ar&gl=EG&ceid=EG:ar", "country": "EG"},
    {"name": "Google News Turkey", "url": "https://news.google.com/rss?hl=tr&gl=TR&ceid=TR:tr", "country": "TR"},
    {"name": "Google News Lebanon", "url": "https://news.google.com/rss?hl=ar&gl=LB&ceid=LB:ar", "country": "LB"},
    {"name": "Google News Jordan", "url": "https://news.google.com/rss?hl=ar&gl=JO&ceid=JO:ar", "country": "JO"},
    {"name": "Google News Morocco", "url": "https://news.google.com/rss?hl=ar&gl=MA&ceid=MA:ar", "country": "MA"},
    {"name": "Google News Algeria", "url": "https://news.google.com/rss?hl=ar&gl=DZ&ceid=DZ:ar", "country": "DZ"},
    {"name": "Google News Tunisia", "url": "https://news.google.com/rss?hl=ar&gl=TN&ceid=TN:ar", "country": "TN"},
    {"name": "Google News Iraq", "url": "https://news.google.com/rss?hl=ar&gl=IQ&ceid=IQ:ar", "country": "IQ"},
    
    # Africa
    {"name": "Google News South Africa", "url": "https://news.google.com/rss?hl=en-ZA&gl=ZA&ceid=ZA:en", "country": "ZA"},
    {"name": "Google News Nigeria", "url": "https://news.google.com/rss?hl=en-NG&gl=NG&ceid=NG:en", "country": "NG"},
    {"name": "Google News Kenya", "url": "https://news.google.com/rss?hl=en-KE&gl=KE&ceid=KE:en", "country": "KE"},
    {"name": "Google News Ghana", "url": "https://news.google.com/rss?hl=en-GH&gl=GH&ceid=GH:en", "country": "GH"},
    {"name": "Google News Tanzania", "url": "https://news.google.com/rss?hl=sw&gl=TZ&ceid=TZ:sw", "country": "TZ"},
    {"name": "Google News Ethiopia", "url": "https://news.google.com/rss?hl=am&gl=ET&ceid=ET:am", "country": "ET"},
    {"name": "Google News Uganda", "url": "https://news.google.com/rss?hl=en-UG&gl=UG&ceid=UG:en", "country": "UG"},
    {"name": "Google News Zimbabwe", "url": "https://news.google.com/rss?hl=en-ZW&gl=ZW&ceid=ZW:en", "country": "ZW"},
    {"name": "Google News Senegal", "url": "https://news.google.com/rss?hl=fr&gl=SN&ceid=SN:fr", "country": "SN"},
    {"name": "Google News Ivory Coast", "url": "https://news.google.com/rss?hl=fr&gl=CI&ceid=CI:fr", "country": "CI"},
    {"name": "Google News Cameroon", "url": "https://news.google.com/rss?hl=fr&gl=CM&ceid=CM:fr", "country": "CM"},
    
    # Oceania
    {"name": "Google News Australia", "url": "https://news.google.com/rss?hl=en-AU&gl=AU&ceid=AU:en", "country": "AU"},
    {"name": "Google News New Zealand", "url": "https://news.google.com/rss?hl=en-NZ&gl=NZ&ceid=NZ:en", "country": "NZ"},
    
    # Latin America
    {"name": "Google News Brazil", "url": "https://news.google.com/rss?hl=pt-BR&gl=BR&ceid=BR:pt-419", "country": "BR"},
    {"name": "Google News Argentina", "url": "https://news.google.com/rss?hl=es-419&gl=AR&ceid=AR:es-419", "country": "AR"},
    {"name": "Google News Chile", "url": "https://news.google.com/rss?hl=es-419&gl=CL&ceid=CL:es-419", "country": "CL"},
    {"name": "Google News Colombia", "url": "https://news.google.com/rss?hl=es-419&gl=CO&ceid=CO:es-419", "country": "CO"},
    {"name": "Google News Peru", "url": "https://news.google.com/rss?hl=es-419&gl=PE&ceid=PE:es-419", "country": "PE"},
    {"name": "Google News Venezuela", "url": "https://news.google.com/rss?hl=es-419&gl=VE&ceid=VE:es-419", "country": "VE"},
    {"name": "Google News Ecuador", "url": "https://news.google.com/rss?hl=es-419&gl=EC&ceid=EC:es-419", "country": "EC"},
    {"name": "Google News Cuba", "url": "https://news.google.com/rss?hl=es-419&gl=CU&ceid=CU:es-419", "country": "CU"},
    {"name": "Google News Costa Rica", "url": "https://news.google.com/rss?hl=es-419&gl=CR&ceid=CR:es-419", "country": "CR"},
    {"name": "Google News Guatemala", "url": "https://news.google.com/rss?hl=es-419&gl=GT&ceid=GT:es-419", "country": "GT"},
    {"name": "Google News Dominican Republic", "url": "https://news.google.com/rss?hl=es-419&gl=DO&ceid=DO:es-419", "country": "DO"},
    {"name": "Google News Puerto Rico", "url": "https://news.google.com/rss?hl=es-419&gl=PR&ceid=PR:es-419", "country": "PR"},
    {"name": "Google News Uruguay", "url": "https://news.google.com/rss?hl=es-419&gl=UY&ceid=UY:es-419", "country": "UY"},
    {"name": "Google News Paraguay", "url": "https://news.google.com/rss?hl=es-419&gl=PY&ceid=PY:es-419", "country": "PY"},
    {"name": "Google News Bolivia", "url": "https://news.google.com/rss?hl=es-419&gl=BO&ceid=BO:es-419", "country": "BO"},
    {"name": "Google News Panama", "url": "https://news.google.com/rss?hl=es-419&gl=PA&ceid=PA:es-419", "country": "PA"},
    {"name": "Google News Honduras", "url": "https://news.google.com/rss?hl=es-419&gl=HN&ceid=HN:es-419", "country": "HN"},
    {"name": "Google News El Salvador", "url": "https://news.google.com/rss?hl=es-419&gl=SV&ceid=SV:es-419", "country": "SV"},
    {"name": "Google News Nicaragua", "url": "https://news.google.com/rss?hl=es-419&gl=NI&ceid=NI:es-419", "country": "NI"},
]


class GoogleNewsCollector(BaseCollector):
    """Collector for Google News RSS feeds by country."""
    
    source_type = "googlenews"
    
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout, follow_redirects=True)
    
    def is_configured(self) -> bool:
        """Google News RSS is free and public."""
        return True
    
    async def collect(self) -> List[CollectedArticle]:
        """Collect articles from all Google News country feeds."""
        articles = []
        
        for feed_config in GOOGLE_NEWS_FEEDS:
            try:
                feed_articles = await self._fetch_feed(feed_config)
                articles.extend(feed_articles)
                logger.debug(
                    "Fetched Google News feed",
                    feed=feed_config["name"],
                    count=len(feed_articles)
                )
            except Exception as e:
                logger.debug(
                    "Failed to fetch Google News feed",
                    feed=feed_config["name"],
                    error=str(e)
                )
        
        logger.info("Fetched Google News articles", count=len(articles))
        return articles
    
    async def _fetch_feed(self, feed_config: dict) -> List[CollectedArticle]:
        """Fetch and parse a Google News RSS feed."""
        articles = []
        
        try:
            response = await self.client.get(feed_config["url"])
            response.raise_for_status()
            
            feed = feedparser.parse(response.text)
            
            for entry in feed.entries[:30]:  # Limit per feed
                article = self._parse_entry(entry, feed_config)
                if article:
                    articles.append(article)
        
        except Exception as e:
            raise Exception(f"Failed to fetch {feed_config['url']}: {e}")
        
        return articles
    
    def _parse_entry(self, entry, feed_config: dict) -> Optional[CollectedArticle]:
        """Parse a feed entry into a CollectedArticle."""
        try:
            # Get URL (Google News wraps URLs)
            url = getattr(entry, 'link', None)
            if not url:
                return None
            
            # Get title
            title = getattr(entry, 'title', None)
            if not title:
                return None
            
            # Get content/description
            content = None
            if hasattr(entry, 'summary'):
                content = entry.summary
            elif hasattr(entry, 'description'):
                content = entry.description
            
            # Parse published date
            published_at = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published_at = datetime.fromtimestamp(mktime(entry.published_parsed))
            
            # Get source name from title (format: "Title - Source Name")
            source_name = "Google News"
            if " - " in title:
                parts = title.rsplit(" - ", 1)
                if len(parts) == 2:
                    title = parts[0]
                    source_name = parts[1]
            
            return CollectedArticle(
                source_type=self.source_type,
                source_name=source_name,
                title=title.strip(),
                url=url,
                content=content,
                country_code=feed_config.get("country"),
                published_at=published_at,
            )
        
        except Exception as e:
            logger.debug("Failed to parse Google News entry", error=str(e))
            return None
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

