# Multi-Agent System for Crypto Analysis

An autonomous, multi-agent crypto research and trading system built on **Google's Agent Development Kit (ADK)** and **Gemini 2.5 Flash**. A root orchestrator agent coordinates five specialized sub-agents to gather market intelligence, synthesize a report, validate a trade against a risk policy, and execute it on **Binance (testnet)**.

> ⚠️ **Disclaimer**: This project is for research/educational purposes. It trades against the Binance **testnet** by default. Do not point it at a live account without fully understanding the risks — nothing here is financial advice.

## How it works

The `root_agent` runs a fixed orchestration workflow on every cycle:

1. **Market Discovery** — loads the active risk policy and scans CryptoPanic + Google Search for trending/volatile assets.
2. **Data Acquisition** — delegates to each analyst sub-agent in parallel/sequence for fundamentals, sentiment, technicals, and current portfolio/trade history.
3. **Synthesis** — merges news, sentiment, technical, historical (RAG) and portfolio context into a single report.
4. **Decision** — decides `BUY` / `SELL` / `HOLD` from the synthesized signals.
5. **Execution** — on `BUY`/`SELL`, builds a `TradeRequest`, sends it to the `policy_enforcer` for validation, and only forwards approved trades to the `trader` for execution. Rejections are logged with the reason.

```
                     ┌─────────────┐
                     │  root_agent │  (orchestrator, Gemini 2.5 Flash)
                     └──────┬──────┘
        ┌───────────┬───────┼────────────┬─────────────┐
        ▼           ▼       ▼            ▼              ▼
 business_       business_  technical_   policy_       trader
 analyst_1       analyst_2  analyst      enforcer
 (news + RAG)    (Telegram   (CoinGecko  (JSON risk    (Binance
   │             sentiment)  market data)  policy)       testnet)
   ▼
 google_search_agent
```

## Sub-agents

| Agent | Role | Key tools |
|---|---|---|
| **business_analyst_1** | Fundamental/news analysis — finds the "why" behind price moves, plus RAG lookup of similar historical news events | `get_news_from_cryptopanic`, `search_similar_news` (ChromaDB + OpenAI embeddings), `google_search_agent` |
| **business_analyst_2** | Community sentiment analysis from Telegram channels | `get_telegram_news` |
| **technical_analyst** | Price/market data — ATH/ATL, market cap, volume, 24h–1y price changes, 1-day volatility | `get_crypto_technical_data` (CoinGecko API) |
| **policy_enforcer** | Validates every trade request against the active risk policy (position sizing, daily trade limits, stop-loss, asset whitelist, liquidity, volatility halts) | `validate_policy` |
| **trader** | Reports portfolio state and executes approved trades | `load_portfolio`, `make_trade`, `log_trade`, `process_trade_request` (Binance API, testnet) |
| **google_search_agent** | General web research to spot trending assets | Google Search grounding |

## Trading strategies

Selected via the `TRADING_STRATEGY` env var, each strategy has its own root-agent prompt and its own JSON risk policy:

| | Safe | Aggressive |
|---|---|---|
| Max position size | 5% | 35% |
| Max trades/day | 5 | 15 |
| Stop-loss required | Yes (≥1.5%) | No |
| Allowed order types | limit, stop_loss, take_profit | market, limit, stop_loss, take_profit |
| Asset whitelist | BTC, ETH, SOL, XRP | BTC, ETH, SOL, XRP, BNB, LTC, TRX, ADA, DOGE, PEPE |
| Min market cap | $10B | $100M |
| Volatility halt | 50% | 100% |

## Project structure

```
root_agent/
├── agent.py                       # Root orchestrator LlmAgent
├── prompt.py                      # ROOT_AGENT_PROMPT_SAFE / _AGGRESSIVE
├── tools/
│   └── trade_request_formatter.py # Builds the TradeRequest schema
└── sub_agents/
    ├── business_analyst_1/        # News + RAG (ChromaDB)
    │   └── sub_agents/google_search_agent/
    ├── business_analyst_2/        # Telegram sentiment
    ├── technical_analyst/         # CoinGecko technicals
    ├── policy_enforcer/           # Risk policy validation
    │   └── tools/policy_safe.json, policy_aggressive.json
    └── trader/                    # Portfolio + Binance execution

creating_database/                 # Dataset prep for the RAG store
├── Process_dataset.ipynb
├── cryptonews-articles-with-price-momentum-labels/
└── cryptonews-*.csv
```

## Tech stack

- **Agent framework**: [google-adk](https://github.com/google/adk-python) (`LlmAgent`, `AgentTool`) on **Gemini 2.5 Flash**
- **Vector store**: ChromaDB with OpenAI `text-embedding-3-small` embeddings (news RAG)
- **Exchange**: `python-binance` (testnet)
- **Market data**: CoinGecko API, CryptoPanic API
- **Social data**: Telethon (Telegram)
- **Data prep**: pandas, Jupyter notebook for building the labeled news dataset

## Setup

### 1. Install dependencies

```bash
cd root_agent
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

Copy `.env.template` to `.env` inside `root_agent/` and fill in credentials:

```bash
# Strategy
TRADING_STRATEGY="safe"   # safe | aggressive

# Google / Vertex AI
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=
GOOGLE_CLOUD_LOCATION=
GOOGLE_CLOUD_STAGING_BUCKET=

# OpenAI (used for RAG embeddings)
OPENAI_API_KEY=

# CryptoPanic
CRYPTO_PANIC_API_KEY=

# CoinGecko
COINGECKO_API_KEY=

# Telegram
TELEGRAM_API_ID=
TELEGRAM_API_HASH=
TELEGRAM_SESSION_STRING=

# Binance (testnet)
BINANCE_API_KEY=
BINANCE_API_SECRET=
```

### 3. Build the RAG database (optional, for `business_analyst_1`)

Run `creating_database/Process_dataset.ipynb` to process the labeled crypto-news dataset into `root_agent/sub_agents/business_analyst_1/tools/database/` (CSV + ChromaDB collection) used by `search_similar_news`.

### 4. Run

```bash
adk run root_agent
# or
adk web
```

## Notes / limitations

- `portfolio_manager.py` connects to Binance with `testnet=True` — trades are simulated against Binance's sandbox, not real funds.
- The RAG tool expects a pre-built ChromaDB collection at `business_analyst_1/tools/database/chroma_db` and a matching `cryptonews.csv` — generate these first via the notebook in `creating_database/`.
- All sub-agents run on `gemini-2.5-flash`; swap the model string in each `agent.py` to change this.
