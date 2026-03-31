# WORLD PREDICTOR
### Multi-Agent AI Simulation for Global Geopolitical Prediction

World Predictor deploys **6,000 virtual agents** across **20 countries**, each with census-accurate demographic profiles (race, religion, education, IQ, income, age, politics). These agents consume real-world news, react based on their individual trust models, and produce emergent predictions about political stability, economic sentiment, and revolution risk.

![Dashboard Preview](https://img.shields.io/badge/status-proof%20of%20concept-blue) ![Python](https://img.shields.io/badge/python-3.10+-green) ![React](https://img.shields.io/badge/frontend-React%20+%20TypeScript-61dafb) ![License](https://img.shields.io/badge/license-Proprietary-red)

---

## How It Works

```
Real-World News (NewsAPI + RSS)
        |
        v
Claude Haiku classifies into 9 categories
        |
        v
6,000 Agents react (IQ-weighted TrustModel)
  - High IQ agents: weight source credibility
  - Low IQ agents: weight political alignment
        |
        v
Opinion Diffusion (Bounded Confidence Model)
  - Echo chambers form naturally
  - Memory decay (mean reversion to baseline)
        |
        v
Country Metrics: stability, sentiment, trust, revolution risk
        |
        v
Inter-Country Spillover (trade, alliance, rivalry dynamics)
        |
        v
Dashboard: globe map, charts, scenario engine
```

## Features

### Simulation Engine
- **20 countries** with 300 agents each, weighted by real demographic distributions
- **IQ normal distribution** per country (e.g. JP: 106, US: 98, NG: 84) correlated with education level
- **5 reaction types**: Support, Opposition, Apathy, Confusion, Fear
- **Bounded Confidence Model** for opinion diffusion — agents only influence each other within a confidence threshold, producing natural echo chambers
- **Memory decay** — agent opinions revert toward baseline over time
- **Revolution Risk Index** — composite of trust erosion, fear levels, opposition ratio, and polarization

### Geopolitical Layer
- **Event system** with magnitude, decay rate, and cross-border spillover (6 presets: financial crash, pandemic, war, etc.)
- **Institution agents** — Government, Central Bank, Military — each with policy levers that affect agent populations
- **8 preset policies**: rate hike, stimulus, austerity, martial law, etc.
- **Inter-country dynamics**: 22 trade relationships, 11 alliances, 8 rivalries with spillover coefficients

### Scenario Engine
- Fork entire simulation state, inject custom events/policies, run N days forward
- Compare baseline vs. scenario outcomes side-by-side

### News Pipeline
- **NewsAPI** with RSS fallback from 14 profiled sources (each with credibility + political bias scores)
- **Claude Haiku** batch classification (10 articles at a time) into: economy, politics, military, social, technology, environment, health, diplomacy, crisis
- Deduplication by MD5 title hash

### Data & Validation
- **SQLite persistence**: daily_metrics, news_archive, simulation_state (WAL journal mode)
- **Market data** integration via yfinance
- **Backtesting framework** for validating predictions against historical outcomes

### React Dashboard
- Interactive **Plotly globe** with click-to-zoom country detail
- **Global metrics strip**: Optimism, Trust, Stability, Revolution Risk, Global Tension
- **Country detail pages**: full demographic breakdowns (pie charts for race/religion/education, bar charts for age/politics), biometrics (IQ mean/std, income percentiles), institution status, trade relationships
- **Scenario builder**: select preset events/policies, run simulations, view results
- Live polling with **TanStack Query** (15s refresh cycle)
- Animated number transitions with **Framer Motion**

## Countries

US, CN, IN, BR, RU, JP, DE, GB, FR, KR, AU, MX, ID, NG, EG, SA, TR, PK, PH, TH

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI, Uvicorn |
| Simulation | NumPy, scikit-learn, custom agent framework |
| AI | Anthropic Claude Haiku (news classification) |
| News | NewsAPI, feedparser, BeautifulSoup |
| Database | SQLite (WAL mode) |
| Frontend | React 19, TypeScript, Vite |
| State | TanStack Query (server), Zustand (UI) |
| Charts | Recharts, Plotly.js (geo) |
| Animation | Framer Motion |
| Market Data | yfinance |

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- [NewsAPI key](https://newsapi.org/) (optional, falls back to RSS)
- [Anthropic API key](https://console.anthropic.com/) (optional, for news classification)

### Setup

```bash
# Clone
git clone https://github.com/dreadnought090/world-predictor-poc.git
cd world-predictor-poc

# Backend
pip install -r requirements.txt
cp .env.example .env  # Add your API keys

# Frontend
cd frontend
npm install
cd ..
```

### Run

```bash
# Terminal 1: API server (initializes 6,000 agents on startup)
python main.py
# -> http://localhost:8080

# Terminal 2: Vite dev server (proxies API calls to backend)
cd frontend
npm run dev
# -> http://localhost:5173
```

### Production Build

```bash
cd frontend && npm run build && cd ..
python main.py
# FastAPI serves the React SPA from frontend/dist/
# -> http://localhost:8080
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/predictions` | All country metrics |
| GET | `/predictions/{code}` | Single country metrics |
| GET | `/country/{code}/profile` | Full demographics, biometrics, institutions, relations |
| GET | `/agents/{code}` | Sample raw agent data |
| GET | `/history` | Historical daily metrics |
| GET | `/events/active` | Currently active geopolitical events |
| GET | `/news/archive` | Classified news articles |
| GET | `/presets/events` | Available preset events |
| GET | `/presets/policies` | Available preset policies |
| POST | `/fetch_news` | Fetch & classify latest news |
| POST | `/simulate` | Run simulation batch (N days) |
| POST | `/events/inject` | Inject a geopolitical event |
| POST | `/institutions/{code}/policy` | Enact a policy for a country |
| POST | `/scenarios/run` | Run a what-if scenario |
| GET | `/global/tension` | Global tension index |
| GET | `/validation/backtest` | Run validation backtest |

## Project Structure

```
world-predictor-poc/
├── main.py                          # Entry point (FastAPI + Uvicorn)
├── config.yaml                      # Centralized configuration
├── requirements.txt
├── world_predictor/
│   ├── config.py                    # Config loader
│   ├── api/
│   │   ├── app.py                   # FastAPI app (30+ endpoints)
│   │   ├── models.py                # Pydantic schemas
│   │   └── routes.py                # Route definitions
│   ├── data/
│   │   ├── agents.py                # AgentGenerator (20 countries, real demographics)
│   │   ├── news.py                  # NewsProcessor (NewsAPI + RSS + Claude classification)
│   │   ├── database.py              # SQLite persistence layer
│   │   └── market.py                # Market data (yfinance)
│   ├── simulation/
│   │   ├── engine.py                # SimulationEngine + CountryEngine
│   │   ├── models.py                # TrustModel, reaction logic, opinion diffusion
│   │   ├── events.py                # GeoEvent, EventManager, presets
│   │   ├── institutions.py          # Institution agents, policies
│   │   ├── intercountry.py          # Trade/alliance/rivalry dynamics
│   │   ├── scenarios.py             # ScenarioEngine (fork & compare)
│   │   └── visualization.py         # Server-side chart generation
│   └── validation/
│       └── backtester.py            # Prediction validation framework
├── frontend/
│   ├── src/
│   │   ├── App.tsx                  # Router (Dashboard, CountryDetail, Scenarios)
│   │   ├── api/
│   │   │   ├── queries.ts           # TanStack Query hooks (polling)
│   │   │   ├── mutations.ts         # Mutation hooks (simulate, inject, policy)
│   │   │   └── client.ts            # Axios instance
│   │   ├── components/
│   │   │   ├── dashboard/           # GlobeMap, CountryTable, GlobalMetricsStrip
│   │   │   ├── events/              # ActiveEventsList
│   │   │   ├── news/                # NewsFeed
│   │   │   └── common/              # MetricCard, Badge, Skeleton, ProgressBar
│   │   ├── pages/
│   │   │   ├── DashboardPage.tsx    # Main dashboard with globe + table
│   │   │   ├── CountryDetailPage.tsx # Full country profile + demographics
│   │   │   └── ScenariosPage.tsx    # What-if scenario builder
│   │   ├── stores/uiStore.ts        # Zustand (search, sort, comparison)
│   │   └── styles/globals.css       # Tailwind CSS v4
│   └── vite.config.ts               # Dev proxy to backend
└── tests/                           # 68 tests (agents, API, news, simulation)
```

## License

Proprietary. See [LICENSE](LICENSE) for details.
