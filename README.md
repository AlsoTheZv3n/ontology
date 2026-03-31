# Sovereign Intelligence Engine

A knowledge graph platform that aggregates 50 tech companies from 20+ public data sources into a unified ontology with AI agent, ML anomaly detection, and real-time market data.

![Stack](https://img.shields.io/badge/stack-FastAPI%20%2B%20React%20%2B%20PostgreSQL-blue)
![Python](https://img.shields.io/badge/python-3.12-green)
![Tests](https://img.shields.io/badge/tests-129%20passed-brightgreen)
![Sources](https://img.shields.io/badge/data%20sources-20+-orange)
![License](https://img.shields.io/badge/license-MIT-blue)

## What it does

Sovereign takes 50 tech companies and enriches them from 8+ data sources — Wikipedia, GitHub, SEC EDGAR/XBRL, Alpha Vantage, Wikidata, HuggingFace, Hacker News, and Forbes. Each company becomes a unified object with merged properties, connected via a knowledge graph of relationships (CEO links, competitor links, article mentions, repo ownership).

An AI agent (Claude) queries this live database using 14 tools — ontology search, real-time market data, news, research papers, and ML-powered anomaly detection.

```
User: "Which AI companies have the most GitHub activity and how does
       that correlate with their HuggingFace model output?"

Agent: [search_objects] → [compare_objects] → [rank_objects]

Google:     4800 repos, 20 HF models, 580k followers
Microsoft:  4200 repos, 20 HF models, 221k followers
Meta:       1200 repos, 20 HF models, facebookresearch
...structured comparison with real data from live DB
```

## Architecture

```
Frontend (React + Vite)           Backend (FastAPI)              Jobs (ARQ Worker)
├── Dashboard (KPIs, trending)    ├── /objects (CRUD)            ├── sync_wikipedia
├── Feed (live event stream)      ├── /graph (traversal)         ├── sync_github
├── Graph (Cytoscape.js)          ├── /search + /suggest         ├── sync_sec + sec_financials
├── Search (autocomplete)         ├── /insights (15 endpoints)   ├── sync_alpha_vantage
├── Agent (Claude chat)           ├── /sync (20 sources)         ├── sync_wikidata
├── Markets (macro + commodities) ├── /chat (WebSocket)          ├── sync_huggingface
├── Entities (type browser)       └── ML endpoints               ├── sync_hn_algolia
├── Schema (ontology viz)                                        ├── compute_sentiment
└── Alerts (Z-score anomalies)    Storage                        ├── compute_embeddings
                                  ├── PostgreSQL + pgvector       ├── compute_clusters
                                  ├── Redis (cache + queue)       └── extract_persons
                                  └── Raw Snapshots
```

## Key Numbers

| Metric | Value |
|--------|-------|
| Companies | 53 (50 seeded + 3 from Forbes) |
| Total Objects | 2,900+ (companies, persons, articles, repos, events, macro indicators) |
| Total Links | 3,200+ |
| Object Types | 7 (company, person, article, repository, event, macro_indicator, country) |
| Link Types | 5 active (mentions, owns_repo, filed, is_ceo_of, competitor_of) |
| Data Sources | 8 on companies (Wikipedia, SEC, GitHub, Alpha Vantage, Wikidata, HuggingFace, Forbes, SEC XBRL) |
| Persons | 26 CEOs extracted |
| Competitor Links | 345 (SIC + sector + 11 industry clusters) |
| Agent Tools | 14 |
| Tests | 129 |

## Data Sources

| Source | Data | Auth | Status |
|--------|------|------|--------|
| Wikipedia | Descriptions, founding dates, HQ | None | Live |
| Wikidata SPARQL | CEOs, founders, employees, founding year | None | Live |
| GitHub | Repos, stars, forks, followers | Token (optional) | Live |
| SEC EDGAR | Filings, CIK, SIC codes, executives | None | Live |
| SEC XBRL | Revenue, net income, assets, R&D, EPS | None | Live |
| Alpha Vantage | Market cap, PE, EPS, revenue, sector | Free key | Live |
| HuggingFace | AI models, downloads, likes | None | Live |
| HN Algolia | Tech articles with scores, comments | None | Live |
| Forbes/Fortune 500 | Revenue, employees, rank | None | Live (local CSV) |
| ArXiv | Academic papers (XML) | None | Ready |
| npm / PyPI | Package stats, downloads | None | Ready |
| World Bank | GDP, inflation, unemployment (10 countries) | None | Live |
| Semantic Scholar | Research papers, citations | None | Ready |
| REST Countries | 250 countries with borders, population | None | Ready |
| GDELT | Global news intelligence | None | Ready |
| Commodities | Gold, silver, copper spot prices | None | Ready |
| FRED | Interest rates, GDP, inflation | Free key | Ready |
| EIA | Oil, gas, electricity prices | Free key | Ready |
| Google News | Real-time news (via Agent) | None | Live |
| Yahoo Finance | Real-time quotes (via Agent) | None | Live |

## Quick Start

### Prerequisites

- Docker & Docker Compose
- An Anthropic API key (for the AI agent)

### Setup

```bash
# Clone
git clone https://github.com/AlsoTheZv3n/ontology.git
cd ontology

# Configure
cp .env.example .env
# Edit .env — add at minimum: ANTHROPIC_API_KEY

# Build & run
docker-compose up -d

# Wait for healthy containers (~30s), then seed data
curl -X POST http://localhost:8001/sync/wikipedia
curl -X POST http://localhost:8001/sync/sec
curl -X POST http://localhost:8001/sync/sec_financials
curl -X POST http://localhost:8001/sync/hn_algolia
curl -X POST http://localhost:8001/sync/huggingface
curl -X POST http://localhost:8001/sync/wikidata
curl -X POST http://localhost:8001/sync/forbes
curl -X POST http://localhost:8001/sync/persons
curl -X POST http://localhost:8001/sync/competitors
curl -X POST http://localhost:8001/sync/derived
curl -X POST http://localhost:8001/sync/clusters
```

If you have an Alpha Vantage key (free, instant):
```bash
curl -X POST http://localhost:8001/sync/yahoo_finance
```

### Access

| Page | URL | Description |
|------|-----|-------------|
| Dashboard | http://localhost:5174 | KPIs, trending, source coverage |
| Feed | http://localhost:5174/feed | Live event stream |
| Graph | http://localhost:5174/graph | Cytoscape network explorer |
| Search | http://localhost:5174/search | Autocomplete + relevance ranking |
| Agent | http://localhost:5174/chat | Claude AI with 14 tools |
| Markets | http://localhost:5174/markets | Macro indicators + company financials |
| Entities | http://localhost:5174/entities | Browse by object type |
| Schema | http://localhost:5174/schema | Ontology link types visualization |
| Alerts | http://localhost:5174/alerts | Z-score anomaly detection |
| API Docs | http://localhost:8001/docs | Swagger/OpenAPI |

## Agent Tools

The AI agent has 14 tools that query live data:

| Tool | What it does |
|------|-------------|
| `search_objects` | Full-text search across all ontology objects |
| `get_object` | Fetch complete object with all properties and sources |
| `get_links` | Traverse graph connections |
| `compare_objects` | Side-by-side comparison of multiple objects |
| `rank_objects` | Top-N ranking by any numeric property |
| `get_anomalies` | Find objects with missing data sources |
| `get_timeline` | Chronological events for a company |
| `get_market_data` | Live stock/commodity/crypto prices (Yahoo Finance chart API) |
| `search_news` | Real-time news via Google News RSS |
| `search_research` | ArXiv papers + HuggingFace models |
| `get_package_stats` | npm/PyPI package statistics |
| `get_sentiment_trend` | FinBERT sentiment from company articles |
| `get_clusters` | K-Means company groupings by financial/tech profile |
| `detect_anomalies_metric` | Z-score anomalies for any metric |

## ML Pipeline

| Module | What it does | Status |
|--------|-------------|--------|
| `ml/analytics.py` | K-Means clustering, Z-score anomaly detection, linear forecasting | **Live** (scikit-learn) |
| `ml/finbert.py` | Financial sentiment: positive/negative/neutral | Ready (needs `transformers`) |
| `ml/ner.py` | Named entity recognition: persons, orgs, locations | Ready (needs `spacy`) |
| `ml/embeddings.py` | 384-dim vectors for pgvector similarity search | Ready (needs `sentence-transformers`) |

All modules gracefully degrade — the system never crashes if models aren't installed.

To enable heavy ML models:
```bash
# Uncomment in requirements.txt, then:
docker-compose build backend   # ~15 min (downloads models)
docker-compose up -d backend worker
curl -X POST http://localhost:8001/sync/sentiment
curl -X POST http://localhost:8001/sync/embeddings
```

## API Endpoints

```
Objects & Graph
  GET  /objects                         List objects (filter by type, missing source)
  GET  /objects/{key}                   Single object with all properties
  GET  /objects/{key}/links             Connected objects with labels
  GET  /objects/{key}/timeline          Chronological events
  GET  /graph?root={key}&depth=2        Subgraph for visualization

Search
  GET  /search?q={term}                 Relevance-ranked search
  GET  /search/suggest?q={prefix}       Autocomplete suggestions
  GET  /search/similar/{key}            pgvector similarity search

Insights
  GET  /insights/stats                  Dashboard KPIs + source coverage
  GET  /insights/trending               Companies by HN mentions + trend %
  GET  /insights/top?metric=market_cap  Top companies by metric
  GET  /insights/anomalies              Missing source coverage
  GET  /insights/movers                 Recently updated companies
  GET  /insights/stale?hours=24         Objects not synced recently
  GET  /insights/feed                   Live event stream
  GET  /insights/schema                 Ontology link types + counts
  GET  /insights/entities?type=company  Browse entities by type
  GET  /insights/markets                Macro indicators + company financials
  GET  /insights/alerts                 Z-score anomaly alerts
  GET  /insights/clusters               K-Means company clusters
  GET  /insights/sentiment/{key}        Article sentiment trend
  GET  /insights/forecast/{key}/{metric} Linear forecast

Sync
  POST /sync/{source}                   Trigger sync (20 sources available)
  GET  /sync/sources                    List all sources

Chat
  WS   /chat/ws                         Agent chat (WebSocket)
  GET  /health                          Health check
```

## Project Structure

```
├── backend/
│   ├── api/routes/                  7 route modules (objects, graph, search, insights, sync, agent, chat)
│   ├── connectors/                  20 data source connectors
│   ├── transform/
│   │   ├── mappers/                 5 object type mappers (company, person, article, repo, event)
│   │   ├── resolver.py              Entity resolution (fuzzy matching, iterative suffix stripping)
│   │   ├── derived.py               Innovation score, source coverage
│   │   ├── person_extractor.py      CEO extraction from company properties
│   │   └── competitor_resolver.py   SIC + sector + 11 industry cluster matching
│   ├── ml/
│   │   ├── analytics.py             K-Means, Z-score anomalies, linear forecast (scikit-learn)
│   │   ├── finbert.py               Financial sentiment (FinBERT, optional)
│   │   ├── ner.py                   Named entity recognition (spaCy, optional)
│   │   └── embeddings.py            Sentence embeddings (MiniLM, optional)
│   ├── store/                       Writer (upsert), Reader (queries + graph BFS), Cache (Redis)
│   ├── jobs/                        ARQ worker with 20 sync tasks + 3 ML tasks + cron schedule
│   ├── schemas/                     Pydantic models + 50 company seed data
│   ├── agents/                      API docs fetcher + Playwright MCP agent config
│   ├── db/init.sql                  PostgreSQL schema (objects, links, raw_snapshots, pgvector)
│   └── tests/                       129 tests
├── frontend/
│   ├── src/
│   │   ├── components/              10 components (Layout, GraphView, SearchBar, Markdown, etc.)
│   │   ├── pages/                   10 pages (Dashboard, Feed, Graph, Search, Chat, Markets, etc.)
│   │   ├── hooks/                   useOntology (React Query) + useChat (WebSocket)
│   │   └── lib/api.ts               Typed API client
│   └── tailwind.config.js           "Sovereign Intelligence" design system
├── docker-compose.yml               5 services: postgres, redis, backend, worker, frontend
├── .env.example
└── README.md
```

## Testing

```bash
# Backend (129 tests)
docker exec ontology-backend-1 python -m pytest tests/ -v

# Covers: API endpoints, all connectors (httpx mock), transform/mappers,
#         entity resolution, derived properties, ML analytics, cache layer
```

## Optional API Keys

The platform works without any keys. For richer data:

| Key | What it unlocks | How to get |
|-----|----------------|------------|
| `ANTHROPIC_API_KEY` | AI agent chat (14 tools) | console.anthropic.com |
| `GITHUB_TOKEN` | 5000 req/h (vs 60), all 50 companies | github.com/settings/tokens |
| `ALPHA_VANTAGE_KEY` | Market cap, PE, EPS, revenue, sector | alphavantage.co (free, instant) |
| `FRED_API_KEY` | Interest rates, GDP, inflation | fredaccount.stlouisfed.org (free) |
| `EIA_API_KEY` | Oil, gas, electricity prices | eia.gov/opendata (free) |

## Graph Engine

The graph uses **Cytoscape.js** with 4 layout algorithms:
- **Force Network** (fCoSE) — physics-based force-directed
- **Cola Physics** — constraint-based layout
- **Concentric** — companies center, persons middle, articles outer ring
- **Grid** — uniform spacing

Nodes are color-coded by type (company=indigo, person=sky, article=orange, repo=green, event=purple). Click a node to open the detail panel with properties and connections.

Filter panel toggles node types, link types, and edge labels.

## Design System

"Sovereign Intelligence" — dark mode, editorial authority:
- Deep atmospheric surfaces (`#020617` → `#0f172a` → `#1e293b`)
- Space Grotesk (headlines) + Inter (body)
- No borders — tonal depth separation
- Color-coded entity types across all views
- Glassmorphism for floating elements

## License

MIT
