"""RSS feed collector for major news publications."""

import feedparser
import httpx
from typing import List, Optional
from datetime import datetime
from time import mktime

from app.collectors.base import BaseCollector, CollectedArticle
from app.utils.geo import get_country_from_source, detect_country_from_text
from app.utils.logging import get_logger

logger = get_logger(__name__)


# Comprehensive RSS feeds from around the world - organized by region
RSS_FEEDS = [
    # ============================================
    # INTERNATIONAL / WIRE SERVICES
    # ============================================
    {"name": "Reuters World", "url": "https://feeds.reuters.com/Reuters/worldNews", "country": None},
    {"name": "AP News", "url": "https://rsshub.app/apnews/topics/world-news", "country": None},
    {"name": "AFP", "url": "https://www.afp.com/en/feed", "country": None},
    {"name": "Euronews", "url": "https://www.euronews.com/rss?level=theme&name=news", "country": None},
    
    # ============================================
    # NORTH AMERICA
    # ============================================
    # United States
    {"name": "NPR News", "url": "https://feeds.npr.org/1001/rss.xml", "country": "US"},
    {"name": "PBS NewsHour", "url": "https://www.pbs.org/newshour/feeds/rss/headlines", "country": "US"},
    {"name": "NBC News", "url": "https://feeds.nbcnews.com/nbcnews/public/news", "country": "US"},
    {"name": "CBS News", "url": "https://www.cbsnews.com/latest/rss/main", "country": "US"},
    {"name": "ABC News", "url": "https://abcnews.go.com/abcnews/topstories", "country": "US"},
    {"name": "USA Today", "url": "http://rssfeeds.usatoday.com/UsatodaycomNation-TopStories", "country": "US"},
    {"name": "Washington Post", "url": "https://feeds.washingtonpost.com/rss/national", "country": "US"},
    {"name": "LA Times", "url": "https://www.latimes.com/world-nation/rss2.0.xml", "country": "US"},
    {"name": "New York Post", "url": "https://nypost.com/feed/", "country": "US"},
    {"name": "The Hill", "url": "https://thehill.com/feed/", "country": "US"},
    {"name": "Politico", "url": "https://www.politico.com/rss/politicopicks.xml", "country": "US"},
    
    # Canada
    {"name": "CBC News", "url": "https://www.cbc.ca/cmlink/rss-topstories", "country": "CA"},
    {"name": "CBC World", "url": "https://www.cbc.ca/cmlink/rss-world", "country": None},
    {"name": "CTV News", "url": "https://www.ctvnews.ca/rss/ctvnews-ca-top-stories-public-rss-1.822009", "country": "CA"},
    {"name": "Global News Canada", "url": "https://globalnews.ca/feed/", "country": "CA"},
    {"name": "Toronto Star", "url": "https://www.thestar.com/search/?f=rss&t=article&c=news*", "country": "CA"},
    {"name": "National Post", "url": "https://nationalpost.com/feed/", "country": "CA"},
    
    # Mexico
    {"name": "El Universal Mexico", "url": "https://www.eluniversal.com.mx/rss.xml", "country": "MX"},
    {"name": "Milenio", "url": "https://www.milenio.com/rss", "country": "MX"},
    {"name": "Excelsior", "url": "https://www.excelsior.com.mx/rss.xml", "country": "MX"},
    
    # ============================================
    # EUROPE - WESTERN
    # ============================================
    # United Kingdom
    {"name": "BBC News", "url": "https://feeds.bbci.co.uk/news/rss.xml", "country": "GB"},
    {"name": "BBC World", "url": "https://feeds.bbci.co.uk/news/world/rss.xml", "country": None},
    {"name": "The Guardian", "url": "https://www.theguardian.com/uk/rss", "country": "GB"},
    {"name": "Guardian World", "url": "https://www.theguardian.com/world/rss", "country": None},
    {"name": "Sky News", "url": "https://feeds.skynews.com/feeds/rss/world.xml", "country": None},
    {"name": "Sky News UK", "url": "https://feeds.skynews.com/feeds/rss/uk.xml", "country": "GB"},
    {"name": "The Telegraph", "url": "https://www.telegraph.co.uk/rss.xml", "country": "GB"},
    {"name": "The Independent", "url": "https://www.independent.co.uk/rss", "country": "GB"},
    {"name": "Daily Mail", "url": "https://www.dailymail.co.uk/news/index.rss", "country": "GB"},
    {"name": "Metro UK", "url": "https://metro.co.uk/feed/", "country": "GB"},
    
    # France
    {"name": "France 24", "url": "https://www.france24.com/en/rss", "country": "FR"},
    {"name": "France 24 World", "url": "https://www.france24.com/en/world/rss", "country": None},
    {"name": "Le Monde", "url": "https://www.lemonde.fr/rss/une.xml", "country": "FR"},
    {"name": "Le Figaro", "url": "https://www.lefigaro.fr/rss/figaro_actualites.xml", "country": "FR"},
    {"name": "RFI", "url": "https://www.rfi.fr/en/rss", "country": "FR"},
    {"name": "20 Minutes FR", "url": "https://www.20minutes.fr/feeds/rss-une.xml", "country": "FR"},
    
    # Germany
    {"name": "Deutsche Welle", "url": "https://rss.dw.com/rdf/rss-en-all", "country": "DE"},
    {"name": "DW World", "url": "https://rss.dw.com/xml/rss-en-world", "country": None},
    {"name": "Der Spiegel", "url": "https://www.spiegel.de/international/index.rss", "country": "DE"},
    {"name": "Tagesschau", "url": "https://www.tagesschau.de/xml/rss2/", "country": "DE"},
    {"name": "Die Zeit", "url": "https://newsfeed.zeit.de/index", "country": "DE"},
    {"name": "FAZ", "url": "https://www.faz.net/rss/aktuell/", "country": "DE"},
    
    # Italy
    {"name": "ANSA", "url": "https://www.ansa.it/sito/ansait_rss.xml", "country": "IT"},
    {"name": "La Repubblica", "url": "https://www.repubblica.it/rss/homepage/rss2.0.xml", "country": "IT"},
    {"name": "Corriere della Sera", "url": "https://xml2.corriereobjects.it/rss/homepage.xml", "country": "IT"},
    {"name": "La Stampa", "url": "https://www.lastampa.it/rss.xml", "country": "IT"},
    {"name": "Il Sole 24 Ore", "url": "https://www.ilsole24ore.com/rss/italia.xml", "country": "IT"},
    
    # Spain
    {"name": "El Pais", "url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada", "country": "ES"},
    {"name": "El Mundo", "url": "https://e00-elmundo.uecdn.es/elmundo/rss/portada.xml", "country": "ES"},
    {"name": "ABC Spain", "url": "https://www.abc.es/rss/feeds/abcPortada.xml", "country": "ES"},
    {"name": "La Vanguardia", "url": "https://www.lavanguardia.com/rss/home.xml", "country": "ES"},
    {"name": "RTVE", "url": "https://www.rtve.es/api/noticias.rss", "country": "ES"},
    
    # Portugal
    {"name": "Publico", "url": "https://feeds.feedburner.com/PublicoRSS", "country": "PT"},
    {"name": "Observador", "url": "https://observador.pt/feed/", "country": "PT"},
    {"name": "RTP", "url": "https://www.rtp.pt/noticias/rss", "country": "PT"},
    
    # Netherlands
    {"name": "NOS News", "url": "https://feeds.nos.nl/nosnieuwsalgemeen", "country": "NL"},
    {"name": "De Telegraaf", "url": "https://www.telegraaf.nl/rss", "country": "NL"},
    {"name": "AD", "url": "https://www.ad.nl/home/rss.xml", "country": "NL"},
    {"name": "NU.nl", "url": "https://www.nu.nl/rss/Algemeen", "country": "NL"},
    
    # Belgium
    {"name": "RTBF", "url": "https://rss.rtbf.be/article/rss/rtbfinfo_homepage.xml", "country": "BE"},
    {"name": "VRT", "url": "https://www.vrt.be/vrtnws/nl.rss.articles.xml", "country": "BE"},
    {"name": "Le Soir", "url": "https://www.lesoir.be/rss/cible_principale.xml", "country": "BE"},
    {"name": "HLN", "url": "https://www.hln.be/home/rss.xml", "country": "BE"},
    
    # Switzerland
    {"name": "SWI swissinfo", "url": "https://www.swissinfo.ch/eng/rss/top-news", "country": "CH"},
    {"name": "20 Minutes CH", "url": "https://www.20min.ch/rss/rss.tmpl?type=channel&get=1", "country": "CH"},
    {"name": "Blick", "url": "https://www.blick.ch/news/rss.xml", "country": "CH"},
    
    # Austria
    {"name": "ORF", "url": "https://rss.orf.at/news.xml", "country": "AT"},
    {"name": "Der Standard", "url": "https://www.derstandard.at/rss", "country": "AT"},
    {"name": "Kurier", "url": "https://kurier.at/xml/rssd", "country": "AT"},
    {"name": "Kronen Zeitung", "url": "https://www.krone.at/nachrichten/rss.html", "country": "AT"},
    
    # Ireland
    {"name": "RTE News", "url": "https://www.rte.ie/news/rss/news-headlines.xml", "country": "IE"},
    {"name": "Irish Times", "url": "https://www.irishtimes.com/cmlink/news-1.1319192", "country": "IE"},
    {"name": "Irish Independent", "url": "https://www.independent.ie/rss/", "country": "IE"},
    {"name": "The Journal IE", "url": "https://www.thejournal.ie/feed/", "country": "IE"},
    
    # ============================================
    # EUROPE - NORDIC
    # ============================================
    # Sweden
    {"name": "SVT Nyheter", "url": "https://www.svt.se/nyheter/rss.xml", "country": "SE"},
    {"name": "Aftonbladet", "url": "https://rss.aftonbladet.se/rss2/small/pages/sections/senastenytt/", "country": "SE"},
    {"name": "Dagens Nyheter", "url": "https://www.dn.se/rss/", "country": "SE"},
    {"name": "Expressen", "url": "https://feeds.expressen.se/nyheter/", "country": "SE"},
    {"name": "The Local Sweden", "url": "https://www.thelocal.se/feed/", "country": "SE"},
    
    # Norway
    {"name": "NRK", "url": "https://www.nrk.no/toppsaker.rss", "country": "NO"},
    {"name": "VG", "url": "https://www.vg.no/rss/feed", "country": "NO"},
    {"name": "Aftenposten", "url": "https://www.aftenposten.no/rss", "country": "NO"},
    {"name": "Dagbladet", "url": "https://www.dagbladet.no/rss", "country": "NO"},
    {"name": "The Local Norway", "url": "https://www.thelocal.no/feed/", "country": "NO"},
    
    # Denmark
    {"name": "DR Nyheder", "url": "https://www.dr.dk/nyheder/service/feeds/allenyheder", "country": "DK"},
    {"name": "TV2 Denmark", "url": "https://nyheder.tv2.dk/rss/seneste", "country": "DK"},
    {"name": "Jyllands-Posten", "url": "https://jyllands-posten.dk/rss/indland", "country": "DK"},
    {"name": "Politiken", "url": "https://politiken.dk/rss/senestenyt.rss", "country": "DK"},
    {"name": "The Local Denmark", "url": "https://www.thelocal.dk/feed/", "country": "DK"},
    
    # Finland
    {"name": "YLE News", "url": "https://feeds.yle.fi/uutiset/v1/majorHeadlines/YLE_NEWS.rss", "country": "FI"},
    {"name": "Helsinki Times", "url": "https://www.helsinkitimes.fi/feed", "country": "FI"},
    {"name": "Helsingin Sanomat", "url": "https://www.hs.fi/rss/tuoreimmat.xml", "country": "FI"},
    
    # Iceland
    {"name": "Iceland Monitor", "url": "https://icelandmonitor.mbl.is/rss/", "country": "IS"},
    {"name": "RUV", "url": "https://www.ruv.is/rss/frettir", "country": "IS"},
    
    # ============================================
    # EUROPE - EASTERN & CENTRAL
    # ============================================
    # Poland
    {"name": "TVN24", "url": "https://tvn24.pl/najnowsze.xml", "country": "PL"},
    {"name": "Gazeta Wyborcza", "url": "https://wiadomosci.gazeta.pl/pub/rss/wiadomosci.xml", "country": "PL"},
    {"name": "Onet", "url": "https://wiadomosci.onet.pl/.feed", "country": "PL"},
    {"name": "Polskie Radio", "url": "https://www.polskieradio.pl/7/129/Rss", "country": "PL"},
    {"name": "Notes from Poland", "url": "https://notesfrompoland.com/feed/", "country": "PL"},
    
    # Czech Republic
    {"name": "Aktualne.cz", "url": "https://www.aktualne.cz/rss/", "country": "CZ"},
    {"name": "iDNES", "url": "https://servis.idnes.cz/rss.aspx?c=zpravodaj", "country": "CZ"},
    {"name": "Radio Prague", "url": "https://english.radio.cz/rss", "country": "CZ"},
    {"name": "Prague Morning", "url": "https://www.praguemorning.cz/feed/", "country": "CZ"},
    
    # Hungary
    {"name": "Hungary Today", "url": "https://hungarytoday.hu/feed/", "country": "HU"},
    {"name": "Index.hu", "url": "https://index.hu/24ora/rss/", "country": "HU"},
    {"name": "Telex", "url": "https://telex.hu/rss", "country": "HU"},
    
    # Romania
    {"name": "Romania Insider", "url": "https://www.romania-insider.com/feed", "country": "RO"},
    {"name": "Digi24", "url": "https://www.digi24.ro/rss", "country": "RO"},
    {"name": "Hotnews", "url": "https://www.hotnews.ro/rss", "country": "RO"},
    
    # Bulgaria
    {"name": "Bulgaria Today", "url": "https://www.novinite.com/rss.php", "country": "BG"},
    {"name": "BNR", "url": "https://bnr.bg/en/rss", "country": "BG"},
    
    # Greece
    {"name": "Ekathimerini", "url": "https://www.ekathimerini.com/rss", "country": "GR"},
    {"name": "Greek Reporter", "url": "https://greekreporter.com/feed/", "country": "GR"},
    {"name": "Naftemporiki", "url": "https://www.naftemporiki.gr/feed/", "country": "GR"},
    
    # Ukraine
    {"name": "Kyiv Independent", "url": "https://kyivindependent.com/feed/", "country": "UA"},
    {"name": "Ukrinform", "url": "https://www.ukrinform.net/rss/block-lastnews", "country": "UA"},
    {"name": "Ukrainska Pravda", "url": "https://www.pravda.com.ua/eng/rss/", "country": "UA"},
    {"name": "UNIAN", "url": "https://www.unian.info/rss", "country": "UA"},
    
    # Russia (international perspective)
    {"name": "Moscow Times", "url": "https://www.themoscowtimes.com/rss/news", "country": "RU"},
    {"name": "TASS", "url": "https://tass.com/rss/v2.xml", "country": "RU"},
    {"name": "RT", "url": "https://www.rt.com/rss/", "country": "RU"},
    
    # Baltic States
    {"name": "LRT Lithuania", "url": "https://www.lrt.lt/en/rss", "country": "LT"},
    {"name": "LSM Latvia", "url": "https://eng.lsm.lv/rss/", "country": "LV"},
    {"name": "ERR Estonia", "url": "https://news.err.ee/rss", "country": "EE"},
    {"name": "Baltic Times", "url": "https://www.baltictimes.com/rss/", "country": None},
    
    # Balkans
    {"name": "N1 Serbia", "url": "https://rs.n1info.com/rss/", "country": "RS"},
    {"name": "N1 Croatia", "url": "https://hr.n1info.com/rss/", "country": "HR"},
    {"name": "N1 Bosnia", "url": "https://ba.n1info.com/rss/", "country": "BA"},
    {"name": "Balkan Insight", "url": "https://balkaninsight.com/feed/", "country": None},
    {"name": "Total Croatia News", "url": "https://www.total-croatia-news.com/feed", "country": "HR"},
    {"name": "Slovenia Times", "url": "https://sloveniatimes.com/feed/", "country": "SI"},
    {"name": "Exit News Albania", "url": "https://exit.al/en/feed/", "country": "AL"},
    {"name": "Kosovo 2.0", "url": "https://kosovotwopointzero.com/en/feed/", "country": "XK"},
    
    # ============================================
    # ASIA - EAST
    # ============================================
    # Japan
    {"name": "NHK World", "url": "https://www3.nhk.or.jp/rss/news/cat0.xml", "country": "JP"},
    {"name": "Japan Times", "url": "https://www.japantimes.co.jp/feed/", "country": "JP"},
    {"name": "Japan Today", "url": "https://japantoday.com/feed", "country": "JP"},
    {"name": "Nikkei Asia", "url": "https://asia.nikkei.com/rss/feed/nar", "country": "JP"},
    {"name": "Mainichi", "url": "https://mainichi.jp/english/rss", "country": "JP"},
    
    # South Korea
    {"name": "Yonhap News", "url": "https://en.yna.co.kr/RSS/news.xml", "country": "KR"},
    {"name": "Korea Herald", "url": "http://www.koreaherald.com/common/rss_xml.php?ct=102", "country": "KR"},
    {"name": "Korea Times", "url": "https://www.koreatimes.co.kr/www/rss/rss.xml", "country": "KR"},
    {"name": "Korea JoongAng Daily", "url": "https://koreajoongangdaily.joins.com/rss/", "country": "KR"},
    
    # China
    {"name": "CGTN", "url": "https://www.cgtn.com/rss/headline.xml", "country": "CN"},
    {"name": "China Daily", "url": "https://www.chinadaily.com.cn/rss/china_rss.xml", "country": "CN"},
    {"name": "Xinhua", "url": "http://www.xinhuanet.com/english/rss/worldrss.xml", "country": "CN"},
    {"name": "Global Times", "url": "https://www.globaltimes.cn/rss/", "country": "CN"},
    {"name": "Sixth Tone", "url": "https://www.sixthtone.com/rss", "country": "CN"},
    
    # Taiwan
    {"name": "Taipei Times", "url": "https://www.taipeitimes.com/xml/rss.xml", "country": "TW"},
    {"name": "Focus Taiwan", "url": "https://focustaiwan.tw/rss", "country": "TW"},
    {"name": "Taiwan News", "url": "https://www.taiwannews.com.tw/rss", "country": "TW"},
    
    # Hong Kong
    {"name": "SCMP", "url": "https://www.scmp.com/rss/91/feed", "country": "HK"},
    {"name": "HK Free Press", "url": "https://hongkongfp.com/feed/", "country": "HK"},
    {"name": "The Standard HK", "url": "https://www.thestandard.com.hk/rss_feed.php", "country": "HK"},
    
    # Mongolia
    {"name": "Montsame", "url": "https://montsame.mn/en/rss", "country": "MN"},
    {"name": "UB Post", "url": "https://theubpost.mn/feed/", "country": "MN"},
    
    # ============================================
    # ASIA - SOUTHEAST
    # ============================================
    # Singapore
    {"name": "CNA", "url": "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml", "country": "SG"},
    {"name": "Straits Times", "url": "https://www.straitstimes.com/rss.xml", "country": "SG"},
    {"name": "Today Singapore", "url": "https://www.todayonline.com/rss.xml", "country": "SG"},
    
    # Malaysia
    {"name": "The Star Malaysia", "url": "https://www.thestar.com.my/rss/News/Nation", "country": "MY"},
    {"name": "New Straits Times", "url": "https://www.nst.com.my/rss", "country": "MY"},
    {"name": "Malay Mail", "url": "https://www.malaymail.com/feed/rss/news", "country": "MY"},
    {"name": "Free Malaysia Today", "url": "https://www.freemalaysiatoday.com/feed/", "country": "MY"},
    
    # Indonesia
    {"name": "Jakarta Post", "url": "https://www.thejakartapost.com/rss.xml", "country": "ID"},
    {"name": "Tempo", "url": "https://en.tempo.co/rss", "country": "ID"},
    {"name": "Kompas", "url": "https://www.kompas.com/rss", "country": "ID"},
    {"name": "Antara News", "url": "https://www.antaranews.com/rss/terkini.xml", "country": "ID"},
    
    # Thailand
    {"name": "Bangkok Post", "url": "https://www.bangkokpost.com/rss/data/topstories.xml", "country": "TH"},
    {"name": "The Nation Thailand", "url": "https://www.nationthailand.com/rss/feed.xml", "country": "TH"},
    {"name": "Khaosod English", "url": "https://www.khaosodenglish.com/feed/", "country": "TH"},
    {"name": "Thai PBS", "url": "https://www.thaipbsworld.com/feed/", "country": "TH"},
    
    # Vietnam
    {"name": "VnExpress", "url": "https://e.vnexpress.net/rss/news.rss", "country": "VN"},
    {"name": "Tuoi Tre News", "url": "https://tuoitrenews.vn/rss/news.rss", "country": "VN"},
    {"name": "Vietnam News", "url": "https://vietnamnews.vn/rss/all.rss", "country": "VN"},
    {"name": "VietnamPlus", "url": "https://en.vietnamplus.vn/rss/news.rss", "country": "VN"},
    
    # Philippines
    {"name": "Inquirer", "url": "https://www.inquirer.net/feed", "country": "PH"},
    {"name": "Manila Bulletin", "url": "https://mb.com.ph/feed/", "country": "PH"},
    {"name": "Rappler", "url": "https://www.rappler.com/feed/", "country": "PH"},
    {"name": "ABS-CBN News", "url": "https://news.abs-cbn.com/rss", "country": "PH"},
    {"name": "GMA News", "url": "https://www.gmanetwork.com/news/rss/news", "country": "PH"},
    
    # Myanmar
    {"name": "Myanmar Now", "url": "https://www.myanmar-now.org/en/feed", "country": "MM"},
    {"name": "Irrawaddy", "url": "https://www.irrawaddy.com/feed", "country": "MM"},
    
    # Cambodia
    {"name": "Khmer Times", "url": "https://www.khmertimeskh.com/feed/", "country": "KH"},
    {"name": "Cambodia Daily", "url": "https://english.cambodiadaily.com/feed/", "country": "KH"},
    
    # ============================================
    # ASIA - SOUTH
    # ============================================
    # India
    {"name": "Times of India", "url": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms", "country": "IN"},
    {"name": "NDTV", "url": "https://feeds.feedburner.com/ndtvnews-top-stories", "country": "IN"},
    {"name": "The Hindu", "url": "https://www.thehindu.com/feeder/default.rss", "country": "IN"},
    {"name": "Indian Express", "url": "https://indianexpress.com/feed/", "country": "IN"},
    {"name": "Hindustan Times", "url": "https://www.hindustantimes.com/rss/topnews/rssfeed.xml", "country": "IN"},
    {"name": "Economic Times India", "url": "https://economictimes.indiatimes.com/rssfeedstopstories.cms", "country": "IN"},
    {"name": "Mint", "url": "https://www.livemint.com/rss/news", "country": "IN"},
    {"name": "The Wire India", "url": "https://thewire.in/feed", "country": "IN"},
    {"name": "Scroll India", "url": "https://scroll.in/feed", "country": "IN"},
    {"name": "News18", "url": "https://www.news18.com/rss/india.xml", "country": "IN"},
    
    # Pakistan
    {"name": "Dawn", "url": "https://www.dawn.com/feeds/home", "country": "PK"},
    {"name": "Geo News", "url": "https://www.geo.tv/rss/1/1", "country": "PK"},
    {"name": "Express Tribune", "url": "https://tribune.com.pk/feed/home", "country": "PK"},
    {"name": "The News International", "url": "https://www.thenews.com.pk/rss/1/1", "country": "PK"},
    {"name": "ARY News", "url": "https://arynews.tv/feed/", "country": "PK"},
    
    # Bangladesh
    {"name": "Daily Star BD", "url": "https://www.thedailystar.net/frontpage/rss.xml", "country": "BD"},
    {"name": "BDNews24", "url": "https://bdnews24.com/rss/rss.xml", "country": "BD"},
    {"name": "Dhaka Tribune", "url": "https://www.dhakatribune.com/rss.xml", "country": "BD"},
    {"name": "Prothom Alo", "url": "https://en.prothomalo.com/feed", "country": "BD"},
    
    # Sri Lanka
    {"name": "Daily Mirror LK", "url": "https://www.dailymirror.lk/RSS_Feeds/breaking-news/108", "country": "LK"},
    {"name": "Ceylon Today", "url": "https://ceylontoday.lk/feed/", "country": "LK"},
    {"name": "Colombo Gazette", "url": "https://colombogazette.com/feed/", "country": "LK"},
    
    # Nepal
    {"name": "Kathmandu Post", "url": "https://kathmandupost.com/rss", "country": "NP"},
    {"name": "Himalayan Times", "url": "https://thehimalayantimes.com/feed/", "country": "NP"},
    {"name": "Nepal News", "url": "https://www.nepalnews.com/rss", "country": "NP"},
    
    # Afghanistan
    {"name": "TOLOnews", "url": "https://tolonews.com/rss.xml", "country": "AF"},
    {"name": "Afghanistan Times", "url": "http://www.afghanistantimes.af/feed/", "country": "AF"},
    
    # ============================================
    # MIDDLE EAST & NORTH AFRICA
    # ============================================
    # Israel
    {"name": "Haaretz", "url": "https://www.haaretz.com/cmlink/1.4605706", "country": "IL"},
    {"name": "Jerusalem Post", "url": "https://www.jpost.com/Rss/RssFeedsHeadlines.aspx", "country": "IL"},
    {"name": "Times of Israel", "url": "https://www.timesofisrael.com/feed/", "country": "IL"},
    {"name": "Ynet", "url": "https://www.ynetnews.com/Integration/StoryRss2.xml", "country": "IL"},
    {"name": "i24 News", "url": "https://www.i24news.tv/en/rss", "country": "IL"},
    
    # Palestine
    {"name": "Wafa News", "url": "https://english.wafa.ps/rss.aspx", "country": "PS"},
    {"name": "Ma'an News", "url": "https://www.maannews.net/rss.aspx", "country": "PS"},
    {"name": "Palestine Chronicle", "url": "https://www.palestinechronicle.com/feed/", "country": "PS"},
    
    # Qatar (Al Jazeera)
    {"name": "Al Jazeera", "url": "https://www.aljazeera.com/xml/rss/all.xml", "country": "QA"},
    {"name": "Al Jazeera Middle East", "url": "https://www.aljazeera.com/xml/rss/2.xml", "country": None},
    
    # Saudi Arabia
    {"name": "Arab News", "url": "https://www.arabnews.com/rss.xml", "country": "SA"},
    {"name": "Saudi Gazette", "url": "https://saudigazette.com.sa/rss", "country": "SA"},
    {"name": "Al Arabiya", "url": "https://english.alarabiya.net/tools/rss", "country": "SA"},
    
    # UAE
    {"name": "Gulf News", "url": "https://gulfnews.com/rss", "country": "AE"},
    {"name": "Khaleej Times", "url": "https://www.khaleejtimes.com/rss", "country": "AE"},
    {"name": "The National UAE", "url": "https://www.thenationalnews.com/rss", "country": "AE"},
    {"name": "Emirates 24/7", "url": "https://www.emirates247.com/rss", "country": "AE"},
    
    # Lebanon
    {"name": "Daily Star Lebanon", "url": "https://www.dailystar.com.lb/RSS.aspx", "country": "LB"},
    {"name": "Naharnet", "url": "https://www.naharnet.com/rss.xml", "country": "LB"},
    {"name": "L'Orient Today", "url": "https://today.lorientlejour.com/rss", "country": "LB"},
    
    # Jordan
    {"name": "Jordan Times", "url": "https://jordantimes.com/rss.xml", "country": "JO"},
    {"name": "Petra News", "url": "http://petra.gov.jo/RSS.aspx", "country": "JO"},
    
    # Iraq
    {"name": "Iraq News", "url": "https://www.iraqinews.com/feed/", "country": "IQ"},
    {"name": "Rudaw", "url": "https://www.rudaw.net/english/rss", "country": "IQ"},
    {"name": "Kurdistan24", "url": "https://www.kurdistan24.net/en/rss", "country": "IQ"},
    
    # Iran
    {"name": "Tehran Times", "url": "https://www.tehrantimes.com/rss", "country": "IR"},
    {"name": "Press TV", "url": "https://www.presstv.ir/Rss", "country": "IR"},
    {"name": "IRNA", "url": "https://en.irna.ir/rss", "country": "IR"},
    
    # Turkey
    {"name": "Daily Sabah", "url": "https://www.dailysabah.com/rssFeed/", "country": "TR"},
    {"name": "Hurriyet Daily News", "url": "https://www.hurriyetdailynews.com/rss", "country": "TR"},
    {"name": "TRT World", "url": "https://www.trtworld.com/rss", "country": "TR"},
    {"name": "Ahval News", "url": "https://ahvalnews.com/rss.xml", "country": "TR"},
    
    # Egypt
    {"name": "Al-Ahram", "url": "https://english.ahram.org.eg/rss/index.aspx", "country": "EG"},
    {"name": "Egypt Independent", "url": "https://egyptindependent.com/feed/", "country": "EG"},
    {"name": "Daily News Egypt", "url": "https://dailynewsegypt.com/feed/", "country": "EG"},
    {"name": "Mada Masr", "url": "https://www.madamasr.com/en/feed/", "country": "EG"},
    
    # Morocco
    {"name": "Morocco World News", "url": "https://www.moroccoworldnews.com/feed/", "country": "MA"},
    {"name": "Maghreb Arab Press", "url": "https://www.mapnews.ma/en/rss.xml", "country": "MA"},
    
    # Tunisia
    {"name": "Tunisia Live", "url": "https://www.tunisia-live.net/feed/", "country": "TN"},
    {"name": "TAP News", "url": "https://www.tap.info.tn/en/rss.xml", "country": "TN"},
    
    # Algeria
    {"name": "Algeria Press Service", "url": "https://www.aps.dz/en/rss.xml", "country": "DZ"},
    {"name": "TSA Algeria", "url": "https://www.tsa-algerie.com/feed/", "country": "DZ"},
    
    # Libya
    {"name": "Libya Herald", "url": "https://libyaherald.com/feed/", "country": "LY"},
    {"name": "Libya Observer", "url": "https://www.libyaobserver.ly/rss.xml", "country": "LY"},
    
    # Syria
    {"name": "Syria Direct", "url": "https://syriadirect.org/feed/", "country": "SY"},
    {"name": "SANA", "url": "https://sana.sy/en/feed/", "country": "SY"},
    
    # Yemen
    {"name": "Yemen News Agency", "url": "https://www.sabanews.net/en/rss.xml", "country": "YE"},
    
    # ============================================
    # AFRICA - SUB-SAHARAN
    # ============================================
    # South Africa
    {"name": "News24 SA", "url": "https://feeds.news24.com/articles/news24/TopStories/rss", "country": "ZA"},
    {"name": "IOL", "url": "https://www.iol.co.za/cmlink/1.640", "country": "ZA"},
    {"name": "Mail & Guardian", "url": "https://mg.co.za/feed/", "country": "ZA"},
    {"name": "Daily Maverick", "url": "https://www.dailymaverick.co.za/feed/", "country": "ZA"},
    {"name": "Eyewitness News", "url": "https://ewn.co.za/RSS%20Feeds/Latest%20News", "country": "ZA"},
    {"name": "Times Live SA", "url": "https://www.timeslive.co.za/rss/", "country": "ZA"},
    
    # Nigeria
    {"name": "Punch Nigeria", "url": "https://punchng.com/feed/", "country": "NG"},
    {"name": "Guardian Nigeria", "url": "https://guardian.ng/feed/", "country": "NG"},
    {"name": "Premium Times", "url": "https://www.premiumtimesng.com/feed", "country": "NG"},
    {"name": "Vanguard Nigeria", "url": "https://www.vanguardngr.com/feed/", "country": "NG"},
    {"name": "The Cable", "url": "https://www.thecable.ng/feed", "country": "NG"},
    {"name": "Channels TV", "url": "https://www.channelstv.com/feed/", "country": "NG"},
    
    # Kenya
    {"name": "Daily Nation", "url": "https://nation.africa/kenya/rss.xml", "country": "KE"},
    {"name": "The Standard Kenya", "url": "https://www.standardmedia.co.ke/rss/", "country": "KE"},
    {"name": "Citizen Digital", "url": "https://www.citizen.digital/rss/", "country": "KE"},
    {"name": "Business Daily Kenya", "url": "https://www.businessdailyafrica.com/rss", "country": "KE"},
    
    # Ghana
    {"name": "Ghana Web", "url": "https://www.ghanaweb.com/GhanaHomePage/rss/", "country": "GH"},
    {"name": "Graphic Online", "url": "https://www.graphic.com.gh/feed", "country": "GH"},
    {"name": "Joy Online", "url": "https://www.myjoyonline.com/feed/", "country": "GH"},
    {"name": "Citi Newsroom", "url": "https://citinewsroom.com/feed/", "country": "GH"},
    
    # Ethiopia
    {"name": "Ethiopian Reporter", "url": "https://www.thereporterethiopia.com/rss.xml", "country": "ET"},
    {"name": "Addis Standard", "url": "https://addisstandard.com/feed/", "country": "ET"},
    {"name": "Fana BC", "url": "https://www.fanabc.com/english/feed/", "country": "ET"},
    
    # Tanzania
    {"name": "The Citizen TZ", "url": "https://www.thecitizen.co.tz/rss.xml", "country": "TZ"},
    {"name": "Daily News TZ", "url": "https://dailynews.co.tz/feed/", "country": "TZ"},
    
    # Uganda
    {"name": "Daily Monitor UG", "url": "https://www.monitor.co.ug/rss.xml", "country": "UG"},
    {"name": "New Vision", "url": "https://www.newvision.co.ug/rss/", "country": "UG"},
    
    # Rwanda
    {"name": "New Times Rwanda", "url": "https://www.newtimes.co.rw/rss.xml", "country": "RW"},
    {"name": "KT Press", "url": "https://www.ktpress.rw/feed/", "country": "RW"},
    
    # Zimbabwe
    {"name": "NewsDay Zimbabwe", "url": "https://www.newsday.co.zw/feed/", "country": "ZW"},
    {"name": "Zimbabwe Independent", "url": "https://www.theindependent.co.zw/feed/", "country": "ZW"},
    {"name": "Chronicle Zimbabwe", "url": "https://www.chronicle.co.zw/feed/", "country": "ZW"},
    
    # Zambia
    {"name": "Zambia Daily Mail", "url": "http://www.daily-mail.co.zm/feed/", "country": "ZM"},
    {"name": "Lusaka Times", "url": "https://www.lusakatimes.com/feed/", "country": "ZM"},
    
    # Botswana
    {"name": "Mmegi", "url": "https://www.mmegi.bw/rss.xml", "country": "BW"},
    {"name": "Sunday Standard BW", "url": "https://www.sundaystandard.info/feed", "country": "BW"},
    
    # Senegal
    {"name": "Seneweb", "url": "https://www.seneweb.com/rss", "country": "SN"},
    {"name": "APS Senegal", "url": "https://aps.sn/feed/", "country": "SN"},
    
    # Ivory Coast
    {"name": "Abidjan.net", "url": "https://news.abidjan.net/rss/", "country": "CI"},
    {"name": "Fraternite Matin", "url": "https://www.fratmat.info/feed/", "country": "CI"},
    
    # Cameroon
    {"name": "Journal du Cameroun", "url": "https://www.journalducameroun.com/feed/", "country": "CM"},
    {"name": "Cameroon Tribune", "url": "https://www.cameroon-tribune.cm/feed/", "country": "CM"},
    
    # Africa - Pan Continental
    {"name": "AllAfrica", "url": "https://allafrica.com/tools/headlines/rdf/latest/headlines.rdf", "country": None},
    {"name": "African Arguments", "url": "https://africanarguments.org/feed/", "country": None},
    {"name": "The Africa Report", "url": "https://www.theafricareport.com/feed/", "country": None},
    {"name": "Africa News", "url": "https://www.africanews.com/feed/", "country": None},
    
    # ============================================
    # OCEANIA
    # ============================================
    # Australia
    {"name": "ABC Australia", "url": "https://www.abc.net.au/news/feed/2942460/rss.xml", "country": "AU"},
    {"name": "ABC World", "url": "https://www.abc.net.au/news/feed/45910/rss.xml", "country": None},
    {"name": "Sydney Morning Herald", "url": "https://www.smh.com.au/rss/feed.xml", "country": "AU"},
    {"name": "The Age", "url": "https://www.theage.com.au/rss/feed.xml", "country": "AU"},
    {"name": "The Australian", "url": "https://www.theaustralian.com.au/feed/", "country": "AU"},
    {"name": "9 News Australia", "url": "https://www.9news.com.au/rss", "country": "AU"},
    {"name": "SBS News", "url": "https://www.sbs.com.au/news/feed", "country": "AU"},
    {"name": "News.com.au", "url": "https://www.news.com.au/feed/", "country": "AU"},
    
    # New Zealand
    {"name": "NZ Herald", "url": "https://www.nzherald.co.nz/arc/outboundfeeds/rss/curated/78/?outputType=xml", "country": "NZ"},
    {"name": "Stuff NZ", "url": "https://www.stuff.co.nz/rss", "country": "NZ"},
    {"name": "1 News NZ", "url": "https://www.1news.co.nz/rss/", "country": "NZ"},
    {"name": "Newshub", "url": "https://www.newshub.co.nz/home.rss", "country": "NZ"},
    {"name": "RNZ", "url": "https://www.rnz.co.nz/rss/national.xml", "country": "NZ"},
    
    # Pacific Islands
    {"name": "Fiji Times", "url": "https://www.fijitimes.com/feed/", "country": "FJ"},
    {"name": "Fiji Sun", "url": "https://fijisun.com.fj/feed/", "country": "FJ"},
    {"name": "PNG Post-Courier", "url": "https://postcourier.com.pg/feed/", "country": "PG"},
    {"name": "Samoa Observer", "url": "https://www.samoaobserver.ws/feed", "country": "WS"},
    {"name": "Pacific Islands News", "url": "https://pina.com.fj/feed/", "country": None},
    {"name": "RNZ Pacific", "url": "https://www.rnz.co.nz/rss/pacific.xml", "country": None},
    
    # ============================================
    # LATIN AMERICA & CARIBBEAN
    # ============================================
    # Brazil
    {"name": "Folha", "url": "https://feeds.folha.uol.com.br/emcimadahora/rss091.xml", "country": "BR"},
    {"name": "O Globo", "url": "https://oglobo.globo.com/rss.xml", "country": "BR"},
    {"name": "Estadao", "url": "https://www.estadao.com.br/rss/ultimas.xml", "country": "BR"},
    {"name": "G1", "url": "https://g1.globo.com/rss/g1/", "country": "BR"},
    {"name": "UOL", "url": "https://rss.uol.com.br/feed/noticias.xml", "country": "BR"},
    {"name": "Brazil Reports", "url": "https://brazilian.report/feed/", "country": "BR"},
    
    # Argentina
    {"name": "Clarin", "url": "https://www.clarin.com/rss/", "country": "AR"},
    {"name": "La Nacion AR", "url": "https://www.lanacion.com.ar/arc/outboundfeeds/rss/", "country": "AR"},
    {"name": "Infobae", "url": "https://www.infobae.com/feeds/rss/", "country": "AR"},
    {"name": "Pagina 12", "url": "https://www.pagina12.com.ar/rss/portada", "country": "AR"},
    {"name": "Buenos Aires Times", "url": "https://www.batimes.com.ar/feed", "country": "AR"},
    
    # Chile
    {"name": "El Mercurio", "url": "https://www.emol.com/rss/rss.asp", "country": "CL"},
    {"name": "La Tercera", "url": "https://www.latercera.com/feed/", "country": "CL"},
    {"name": "BioBioChile", "url": "https://www.biobiochile.cl/feed/", "country": "CL"},
    {"name": "Cooperativa", "url": "https://www.cooperativa.cl/noticias/rss/", "country": "CL"},
    
    # Colombia
    {"name": "El Tiempo", "url": "https://www.eltiempo.com/rss/", "country": "CO"},
    {"name": "El Espectador", "url": "https://www.elespectador.com/rss.xml", "country": "CO"},
    {"name": "Semana", "url": "https://www.semana.com/rss.xml", "country": "CO"},
    {"name": "Colombia Reports", "url": "https://colombiareports.com/feed/", "country": "CO"},
    
    # Peru
    {"name": "El Comercio Peru", "url": "https://elcomercio.pe/arcio/rss/", "country": "PE"},
    {"name": "La Republica Peru", "url": "https://larepublica.pe/rss/", "country": "PE"},
    {"name": "RPP Noticias", "url": "https://rpp.pe/feed", "country": "PE"},
    {"name": "Peru Reports", "url": "https://perureports.com/feed/", "country": "PE"},
    
    # Venezuela
    {"name": "El Nacional VE", "url": "https://www.elnacional.com/feed/", "country": "VE"},
    {"name": "El Universal VE", "url": "https://www.eluniversal.com/rss", "country": "VE"},
    {"name": "Efecto Cocuyo", "url": "https://efectococuyo.com/feed/", "country": "VE"},
    
    # Ecuador
    {"name": "El Comercio Ecuador", "url": "https://www.elcomercio.com/feed/", "country": "EC"},
    {"name": "El Universo", "url": "https://www.eluniverso.com/rss/", "country": "EC"},
    
    # Bolivia
    {"name": "Los Tiempos", "url": "https://www.lostiempos.com/rss.xml", "country": "BO"},
    {"name": "El Deber", "url": "https://eldeber.com.bo/rss", "country": "BO"},
    
    # Uruguay
    {"name": "El Pais Uruguay", "url": "https://www.elpais.com.uy/rss.xml", "country": "UY"},
    {"name": "El Observador UY", "url": "https://www.elobservador.com.uy/rss.xml", "country": "UY"},
    
    # Paraguay
    {"name": "ABC Color", "url": "https://www.abc.com.py/rss/", "country": "PY"},
    {"name": "Ultima Hora", "url": "https://www.ultimahora.com/rss.xml", "country": "PY"},
    
    # Central America
    {"name": "La Prensa Panama", "url": "https://www.prensa.com/rss.xml", "country": "PA"},
    {"name": "La Nacion Costa Rica", "url": "https://www.nacion.com/rss/", "country": "CR"},
    {"name": "Prensa Libre", "url": "https://www.prensalibre.com/feed/", "country": "GT"},
    {"name": "El Heraldo Honduras", "url": "https://www.elheraldo.hn/rss/", "country": "HN"},
    {"name": "El Faro", "url": "https://elfaro.net/es/rss/", "country": "SV"},
    {"name": "Confidencial Nicaragua", "url": "https://www.confidencial.com.ni/feed/", "country": "NI"},
    
    # Caribbean
    {"name": "Jamaica Observer", "url": "https://www.jamaicaobserver.com/feed/", "country": "JM"},
    {"name": "Jamaica Gleaner", "url": "https://jamaica-gleaner.com/feed", "country": "JM"},
    {"name": "Trinidad Guardian", "url": "https://www.guardian.co.tt/rss.xml", "country": "TT"},
    {"name": "Barbados Today", "url": "https://barbadostoday.bb/feed/", "country": "BB"},
    {"name": "Stabroek News", "url": "https://www.stabroeknews.com/feed/", "country": "GY"},
    {"name": "Dominican Today", "url": "https://dominicantoday.com/feed/", "country": "DO"},
    {"name": "Diario Libre", "url": "https://www.diariolibre.com/rss.xml", "country": "DO"},
    {"name": "Haiti Libre", "url": "https://www.haitilibre.com/en/rss.xml", "country": "HT"},
    {"name": "Cuba Headlines", "url": "https://www.cubaheadlines.com/feed", "country": "CU"},
    {"name": "Cubanet", "url": "https://www.cubanet.org/feed/", "country": "CU"},
    
    # ============================================
    # CENTRAL ASIA
    # ============================================
    {"name": "Akipress Kyrgyzstan", "url": "https://akipress.com/rss/", "country": "KG"},
    {"name": "Fergana News", "url": "https://fergana.agency/rss/", "country": None},
    {"name": "Tengri News Kazakhstan", "url": "https://en.tengrinews.kz/rss/", "country": "KZ"},
    {"name": "Asia Plus Tajikistan", "url": "https://asiaplustj.info/en/rss", "country": "TJ"},
    {"name": "Turkmenistan Chronicle", "url": "https://www.chroniclesoftk.com/feed/", "country": "TM"},
    {"name": "UzReport", "url": "https://uzreport.news/en/rss", "country": "UZ"},
    
    # ============================================
    # CAUCASUS
    # ============================================
    {"name": "Civil Georgia", "url": "https://civil.ge/rss", "country": "GE"},
    {"name": "JAM News", "url": "https://jam-news.net/feed/", "country": None},
    {"name": "OC Media", "url": "https://oc-media.org/feed/", "country": None},
    {"name": "EVN Report Armenia", "url": "https://evnreport.com/feed/", "country": "AM"},
    {"name": "Report Azerbaijan", "url": "https://report.az/en/rss/", "country": "AZ"},
]


class RSSCollector(BaseCollector):
    """Collector for RSS news feeds."""
    
    source_type = "rss"
    
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout, follow_redirects=True)
    
    def is_configured(self) -> bool:
        """RSS feeds don't require configuration."""
        return True
    
    async def collect(self) -> List[CollectedArticle]:
        """Collect articles from all RSS feeds."""
        articles = []
        
        for feed_config in RSS_FEEDS:
            try:
                feed_articles = await self._fetch_feed(feed_config)
                articles.extend(feed_articles)
                logger.info(
                    "Fetched RSS feed",
                    feed=feed_config["name"],
                    count=len(feed_articles)
                )
            except Exception as e:
                logger.warning(
                    "Failed to fetch RSS feed",
                    feed=feed_config["name"],
                    error=str(e)
                )
        
        return articles
    
    async def _fetch_feed(self, feed_config: dict) -> List[CollectedArticle]:
        """Fetch and parse a single RSS feed."""
        articles = []
        
        try:
            response = await self.client.get(feed_config["url"])
            response.raise_for_status()
            
            feed = feedparser.parse(response.text)
            
            for entry in feed.entries[:50]:  # Limit per feed
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
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                published_at = datetime.fromtimestamp(mktime(entry.updated_parsed))
            
            # Get country - try multiple methods
            country_code = feed_config.get("country")
            
            # If no country from feed config, try to get from source name
            if not country_code:
                country_code = get_country_from_source(feed_config["name"])
            
            # If still no country, detect from article text (title + content)
            if not country_code:
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
            logger.debug("Failed to parse RSS entry", error=str(e))
            return None
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
