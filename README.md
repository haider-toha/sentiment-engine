# Global Sentiment Engine

A real-time pipeline that ingests news and social data, runs sentiment analysis, and visualizes the emotional state of the world on an interactive 3D globe.

![Sentiment Engine](https://via.placeholder.com/800x400?text=Global+Sentiment+Engine)

## Features

- **Multi-source data ingestion**: RSS feeds, Reddit, Mastodon, Hacker News, and web scraping
- **GPU-accelerated sentiment analysis**: Using FinBERT transformer model
- **Interactive 3D globe**: Built with React Three Fiber
- **Country-level sentiment tracking**: See headlines and trends per country
- **Hourly aggregation**: Efficient batch processing and data retention
- **Minimal, modern UI**: Clean design that's easy on the eyes

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python, FastAPI, SQLAlchemy |
| Database | SQLite (zero-config) |
| ML | HuggingFace Transformers (FinBERT) |
| Scheduler | APScheduler |
| Frontend | Next.js 14, React Three Fiber |
| Styling | TailwindCSS, shadcn/ui patterns |

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- (Optional) NVIDIA GPU with CUDA for faster inference

### Backend Setup

```bash
cd backend

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload
```

The backend will start at `http://localhost:8000`. API docs available at `http://localhost:8000/docs`.

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.local.example .env.local

# Run development server
npm run dev
```

The frontend will start at `http://localhost:3000`.

## Configuration

### Backend Environment Variables

Create a `backend/.env` file:

```env
# Database (SQLite by default)
DATABASE_URL=sqlite:///./sentiment.db

# Reddit API (optional but recommended)
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=SentimentEngine/1.0

# Mastodon API (optional)
MASTODON_ACCESS_TOKEN=your_token
MASTODON_API_BASE_URL=https://mastodon.social

# ML Settings
USE_GPU=true  # Set to false for CPU-only
SENTIMENT_MODEL=ProsusAI/finbert
BATCH_SIZE=32

# Scheduler
COLLECTION_INTERVAL_HOURS=1

# Data retention
RETENTION_DAYS=30
```

### Getting API Keys

**Reddit:**
1. Go to https://www.reddit.com/prefs/apps
2. Create a new "script" application
3. Copy the client ID (under the app name) and secret

**Mastodon (optional):**
1. Go to your Mastodon instance settings
2. Development > New Application
3. Copy the access token

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Data Sources  │────>│  FastAPI Backend│────>│ Next.js Frontend│
│  RSS, Reddit,   │     │   + SQLite DB   │     │  3D Globe View  │
│  Mastodon, HN   │     │ + Sentiment ML  │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Data Flow

1. **Collection**: Every hour, the scheduler triggers data collection from all sources
2. **Analysis**: Collected articles are batch-processed through the sentiment model
3. **Aggregation**: Results are aggregated by country and stored
4. **Visualization**: The frontend fetches and displays data on the 3D globe

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check with system status |
| `/api/sentiment/global` | GET | All countries, current sentiment |
| `/api/sentiment/{country}` | GET | Country detail with 24h history |
| `/api/headlines/{country}` | GET | Top headlines for a country |
| `/api/trends` | GET | Global sentiment trends |
| `/api/collect/trigger` | POST | Manually trigger data collection |

## Deployment

### Render (Recommended)

**Backend:**
1. Create a new Web Service
2. Connect your GitHub repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables

**Frontend:**
1. Create a new Static Site
2. Set build command: `npm run build`
3. Set publish directory: `out`
4. Add `NEXT_PUBLIC_API_URL` environment variable

**Note:** SQLite works on Render but data resets on redeploy. For persistence, use Render's Disk ($7/month) or switch to PostgreSQL.

## Performance Notes

- **GPU Inference**: With an RTX 5070, expect ~100 articles/second batch processing
- **CPU Inference**: Slower but functional, ~5-10 articles/second
- **Memory**: The FinBERT model requires ~500MB RAM
- **Database**: SQLite handles ~10k articles/day easily

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - feel free to use this project for learning and building your own sentiment analysis tools.

