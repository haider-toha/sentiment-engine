# Global Sentiment Engine

A real-time NLP pipeline that ingests multilingual news and social content from 150+ countries, performs GPU-accelerated transformer-based sentiment analysis, aggregates results by country and time and visualizes global emotional state on an interactive WebGL 3D globe.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                DATA COLLECTION LAYER                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │   RSS    │ │  Reddit  │ │ Mastodon │ │  Hacker  │ │ Bluesky  │ │  Lemmy   │ │
│  │ 300+feeds│ │   PRAW   │ │   API    │ │   News   │ │  AT Proto│ │   API    │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ │
│       │            │            │            │            │            │        │
│       └────────────┴────────────┴─────┬──────┴────────────┴────────────┘        │
│                                       ▼                                          │
│                          ┌─────────────────────────┐                            │
│                          │   Article Normalizer    │                            │
│                          │  (Dedup, Country Detect)│                            │
│                          └───────────┬─────────────┘                            │
└──────────────────────────────────────┼──────────────────────────────────────────┘
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              PROCESSING LAYER                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                        Sentiment Analyzer                                │    │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │    │
│  │  │  Text Cleaner   │─▶│  XLM-RoBERTa    │─▶│  Label Normalizer       │  │    │
│  │  │  (URL, HTML,    │  │  (278M params)  │  │  (→ -1.0 to +1.0 scale) │  │    │
│  │  │   whitespace)   │  │  CUDA/CPU       │  │                         │  │    │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                                       │                                          │
│                                       ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                        Aggregation Engine                                │    │
│  │  • Hourly rollups by country                                             │    │
│  │  • Weighted averaging (source credibility)                               │    │
│  │  • Top positive/negative article tracking                                │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────┼──────────────────────────────────────────┘
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                               STORAGE LAYER                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                    SQLite / PostgreSQL                                   │    │
│  │  ┌─────────────────────┐        ┌─────────────────────────────────┐     │    │
│  │  │      articles       │        │      country_sentiment          │     │    │
│  │  ├─────────────────────┤        ├─────────────────────────────────┤     │    │
│  │  │ id (PK)             │        │ id (PK)                         │     │    │
│  │  │ url (UNIQUE, IDX)   │        │ country_code (IDX)              │     │    │
│  │  │ title               │        │ hour (IDX)                      │     │    │
│  │  │ content             │        │ avg_sentiment                   │     │    │
│  │  │ source_type (IDX)   │        │ weighted_sentiment              │     │    │
│  │  │ source_name         │        │ article_count                   │     │    │
│  │  │ country_code (IDX)  │        │ top_positive_id (FK)            │     │    │
│  │  │ sentiment_score     │        │ top_negative_id (FK)            │     │    │
│  │  │ sentiment_label     │        │ created_at                      │     │    │
│  │  │ published_at        │        └─────────────────────────────────┘     │    │
│  │  │ created_at (IDX)    │                                                │    │
│  │  └─────────────────────┘                                                │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────┼──────────────────────────────────────────┘
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                 API LAYER                                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         FastAPI (async)                                  │    │
│  │  GET  /api/health              → System status, model state              │    │
│  │  GET  /api/sentiment/global    → All countries, current scores           │    │
│  │  GET  /api/sentiment/{code}    → Country detail, 24h trend               │    │
│  │  GET  /api/headlines/{code}    → Paginated headlines, sentiment filter   │    │
│  │  GET  /api/trends              → Global hourly aggregates                │    │
│  │  GET  /api/sources             → Per-source statistics                   │    │
│  │  POST /api/collect/trigger     → Manual collection trigger               │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────┼──────────────────────────────────────────┘
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              PRESENTATION LAYER                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                     Next.js 14 + React Three Fiber                       │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │    │
│  │  │  3D Globe   │  │   Country   │  │  Headlines  │  │   Stats Bar     │ │    │
│  │  │  (Three.js) │  │   Panel     │  │   List      │  │   + Legend      │ │    │
│  │  │  WebGL 2.0  │  │  Sparklines │  │  Sentiment  │  │                 │ │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Technical Specifications

### Backend Stack

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Runtime | Python | 3.10+ | Async support, type hints |
| Framework | FastAPI | 0.109+ | Async HTTP, OpenAPI docs |
| Server | Uvicorn | 0.27+ | ASGI server, hot reload |
| ORM | SQLAlchemy | 2.0+ | Async database operations |
| Scheduler | APScheduler | 3.10+ | Background job scheduling |
| ML Framework | PyTorch | 2.0+ | Tensor computation, CUDA |
| NLP | Transformers | 4.37+ | Pre-trained model loading |
| HTTP Client | httpx | 0.26+ | Async HTTP requests |

### Frontend Stack

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Framework | Next.js | 14.x | React SSR, App Router |
| 3D Rendering | React Three Fiber | 8.x | Declarative Three.js |
| 3D Engine | Three.js | 0.160+ | WebGL rendering |
| Styling | TailwindCSS | 3.4+ | Utility-first CSS |
| State | SWR | 2.x | Data fetching, caching |
| Types | TypeScript | 5.x | Static type checking |

### Supported Sentiment Models

| Model | Parameters | Languages | Output Format | Use Case |
|-------|------------|-----------|---------------|----------|
| cardiffnlp/twitter-xlm-roberta-base-sentiment | 278M | 100+ | negative/neutral/positive | Default, multilingual news |
| cardiffnlp/twitter-roberta-base-sentiment-latest | 125M | English | negative/neutral/positive | High-accuracy English |
| nlptown/bert-base-multilingual-uncased-sentiment | 110M | 6 | 1-5 stars | Nuanced rating |
| ProsusAI/finbert | 110M | English | negative/neutral/positive | Financial news |
| siebert/sentiment-roberta-large-english | 355M | English | POSITIVE/NEGATIVE | Maximum accuracy |

---

## Data Collection Architecture

### Collector Interface

All collectors implement a common interface ensuring consistent data normalization:

```
BaseCollector (Abstract)
├── source_type: str           # Identifier (rss, reddit, mastodon, hn)
├── is_configured() → bool     # Check if required credentials exist
├── collect() → List[Article]  # Fetch and normalize articles
└── close()                    # Cleanup resources
```

### Collected Article Schema

```
CollectedArticle
├── source_type: str           # Origin collector type
├── source_name: str           # Specific source (e.g., "BBC News")
├── title: str                 # Article headline
├── url: str                   # Canonical URL (used for deduplication)
├── content: Optional[str]     # Body text or description
├── country_code: Optional[str]# ISO 3166-1 alpha-2 code
└── published_at: Optional[datetime]
```

### RSS Feed Coverage

**Wire Services (4)**: Reuters, AP, AFP, Euronews

**North America (17)**: NPR, PBS, NBC, CBS, ABC, USA Today, Washington Post, NY Post, The Hill, Politico, CBC, CTV, Global News, Toronto Star, National Post, Milenio, El Universal MX

**Europe - Western (45)**: BBC, Guardian, Sky, Telegraph, Independent, Daily Mail, Metro UK, France 24, Le Monde, Le Figaro, RFI, Deutsche Welle, Der Spiegel, Tagesschau, Die Zeit, FAZ, ANSA, La Repubblica, Corriere, El Pais, El Mundo, ABC Spain, NOS, De Telegraaf, RTBF, VRT, SWI, ORF, RTE, Irish Times...

**Europe - Nordic (18)**: SVT, Aftonbladet, DN, NRK, VG, DR, TV2 DK, YLE, Helsinki Times, Iceland Monitor...

**Europe - Eastern (30)**: TVN24, Gazeta Wyborcza, Aktualne.cz, Hungary Today, Romania Insider, Ekathimerini, Kyiv Independent, Moscow Times, Baltic Times, N1 Serbia/Croatia/Bosnia...

**Asia (65)**: NHK, Japan Times, Yonhap, CGTN, SCMP, CNA, Straits Times, Jakarta Post, Bangkok Post, Times of India, NDTV, Dawn, Daily Star BD...

**Middle East & Africa (55)**: Al Jazeera, Arab News, Haaretz, Jerusalem Post, Gulf News, Daily Sabah, News24 SA, Punch Nigeria, Daily Nation Kenya...

**Americas (40)**: Folha, Clarin, El Mercurio, El Tiempo, Jamaica Observer...

**Oceania (15)**: ABC Australia, NZ Herald, Fiji Times, RNZ Pacific...

**Total: 300+ RSS feeds across 150+ countries**

### Country Detection Pipeline

```
Article Text
     │
     ▼
┌─────────────────────────────────────────────────┐
│           Source-Based Attribution               │
│  (If source has known country → assign directly) │
└─────────────────────────┬───────────────────────┘
                          │ No match
                          ▼
┌─────────────────────────────────────────────────┐
│            Text-Based Detection                  │
│  1. Extract all country mentions                 │
│  2. Match against 200+ variations:               │
│     - Official names ("United States")           │
│     - Common names ("America")                   │
│     - Demonyms ("American", "Japanese")          │
│     - Major cities ("Tokyo" → JP)                │
│     - Local names ("Deutschland" → DE)           │
│  3. Count frequency, return most mentioned       │
└─────────────────────────────────────────────────┘
```

---

## Sentiment Analysis Pipeline

### Text Preprocessing

```
Raw Text
    │
    ├─► Remove URLs (https?://\S+)
    ├─► Strip HTML tags (<[^>]+>)
    ├─► Remove hashtags/mentions ([#@]\w+)
    ├─► Normalize whitespace (\s+ → single space)
    ├─► Preserve Unicode (multilingual support)
    └─► Truncate to 512 tokens (model max context)
```

### Inference Pipeline

```
Cleaned Text
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    HuggingFace Pipeline                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │  Tokenizer  │───▶│   Model     │───▶│  Softmax Output     │  │
│  │  (BPE/SPM)  │    │  (Forward)  │    │  [{label, score}]   │  │
│  └─────────────┘    └─────────────┘    └─────────────────────┘  │
│         │                  │                      │              │
│    Subword tokens     Hidden states         Probabilities        │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Label Normalization                           │
│  Model Output          →    Normalized                          │
│  ─────────────────────────────────────────                      │
│  "LABEL_0" (0.85)      →    score: -0.85, label: "negative"     │
│  "positive" (0.72)     →    score: +0.72, label: "positive"     │
│  "3 stars" (0.60)      →    score: 0.00,  label: "neutral"      │
│  "5 stars" (0.91)      →    score: +0.91, label: "positive"     │
└─────────────────────────────────────────────────────────────────┘
```

### Batch Processing

Single inference is inefficient. The system batches articles for GPU parallelization:

```
Articles[0..N]
      │
      ▼
┌─────────────────────────────────────┐
│  Batch Formation (size=32 default)  │
│  Filter articles with len >= 10     │
│  Track original indices for mapping │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│  GPU Batch Inference                │
│  • Pad to max length in batch       │
│  • Single forward pass              │
│  • Return all predictions           │
└─────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────┐
│  Result Mapping                     │
│  Map predictions back to articles   │
│  Handle None for filtered articles  │
└─────────────────────────────────────┘
```

---

## Aggregation System

### Source Credibility Weights

```
Source Type    Weight    Rationale
───────────────────────────────────────────────────
rss            1.0       Established news outlets
scraper        0.9       Direct news site extraction
hn             0.8       Curated tech community
reddit         0.6       Mixed user-generated content
mastodon       0.5       Social media, lower signal
```

### Weighted Sentiment Calculation

```
                    Σ (sentiment_score × source_weight)
Weighted Average = ─────────────────────────────────────
                         Σ source_weight
```

### Hourly Aggregation Output

```
CountrySentiment
├── country_code: str          # ISO 3166-1 alpha-2
├── hour: datetime             # Truncated to hour
├── avg_sentiment: float       # Simple mean
├── weighted_sentiment: float  # Credibility-weighted mean
├── article_count: int         # Articles in this hour
├── top_positive_id: int       # FK to most positive article
└── top_negative_id: int       # FK to most negative article
```

---

## API Specification

### GET /api/health

Returns system health status.

**Response Schema:**
```
{
  status: "healthy" | "degraded",
  last_collection: ISO8601 | null,
  articles_today: int,
  model_loaded: bool,
  database_ok: bool
}
```

### GET /api/sentiment/global

Returns current sentiment for all countries.

**Response Schema:**
```
{
  countries: [
    {
      country_code: str,      # "US", "GB", "JP"
      country_name: str,      # "United States"
      sentiment_score: float, # -1.0 to +1.0
      article_count: int
    }
  ],
  global_average: float,      # Weighted global mean
  total_articles: int,
  last_updated: ISO8601
}
```

### GET /api/sentiment/{country_code}

Returns detailed sentiment data for a country.

**Parameters:**
- `country_code`: ISO 3166-1 alpha-2 (e.g., "US", "GB")
- `hours`: int (default: 24) - Hours of trend data

**Response Schema:**
```
{
  country_code: str,
  country_name: str,
  current_sentiment: float,
  article_count: int,
  hourly_trend: [
    {
      hour: ISO8601,
      sentiment: float,
      articles: int
    }
  ],
  top_headlines: [
    {
      id: int,
      title: str,
      source_name: str,
      source_type: str,
      sentiment_score: float,
      sentiment_label: str,
      published_at: ISO8601,
      url: str
    }
  ],
  source_breakdown: {
    "rss": int,
    "reddit": int,
    ...
  }
}
```

### GET /api/headlines/{country_code}

Returns paginated headlines with optional sentiment filter.

**Parameters:**
- `limit`: int (default: 20)
- `sentiment`: "positive" | "negative" | "neutral" | null

**Sentiment Filter Thresholds:**
- Positive: score > 0.2
- Negative: score < -0.2
- Neutral: -0.2 ≤ score ≤ 0.2

---

## Frontend Architecture

### Component Hierarchy

```
App (Next.js App Router)
└── page.tsx
    └── Dashboard
        ├── StatsBar              # Global stats, last update
        ├── Legend                # Color scale explanation
        ├── GlobeWrapper          # Client-side boundary
        │   └── Globe             # Three.js canvas
        │       ├── EarthSphere   # Textured sphere
        │       ├── CountryMarkers# Sentiment-colored dots
        │       └── OrbitControls # User interaction
        ├── CountryList           # Sidebar country list
        └── CountryPanel          # Detail slide-in panel
            ├── SentimentCard     # Current score display
            ├── TrendSparkline    # 24h SVG chart
            ├── SourceBreakdown   # Bar chart
            └── HeadlinesList     # Scrollable headlines
```

### Globe Rendering Pipeline

```
Country Data
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│  Lat/Long → 3D Position                                      │
│  ─────────────────────────────────────────────────────────  │
│  φ = (90 - lat) × (π/180)                                   │
│  θ = (lon + 180) × (π/180)                                  │
│  x = -radius × sin(φ) × cos(θ)                              │
│  y = radius × cos(φ)                                        │
│  z = radius × sin(φ) × sin(θ)                               │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│  Sentiment → Color                                           │
│  ─────────────────────────────────────────────────────────  │
│  score < -0.3  →  #ef4444 (red)                             │
│  score < 0.0   →  interpolate red → amber                   │
│  score = 0.0   →  #f59e0b (amber)                           │
│  score < 0.3   →  interpolate amber → green                 │
│  score >= 0.3  →  #22c55e (green)                           │
└─────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────┐
│  Three.js Mesh                                               │
│  ─────────────────────────────────────────────────────────  │
│  <sphereGeometry args={[scale, 16, 16]} />                  │
│  <meshStandardMaterial                                       │
│    color={sentimentColor}                                    │
│    emissive={sentimentColor}                                 │
│    emissiveIntensity={hovered ? 0.6 : 0.3}                  │
│  />                                                          │
└─────────────────────────────────────────────────────────────┘
```

### Data Fetching Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                         SWR Config                           │
│  ─────────────────────────────────────────────────────────  │
│  refreshInterval: 60000ms (1 minute)                         │
│  revalidateOnFocus: true                                     │
│  dedupingInterval: 5000ms                                    │
│  errorRetryCount: 3                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Performance Characteristics

### Throughput Benchmarks

| Operation | GPU (RTX 5070) | CPU (12-core) |
|-----------|----------------|---------------|
| Single inference | 15ms | 150ms |
| Batch (32 articles) | 80ms | 2400ms |
| Effective rate | ~400 articles/sec | ~13 articles/sec |

### Collection Timing

| Source | Typical Duration | Articles |
|--------|------------------|----------|
| RSS (300+ feeds) | 2-5 minutes | 2000-5000 |
| Reddit | 30-60 seconds | 100-500 |
| Hacker News | 10-20 seconds | 50-100 |
| Total cycle | 3-7 minutes | 2000-6000 |

### Resource Usage

| Resource | Idle | Collection | Inference |
|----------|------|------------|-----------|
| CPU | <5% | 20-40% | 10-30% |
| RAM | 1.2GB | 1.5GB | 1.8GB |
| GPU Memory | 500MB | 500MB | 800MB |
| Network | ~0 | 5-20 Mbps | ~0 |

### Database Growth

| Metric | Value |
|--------|-------|
| Average article size | ~2KB |
| Articles per hour | 1000-3000 |
| Daily storage | 50-150MB |
| 30-day retention | 1.5-4.5GB |
| Aggregates overhead | <1% |

---

## Configuration Reference

### Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DB_USER` | string | - | PostgreSQL username |
| `DB_PASSWORD` | string | - | PostgreSQL password |
| `DB_HOST` | string | - | PostgreSQL host |
| `DB_PORT` | int | 6543 | PostgreSQL port |
| `DB_NAME` | string | postgres | Database name |
| `REDDIT_CLIENT_ID` | string | - | Reddit API client ID |
| `REDDIT_CLIENT_SECRET` | string | - | Reddit API secret |
| `REDDIT_USER_AGENT` | string | SentimentEngine/1.0 | Reddit user agent |
| `MASTODON_ACCESS_TOKEN` | string | - | Mastodon API token |
| `MASTODON_API_BASE_URL` | string | https://mastodon.social | Instance URL |
| `USE_GPU` | bool | true | Enable CUDA inference |
| `SENTIMENT_MODEL` | string | cardiffnlp/twitter-xlm-roberta-base-sentiment | HuggingFace model ID |
| `BATCH_SIZE` | int | 32 | Inference batch size |
| `COLLECTION_INTERVAL_HOURS` | int | 1 | Hours between collections |
| `RETENTION_DAYS` | int | 30 | Data retention period |

### Fallback Behavior

- If PostgreSQL credentials missing → Falls back to SQLite
- If Reddit credentials missing → Skip Reddit collection
- If Mastodon credentials missing → Skip Mastodon collection
- If GPU unavailable → Falls back to CPU inference
- If model load fails → API returns degraded status

---

## Error Handling

### Collection Failures

```
┌─────────────────────────────────────────────────────────────┐
│  Per-source isolation: one source failure doesn't stop job  │
│  Automatic retry: 3 attempts with exponential backoff       │
│  Timeout: 30 seconds per source                             │
│  Logging: structured JSON logs with source context          │
└─────────────────────────────────────────────────────────────┘
```

### Inference Failures

```
┌─────────────────────────────────────────────────────────────┐
│  Text too short (<10 chars): return None, skip article      │
│  Model exception: log error, return None for article        │
│  Batch failure: fall back to individual processing          │
│  OOM: reduce batch size dynamically                         │
└─────────────────────────────────────────────────────────────┘
```

### API Error Responses

| Status | Condition |
|--------|-----------|
| 200 | Success |
| 404 | Country not found / no data |
| 500 | Database error / internal failure |
| 503 | Model not loaded / service degraded |

---

## Monitoring & Observability

### Structured Logging

All logs are JSON-formatted via `structlog` for easy parsing:

```
{
  "timestamp": "2025-12-25T12:00:00Z",
  "level": "info",
  "event": "Fetched RSS feed",
  "feed": "BBC News",
  "count": 35,
  "duration_ms": 1250
}
```

### Key Metrics

- `articles_collected_total` - Counter by source
- `sentiment_inference_duration_seconds` - Histogram
- `collection_job_duration_seconds` - Histogram
- `active_countries` - Gauge
- `database_size_bytes` - Gauge

### Health Check Indicators

| Check | Healthy | Degraded |
|-------|---------|----------|
| Scheduler | Running | Stopped |
| Model | Loaded | Failed to load |
| Database | Connected | Connection failed |
| Last collection | < 2 hours ago | > 2 hours ago |

---

## Security Considerations

### Input Validation

- URL deduplication prevents duplicate processing
- Text length limits prevent memory exhaustion
- Country codes validated against ISO 3166-1

### API Security

- CORS configured for allowed origins
- Rate limiting recommended for production
- No authentication required (read-only public data)

### Credential Management

- All secrets via environment variables
- Never logged or exposed in API responses
- `.env` file excluded from version control

---

## Limitations

### Technical Constraints

- **Model accuracy**: ~85% on standard benchmarks; sarcasm and cultural context remain challenging
- **Language coverage**: While XLM-RoBERTa supports 100+ languages, accuracy varies; best for high-resource languages
- **Real-time latency**: 1-hour collection interval; breaking news delayed up to 60 minutes
- **Geographic granularity**: Country-level only; no city or region subdivision

### Data Constraints

- **Source availability**: RSS feeds may block, rate-limit, or discontinue without notice
- **Attribution ambiguity**: Articles covering multiple countries assigned to most-mentioned
- **Bias propagation**: Model inherits biases from training data
- **Coverage gaps**: Some countries have minimal English-language sources

---

## License

MIT License — Use freely for learning, experimentation and building derivative works.
