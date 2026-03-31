# Sovereign Intelligence Engine

A unified ontology platform that aggregates data from 13+ public sources into a single object graph. Built with FastAPI, PostgreSQL (pgvector), React, and an AI agent powered by Claude.

![Dashboard](https://img.shields.io/badge/stack-FastAPI%20%2B%20React%20%2B%20PostgreSQL-blue)
![Python](https://img.shields.io/badge/python-3.12-green)
![Tests](https://img.shields.io/badge/tests-82%20passed-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)

## What it does

Sovereign takes 50 tech companies and enriches them from multiple public data sources — Wikipedia, GitHub, SEC EDGAR, Alpha Vantage, HuggingFace, Hacker News, and more. Every company becomes a unified object with properties merged from all sources, connected via a graph of relationships.

An AI agent (Claude) can query this live database using 11 tools — from ontology search to real-time market data and news.

```
User: "How does Apple's GitHub activity compare to Microsoft?"

Agent: [search_objects] → [compare_objects] → [get_links]

Apple:  580 repos, 20 linked repos, 4 sources
Microsoft: 4,800+ repos, GitHub org with 221k employees
...structured comparison with real data
```

## Architecture

```
Frontend (React + Vite)          Backend (FastAPI)           Jobs (ARQ Worker)
├── Dashboard                    ├── /objects                ├── sync_wikipedia
├── Graph Explorer (Dagre)       ├── /graph                  ├── sync_github
├── Search (autocomplete)        ├── /search + /suggest      ├── sync_alpha_vantage
├── AI Agent Chat                ├── /insights               ├── sync_sec
└── Tailwind "Sovereign" UI      ├── /sync                   ├── sync_huggingface
                                 └── /chat (WebSocket)       ├── sync_hn_algolia
                                                             └── compute_derived
Storage
├── PostgreSQL + pgvector (objects, links, embeddings)
├── Redis (API cache, job queue)
└── Raw Snapshots (every API response archived)
```

## Data Sources

| Source | Data | Auth |
|--------|------|------|
| Wikipedia | Descriptions, founding dates | None |
| GitHub | Repos, stars, forks, languages | Token (optional) |
| SEC EDGAR | Filings, CIK, SIC codes | None |
| Alpha Vantage | Market cap, PE, EPS, revenue, sector | Free key |
| HuggingFace | AI models, downloads, likes | None |
| HN Algolia | Tech articles, scores, comments | None |
| Forbes/Fortune 500 | Revenue, employees, rank | None |
| ArXiv | Academic papers | None |
| npm / PyPI | Package stats, downloads | None |
| FRED | Interest rates, GDP, inflation | Free key |
| EIA | Oil, gas, electricity prices | Free key |
| Google News | Real-time news (via Agent) | None |
| Yahoo Finance | Real-time quotes (via Agent) | None |

## Quick Start

### Prerequisites

- Docker & Docker Compose
- An Anthropic API key (for the AI agent)

### Setup

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/sovereign-ontology.git
cd sovereign-ontology

# Configure
cp .env.example .env
# Edit .env — add at minimum: ANTHROPIC_API_KEY

# Build & run
docker-compose up -d

# Wait for healthy containers, then seed data
curl -X POST http://localhost:8001/sync/wikipedia
curl -X POST http://localhost:8001/sync/github
curl -X POST http://localhost:8001/sync/sec
curl -X POST http://localhost:8001/sync/hn_algolia
curl -X POST http://localhost:8001/sync/huggingface
curl -X POST http://localhost:8001/sync/forbes
curl -X POST http://localhost:8001/sync/derived
```

### Access

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:5174 |
| API Docs (Swagger) | http://localhost:8001/docs |
| Graph Explorer | http://localhost:5174/graph |
| AI Agent | http://localhost:5174/chat |

## Agent Tools

The AI agent has 11 tools that query live data:

| Tool | What it does |
|------|-------------|
| `search_objects` | Full-text search across all ontology objects |
| `get_object` | Fetch complete object with all properties and sources |
| `get_links` | Traverse graph connections |
| `compare_objects` | Side-by-side comparison of multiple objects |
| `rank_objects` | Top-N ranking by any numeric property |
| `get_anomalies` | Find objects with missing data sources |
| `get_timeline` | Chronological events for a company |
| `get_market_data` | Live stock/commodity/crypto prices |
| `search_news` | Real-time news via Google News |
| `search_research` | ArXiv papers + HuggingFace models |
| `get_package_stats` | npm/PyPI package statistics |

## API Endpoints

```
GET  /objects                       List objects (filter by type, missing source)
GET  /objects/{key}                 Single object with all properties
GET  /objects/{key}/links           Connected objects
GET  /objects/{key}/timeline        Chronological events

GET  /graph?root={key}&depth=2      Subgraph for visualization
GET  /search?q={term}               Full-text search with relevance ranking
GET  /search/suggest?q={prefix}     Autocomplete suggestions

GET  /insights/stats                Dashboard KPIs
GET  /insights/trending             Companies by HN mentions + trend %
GET  /insights/top?metric=market_cap Top companies by metric
GET  /insights/anomalies            Missing source coverage
GET  /insights/movers               Recently updated companies
GET  /insights/stale?hours=24       Objects not synced recently

POST /sync/{source}                 Trigger manual sync
GET  /sync/sources                  List available sources

WS   /chat/ws                       Agent chat (WebSocket)
GET  /health                        Health check
```

## Project Structure

```
├── backend/
│   ├── api/
│   │   ├── main.py                 FastAPI app + lifespan
│   │   ├── deps.py                 Dependency injection
│   │   └── routes/
│   │       ├── objects.py          CRUD endpoints
│   │       ├── graph.py            Graph traversal
│   │       ├── search.py           Search + autocomplete
│   │       ├── insights.py         Trending, anomalies, stats
│   │       ├── sync.py             Manual sync triggers
│   │       ├── agent.py            11 tool definitions + agentic loop
│   │       └── chat.py             WebSocket endpoint
│   ├── connectors/                 15 data source connectors
│   ├── transform/
│   │   ├── mappers/                Object type mappers
│   │   ├── resolver.py             Entity resolution (fuzzy matching)
│   │   └── derived.py              Computed properties
│   ├── store/
│   │   ├── writer.py               Upsert objects/links
│   │   ├── reader.py               Query + graph traversal
│   │   └── cache.py                Redis response cache
│   ├── jobs/
│   │   ├── tasks.py                All sync tasks
│   │   └── worker.py               ARQ worker + cron schedule
│   ├── schemas/
│   │   ├── objects.py              Pydantic models
│   │   └── seed.py                 50 company definitions
│   ├── agents/
│   │   ├── docs_fetcher.py         API documentation collector
│   │   └── api_key_agent.py        Playwright MCP agent config
│   ├── db/init.sql                 PostgreSQL schema
│   └── tests/                      82 tests
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Layout.tsx          Sidebar navigation
│   │   │   ├── GraphView.tsx       React Flow + Dagre layout
│   │   │   ├── GraphFilterPanel.tsx Node/link type filters
│   │   │   ├── SearchBar.tsx       Autocomplete search
│   │   │   ├── ObjectCard.tsx      Object display card
│   │   │   ├── SourceBadge.tsx     Data source indicator
│   │   │   ├── ToolCallBadge.tsx   Agent tool call display
│   │   │   ├── Markdown.tsx        Markdown renderer
│   │   │   └── InsightsFeed.tsx    Anomaly feed
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx       KPIs, charts, trending
│   │   │   ├── Graph.tsx           Graph explorer
│   │   │   ├── Company.tsx         Company detail view
│   │   │   ├── Search.tsx          Search results
│   │   │   └── Chat.tsx            AI agent interface
│   │   ├── hooks/
│   │   │   ├── useOntology.ts      React Query hooks
│   │   │   └── useChat.ts          WebSocket chat hook
│   │   └── lib/api.ts              Typed API client
│   └── tailwind.config.js          "Sovereign" design system
├── docker-compose.yml
├── .env.example
└── README.md
```

## Testing

```bash
# Backend (82 tests)
docker exec ontology-backend-1 python -m pytest tests/ -v

# Frontend
docker exec ontology-frontend-1 npm test
```

## Optional API Keys

The platform works without any keys (Wikipedia, GitHub public API, SEC, HN are all free). For richer data:

| Key | What it unlocks | How to get |
|-----|----------------|------------|
| `GITHUB_TOKEN` | 5000 req/h (vs 60), all 50 companies | github.com/settings/tokens |
| `ALPHA_VANTAGE_KEY` | Market cap, PE ratio, revenue, sector | alphavantage.co (free, instant) |
| `ANTHROPIC_API_KEY` | AI agent chat | console.anthropic.com |
| `FRED_API_KEY` | Interest rates, GDP, inflation | fredaccount.stlouisfed.org (free) |
| `EIA_API_KEY` | Oil, gas, electricity prices | eia.gov/opendata (free) |

## Design System

The frontend uses the "Sovereign Intelligence" design language:
- Dark mode with atmospheric surface layers
- Space Grotesk + Inter typography
- No borders — tonal depth separation
- Color-coded entity types in graph visualization
- Glassmorphism for floating elements

## License

MIT
