-- Migration: Create sentiment tables for Supabase
-- Run this in Supabase SQL Editor: https://supabase.com/dashboard/project/ctvadyesxiwsteryqofy/sql

-- Create articles table
CREATE TABLE IF NOT EXISTS articles (
    id SERIAL PRIMARY KEY,
    source_type VARCHAR(20) NOT NULL,
    source_name VARCHAR(100) NOT NULL,
    country_code VARCHAR(2),
    title TEXT NOT NULL,
    content TEXT,
    url VARCHAR(2048) UNIQUE NOT NULL,
    sentiment_score FLOAT,
    sentiment_label VARCHAR(20),
    confidence FLOAT,
    published_at TIMESTAMP,
    analyzed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create indexes for articles
CREATE INDEX IF NOT EXISTS idx_articles_id ON articles(id);
CREATE INDEX IF NOT EXISTS idx_articles_country_code ON articles(country_code);
CREATE INDEX IF NOT EXISTS idx_articles_country_created ON articles(country_code, created_at);
CREATE INDEX IF NOT EXISTS idx_articles_source_created ON articles(source_type, created_at);

-- Create country_sentiment table
CREATE TABLE IF NOT EXISTS country_sentiment (
    id SERIAL PRIMARY KEY,
    country_code VARCHAR(2) NOT NULL,
    hour TIMESTAMP NOT NULL,
    avg_sentiment FLOAT NOT NULL,
    weighted_sentiment FLOAT,
    article_count INTEGER NOT NULL DEFAULT 0,
    top_positive_id INTEGER REFERENCES articles(id),
    top_negative_id INTEGER REFERENCES articles(id),
    UNIQUE(country_code, hour)
);

-- Create indexes for country_sentiment
CREATE INDEX IF NOT EXISTS idx_country_sentiment_id ON country_sentiment(id);
CREATE INDEX IF NOT EXISTS idx_country_sentiment_country_code ON country_sentiment(country_code);
CREATE INDEX IF NOT EXISTS idx_country_sentiment_hour ON country_sentiment(hour);
CREATE INDEX IF NOT EXISTS idx_country_sentiment_lookup ON country_sentiment(country_code, hour);

-- Create data_sources table
CREATE TABLE IF NOT EXISTS data_sources (
    id SERIAL PRIMARY KEY,
    source_type VARCHAR(20) NOT NULL,
    name VARCHAR(100) UNIQUE NOT NULL,
    url VARCHAR(2048) NOT NULL,
    country_code VARCHAR(2),
    credibility_score FLOAT DEFAULT 1.0,
    is_active INTEGER DEFAULT 1,
    last_fetched TIMESTAMP,
    fetch_error_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_data_sources_id ON data_sources(id);

-- Enable Row Level Security (optional, but recommended for production)
-- ALTER TABLE articles ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE country_sentiment ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE data_sources ENABLE ROW LEVEL SECURITY;

