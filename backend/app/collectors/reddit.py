"""Reddit collector using PRAW."""

import asyncio
from typing import List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from app.collectors.base import BaseCollector, CollectedArticle
from app.utils.geo import get_country_from_subreddit, detect_country_from_text
from app.utils.logging import get_logger
from app.config import get_settings

logger = get_logger(__name__)
settings = get_settings()

# Comprehensive subreddits to monitor for news and sentiment
SUBREDDITS = [
    # ============================================
    # GLOBAL NEWS
    # ============================================
    {"name": "worldnews", "country": None, "limit": 100},
    {"name": "news", "country": "US", "limit": 100},
    {"name": "politics", "country": "US", "limit": 50},
    {"name": "geopolitics", "country": None, "limit": 50},
    {"name": "anime_titties", "country": None, "limit": 50},  # Actually a serious world news sub
    {"name": "inthenews", "country": None, "limit": 30},
    {"name": "neutralnews", "country": None, "limit": 30},
    {"name": "qualitynews", "country": None, "limit": 30},
    
    # ============================================
    # NORTH AMERICA
    # ============================================
    # United States - National
    {"name": "uspolitics", "country": "US", "limit": 30},
    {"name": "usanews", "country": "US", "limit": 30},
    {"name": "moderatepolitics", "country": "US", "limit": 30},
    {"name": "PoliticalDiscussion", "country": "US", "limit": 30},
    {"name": "NeutralPolitics", "country": "US", "limit": 30},
    {"name": "Conservative", "country": "US", "limit": 30},
    {"name": "Liberal", "country": "US", "limit": 30},
    {"name": "democrats", "country": "US", "limit": 30},
    
    # Canada
    {"name": "canada", "country": "CA", "limit": 50},
    {"name": "CanadaPolitics", "country": "CA", "limit": 30},
    {"name": "onguardforthee", "country": "CA", "limit": 30},
    {"name": "ontario", "country": "CA", "limit": 20},
    {"name": "quebec", "country": "CA", "limit": 20},
    {"name": "britishcolumbia", "country": "CA", "limit": 20},
    {"name": "alberta", "country": "CA", "limit": 20},
    
    # Mexico
    {"name": "mexico", "country": "MX", "limit": 50},
    {"name": "mujico", "country": "MX", "limit": 30},
    
    # ============================================
    # EUROPE - WESTERN
    # ============================================
    # Pan-European
    {"name": "europe", "country": None, "limit": 50},
    {"name": "EuropeanUnion", "country": None, "limit": 30},
    {"name": "EuropeanFederalists", "country": None, "limit": 20},
    {"name": "europes", "country": None, "limit": 20},
    
    # United Kingdom
    {"name": "unitedkingdom", "country": "GB", "limit": 50},
    {"name": "ukpolitics", "country": "GB", "limit": 50},
    {"name": "casualuk", "country": "GB", "limit": 30},
    {"name": "london", "country": "GB", "limit": 20},
    {"name": "scotland", "country": "GB", "limit": 20},
    {"name": "wales", "country": "GB", "limit": 20},
    {"name": "northernireland", "country": "GB", "limit": 20},
    {"name": "GreenAndPleasant", "country": "GB", "limit": 20},
    {"name": "LabourUK", "country": "GB", "limit": 20},
    {"name": "tories", "country": "GB", "limit": 20},
    
    # France
    {"name": "france", "country": "FR", "limit": 50},
    {"name": "French", "country": "FR", "limit": 20},
    {"name": "paris", "country": "FR", "limit": 20},
    
    # Germany
    {"name": "germany", "country": "DE", "limit": 50},
    {"name": "de", "country": "DE", "limit": 50},
    {"name": "berlin", "country": "DE", "limit": 20},
    {"name": "munich", "country": "DE", "limit": 20},
    
    # Italy
    {"name": "italy", "country": "IT", "limit": 40},
    {"name": "Italia", "country": "IT", "limit": 30},
    {"name": "rome", "country": "IT", "limit": 20},
    
    # Spain
    {"name": "spain", "country": "ES", "limit": 40},
    {"name": "es", "country": "ES", "limit": 30},
    {"name": "barcelona", "country": "ES", "limit": 20},
    {"name": "madrid", "country": "ES", "limit": 20},
    {"name": "catalunya", "country": "ES", "limit": 20},
    
    # Portugal
    {"name": "portugal", "country": "PT", "limit": 30},
    {"name": "lisboa", "country": "PT", "limit": 15},
    
    # Netherlands
    {"name": "thenetherlands", "country": "NL", "limit": 40},
    {"name": "Netherlands", "country": "NL", "limit": 30},
    {"name": "Amsterdam", "country": "NL", "limit": 20},
    
    # Belgium
    {"name": "belgium", "country": "BE", "limit": 30},
    {"name": "brussels", "country": "BE", "limit": 20},
    
    # Switzerland
    {"name": "Switzerland", "country": "CH", "limit": 30},
    {"name": "zurich", "country": "CH", "limit": 15},
    
    # Austria
    {"name": "Austria", "country": "AT", "limit": 30},
    {"name": "wien", "country": "AT", "limit": 20},
    
    # Ireland
    {"name": "ireland", "country": "IE", "limit": 40},
    {"name": "Dublin", "country": "IE", "limit": 20},
    {"name": "irishpolitics", "country": "IE", "limit": 20},
    
    # ============================================
    # EUROPE - NORDIC
    # ============================================
    {"name": "sweden", "country": "SE", "limit": 30},
    {"name": "sweden_news", "country": "SE", "limit": 20},
    {"name": "stockholm", "country": "SE", "limit": 15},
    {"name": "norway", "country": "NO", "limit": 30},
    {"name": "norge", "country": "NO", "limit": 25},
    {"name": "oslo", "country": "NO", "limit": 15},
    {"name": "Denmark", "country": "DK", "limit": 30},
    {"name": "copenhagen", "country": "DK", "limit": 15},
    {"name": "Finland", "country": "FI", "limit": 30},
    {"name": "Suomi", "country": "FI", "limit": 25},
    {"name": "helsinki", "country": "FI", "limit": 15},
    {"name": "Iceland", "country": "IS", "limit": 20},
    
    # ============================================
    # EUROPE - EASTERN & CENTRAL
    # ============================================
    # Poland
    {"name": "poland", "country": "PL", "limit": 40},
    {"name": "Polska", "country": "PL", "limit": 30},
    {"name": "warsaw", "country": "PL", "limit": 15},
    
    # Czech Republic
    {"name": "czech", "country": "CZ", "limit": 25},
    {"name": "Prague", "country": "CZ", "limit": 20},
    
    # Hungary
    {"name": "hungary", "country": "HU", "limit": 30},
    {"name": "budapest", "country": "HU", "limit": 15},
    
    # Romania
    {"name": "Romania", "country": "RO", "limit": 30},
    {"name": "bucuresti", "country": "RO", "limit": 15},
    
    # Bulgaria
    {"name": "bulgaria", "country": "BG", "limit": 25},
    
    # Greece
    {"name": "greece", "country": "GR", "limit": 30},
    {"name": "Athens", "country": "GR", "limit": 15},
    
    # Ukraine
    {"name": "ukraine", "country": "UA", "limit": 50},
    {"name": "ukraina", "country": "UA", "limit": 30},
    {"name": "UkrainianConflict", "country": "UA", "limit": 30},
    {"name": "UkraineWarVideoReport", "country": "UA", "limit": 30},
    
    # Russia
    {"name": "russia", "country": "RU", "limit": 30},
    {"name": "AskARussian", "country": "RU", "limit": 20},
    {"name": "liberta", "country": "RU", "limit": 20},
    
    # Baltic States
    {"name": "BalticStates", "country": None, "limit": 25},
    {"name": "lithuania", "country": "LT", "limit": 20},
    {"name": "latvia", "country": "LV", "limit": 20},
    {"name": "Eesti", "country": "EE", "limit": 20},
    
    # Balkans
    {"name": "serbia", "country": "RS", "limit": 25},
    {"name": "croatia", "country": "HR", "limit": 25},
    {"name": "bosnia", "country": "BA", "limit": 20},
    {"name": "slovenia", "country": "SI", "limit": 20},
    {"name": "albania", "country": "AL", "limit": 20},
    {"name": "Kosovo", "country": "XK", "limit": 15},
    {"name": "NorthMacedonia", "country": "MK", "limit": 15},
    {"name": "montenegro", "country": "ME", "limit": 15},
    
    # ============================================
    # ASIA - EAST
    # ============================================
    # Japan
    {"name": "japan", "country": "JP", "limit": 40},
    {"name": "newsokur", "country": "JP", "limit": 30},
    {"name": "Tokyo", "country": "JP", "limit": 20},
    {"name": "JapanLife", "country": "JP", "limit": 20},
    
    # South Korea
    {"name": "korea", "country": "KR", "limit": 40},
    {"name": "hanguk", "country": "KR", "limit": 30},
    {"name": "Korean", "country": "KR", "limit": 20},
    {"name": "seoul", "country": "KR", "limit": 20},
    
    # China
    {"name": "China", "country": "CN", "limit": 40},
    {"name": "sino", "country": "CN", "limit": 30},
    {"name": "ChineseLanguage", "country": "CN", "limit": 15},
    
    # Taiwan
    {"name": "taiwan", "country": "TW", "limit": 30},
    
    # Hong Kong
    {"name": "HongKong", "country": "HK", "limit": 30},
    
    # Mongolia
    {"name": "mongolia", "country": "MN", "limit": 15},
    
    # ============================================
    # ASIA - SOUTHEAST
    # ============================================
    {"name": "singapore", "country": "SG", "limit": 30},
    {"name": "malaysia", "country": "MY", "limit": 30},
    {"name": "indonesia", "country": "ID", "limit": 30},
    {"name": "Thailand", "country": "TH", "limit": 30},
    {"name": "vietnam", "country": "VN", "limit": 25},
    {"name": "Philippines", "country": "PH", "limit": 30},
    {"name": "Myanmar", "country": "MM", "limit": 20},
    {"name": "cambodia", "country": "KH", "limit": 15},
    {"name": "laos", "country": "LA", "limit": 15},
    
    # ============================================
    # ASIA - SOUTH
    # ============================================
    # India
    {"name": "india", "country": "IN", "limit": 50},
    {"name": "IndiaSpeaks", "country": "IN", "limit": 40},
    {"name": "unitedstatesofindia", "country": "IN", "limit": 30},
    {"name": "IndianPolitics", "country": "IN", "limit": 25},
    {"name": "mumbai", "country": "IN", "limit": 20},
    {"name": "delhi", "country": "IN", "limit": 20},
    {"name": "bangalore", "country": "IN", "limit": 20},
    
    # Pakistan
    {"name": "pakistan", "country": "PK", "limit": 35},
    {"name": "chutyapa", "country": "PK", "limit": 20},
    
    # Bangladesh
    {"name": "bangladesh", "country": "BD", "limit": 25},
    
    # Sri Lanka
    {"name": "srilanka", "country": "LK", "limit": 20},
    
    # Nepal
    {"name": "nepal", "country": "NP", "limit": 20},
    
    # Afghanistan
    {"name": "afghanistan", "country": "AF", "limit": 20},
    
    # ============================================
    # MIDDLE EAST
    # ============================================
    {"name": "MiddleEast", "country": None, "limit": 30},
    {"name": "Israel", "country": "IL", "limit": 40},
    {"name": "IsraelPalestine", "country": None, "limit": 30},
    {"name": "Palestine", "country": "PS", "limit": 30},
    {"name": "arabs", "country": None, "limit": 25},
    {"name": "SaudiArabia", "country": "SA", "limit": 25},
    {"name": "dubai", "country": "AE", "limit": 25},
    {"name": "UAE", "country": "AE", "limit": 20},
    {"name": "iran", "country": "IR", "limit": 30},
    {"name": "NewIran", "country": "IR", "limit": 20},
    {"name": "Turkey", "country": "TR", "limit": 35},
    {"name": "turkish", "country": "TR", "limit": 25},
    {"name": "Iraq", "country": "IQ", "limit": 25},
    {"name": "kurdistan", "country": None, "limit": 20},
    {"name": "Lebanon", "country": "LB", "limit": 25},
    {"name": "jordan", "country": "JO", "limit": 20},
    {"name": "Egypt", "country": "EG", "limit": 30},
    {"name": "syria", "country": "SY", "limit": 25},
    {"name": "syriancivilwar", "country": "SY", "limit": 25},
    {"name": "yemen", "country": "YE", "limit": 20},
    
    # ============================================
    # AFRICA
    # ============================================
    {"name": "Africa", "country": None, "limit": 30},
    {"name": "southafrica", "country": "ZA", "limit": 40},
    {"name": "johannesburg", "country": "ZA", "limit": 15},
    {"name": "capetown", "country": "ZA", "limit": 15},
    {"name": "Nigeria", "country": "NG", "limit": 30},
    {"name": "Kenya", "country": "KE", "limit": 25},
    {"name": "Ethiopia", "country": "ET", "limit": 20},
    {"name": "ghana", "country": "GH", "limit": 20},
    {"name": "tanzania", "country": "TZ", "limit": 15},
    {"name": "uganda", "country": "UG", "limit": 15},
    {"name": "Rwanda", "country": "RW", "limit": 15},
    {"name": "zimbabwe", "country": "ZW", "limit": 15},
    {"name": "zambia", "country": "ZM", "limit": 15},
    {"name": "Morocco", "country": "MA", "limit": 20},
    {"name": "algeria", "country": "DZ", "limit": 20},
    {"name": "Tunisia", "country": "TN", "limit": 20},
    {"name": "libya", "country": "LY", "limit": 15},
    {"name": "sudan", "country": "SD", "limit": 15},
    {"name": "SouthSudan", "country": "SS", "limit": 10},
    {"name": "somalia", "country": "SO", "limit": 15},
    {"name": "senegal", "country": "SN", "limit": 15},
    {"name": "CotedIvoire", "country": "CI", "limit": 10},
    {"name": "cameroon", "country": "CM", "limit": 15},
    {"name": "angola", "country": "AO", "limit": 15},
    {"name": "mozambique", "country": "MZ", "limit": 10},
    {"name": "botswana", "country": "BW", "limit": 10},
    {"name": "namibia", "country": "NA", "limit": 10},
    {"name": "mauritius", "country": "MU", "limit": 10},
    
    # ============================================
    # OCEANIA
    # ============================================
    # Australia
    {"name": "australia", "country": "AU", "limit": 50},
    {"name": "AustralianPolitics", "country": "AU", "limit": 30},
    {"name": "sydney", "country": "AU", "limit": 20},
    {"name": "melbourne", "country": "AU", "limit": 20},
    {"name": "brisbane", "country": "AU", "limit": 15},
    {"name": "perth", "country": "AU", "limit": 15},
    {"name": "adelaide", "country": "AU", "limit": 15},
    
    # New Zealand
    {"name": "newzealand", "country": "NZ", "limit": 40},
    {"name": "Wellington", "country": "NZ", "limit": 15},
    {"name": "Auckland", "country": "NZ", "limit": 20},
    
    # Pacific
    {"name": "fiji", "country": "FJ", "limit": 10},
    {"name": "PapuaNewGuinea", "country": "PG", "limit": 10},
    
    # ============================================
    # LATIN AMERICA
    # ============================================
    {"name": "LatinAmerica", "country": None, "limit": 30},
    
    # Brazil
    {"name": "brasil", "country": "BR", "limit": 50},
    {"name": "Brazil", "country": "BR", "limit": 30},
    {"name": "brasilivre", "country": "BR", "limit": 30},
    {"name": "saopaulo", "country": "BR", "limit": 20},
    {"name": "riodejaneiro", "country": "BR", "limit": 15},
    
    # Argentina
    {"name": "argentina", "country": "AR", "limit": 40},
    {"name": "buenosaires", "country": "AR", "limit": 20},
    
    # Chile
    {"name": "chile", "country": "CL", "limit": 35},
    {"name": "santiago", "country": "CL", "limit": 15},
    
    # Colombia
    {"name": "Colombia", "country": "CO", "limit": 30},
    {"name": "bogota", "country": "CO", "limit": 15},
    
    # Peru
    {"name": "PERU", "country": "PE", "limit": 25},
    {"name": "lima", "country": "PE", "limit": 15},
    
    # Venezuela
    {"name": "vzla", "country": "VE", "limit": 25},
    {"name": "venezuela", "country": "VE", "limit": 20},
    
    # Ecuador
    {"name": "ecuador", "country": "EC", "limit": 20},
    
    # Bolivia
    {"name": "BOLIVIA", "country": "BO", "limit": 15},
    
    # Uruguay
    {"name": "uruguay", "country": "UY", "limit": 20},
    
    # Paraguay
    {"name": "Paraguay", "country": "PY", "limit": 15},
    
    # Central America & Caribbean
    {"name": "Panama", "country": "PA", "limit": 15},
    {"name": "costarica", "country": "CR", "limit": 20},
    {"name": "Guatemala", "country": "GT", "limit": 15},
    {"name": "Honduras", "country": "HN", "limit": 10},
    {"name": "ElSalvador", "country": "SV", "limit": 15},
    {"name": "nicaragua", "country": "NI", "limit": 15},
    {"name": "Cuba", "country": "CU", "limit": 25},
    {"name": "RealCuba", "country": "CU", "limit": 15},
    {"name": "puertorico", "country": "PR", "limit": 20},
    {"name": "DominicanRepublic", "country": "DO", "limit": 15},
    {"name": "Haiti", "country": "HT", "limit": 15},
    {"name": "Jamaica", "country": "JM", "limit": 15},
    {"name": "TrinidadandTobago", "country": "TT", "limit": 10},
    
    # ============================================
    # CENTRAL ASIA & CAUCASUS
    # ============================================
    {"name": "Kazakhstan", "country": "KZ", "limit": 15},
    {"name": "uzbekistan", "country": "UZ", "limit": 10},
    {"name": "Kyrgyzstan", "country": "KG", "limit": 10},
    {"name": "Tajikistan", "country": "TJ", "limit": 10},
    {"name": "Turkmenistan", "country": "TM", "limit": 10},
    {"name": "Sakartvelo", "country": "GE", "limit": 20},  # Georgia
    {"name": "armenia", "country": "AM", "limit": 20},
    {"name": "azerbaijan", "country": "AZ", "limit": 20},
    {"name": "belarus", "country": "BY", "limit": 20},
    {"name": "moldova", "country": "MD", "limit": 15},
]


class RedditCollector(BaseCollector):
    """Collector for Reddit posts."""
    
    source_type = "reddit"
    
    def __init__(self):
        self._reddit = None
        self._executor = ThreadPoolExecutor(max_workers=4)  # Increased for more subreddits
    
    def is_configured(self) -> bool:
        """Check if Reddit credentials are configured."""
        return bool(settings.reddit_client_id and settings.reddit_client_secret)
    
    def _get_reddit(self):
        """Get or create Reddit instance (must be done in sync context)."""
        if self._reddit is None:
            try:
                import praw
                self._reddit = praw.Reddit(
                    client_id=settings.reddit_client_id,
                    client_secret=settings.reddit_client_secret,
                    user_agent=settings.reddit_user_agent,
                )
            except Exception as e:
                logger.error("Failed to initialize Reddit client", error=str(e))
                return None
        return self._reddit
    
    async def collect(self) -> List[CollectedArticle]:
        """Collect posts from monitored subreddits."""
        if not self.is_configured():
            logger.warning("Reddit collector not configured - skipping")
            return []
        
        articles = []
        loop = asyncio.get_event_loop()
        
        for sub_config in SUBREDDITS:
            try:
                # Run PRAW in thread pool since it's synchronous
                sub_articles = await loop.run_in_executor(
                    self._executor,
                    self._fetch_subreddit,
                    sub_config
                )
                articles.extend(sub_articles)
                logger.info(
                    "Fetched subreddit",
                    subreddit=sub_config["name"],
                    count=len(sub_articles)
                )
            except Exception as e:
                logger.warning(
                    "Failed to fetch subreddit",
                    subreddit=sub_config["name"],
                    error=str(e)
                )
        
        return articles
    
    def _fetch_subreddit(self, sub_config: dict) -> List[CollectedArticle]:
        """Fetch posts from a subreddit (synchronous)."""
        articles = []
        
        try:
            reddit = self._get_reddit()
            if not reddit:
                return articles
            
            subreddit = reddit.subreddit(sub_config["name"])
            
            for post in subreddit.hot(limit=sub_config["limit"]):
                # Skip stickied posts and self posts without much content
                if post.stickied:
                    continue
                
                article = self._parse_post(post, sub_config)
                if article:
                    articles.append(article)
        
        except Exception as e:
            raise Exception(f"Failed to fetch r/{sub_config['name']}: {e}")
        
        return articles
    
    def _parse_post(self, post, sub_config: dict) -> CollectedArticle:
        """Parse a Reddit post into a CollectedArticle."""
        try:
            # Get content
            content = post.selftext if post.selftext else post.title
            
            # Determine country - try multiple methods
            country_code = sub_config.get("country")
            
            # If no country from config, try to get from subreddit name
            if not country_code:
                country_code = get_country_from_subreddit(sub_config["name"])
            
            # If still no country (for global subs), detect from post text
            if not country_code:
                country_code = detect_country_from_text(content, post.title)
            
            return CollectedArticle(
                source_type=self.source_type,
                source_name=f"r/{sub_config['name']}",
                title=post.title,
                url=f"https://reddit.com{post.permalink}",
                content=content[:2000] if content else None,  # Limit content length
                country_code=country_code,
                published_at=datetime.fromtimestamp(post.created_utc),
            )
        
        except Exception as e:
            logger.debug("Failed to parse Reddit post", error=str(e))
            return None
