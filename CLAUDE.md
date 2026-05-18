# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

This repository currently contains only a PRD (`.llm/prd.md`) and Supabase MCP configuration. The application code described below has **not yet been written** — generating it is the primary task.

## What is being built

A self-service Streamlit dashboard that reads gold-layer Data Marts from a Supabase PostgreSQL database and serves three directors of an e-commerce business. Each director has a dedicated page with KPIs, charts, filters, and (where specified) detail tables.

The full spec — KPI formulas, chart types, source columns, filters, and page-by-page layout — lives in `.llm/prd.md`. Treat it as authoritative; do not invent KPIs or visualizations not listed there.

## Target architecture

```
Supabase (PostgreSQL)
    ├── public_gold_sales.vendas_temporais         → Page "Vendas"   (Diretor Comercial)
    ├── public_gold_cs.clientes_segmentacao        → Page "Clientes" (Diretora de CS)
    └── public_gold_pricing.precos_competitividade → Page "Pricing"  (Diretor de Pricing)
            │
            ▼
    case-01-dashboard/app.py   (single Streamlit app, sidebar navigates the 3 pages)
```

**Stack:** Python 3.10+, Streamlit, psycopg2-binary, pandas, plotly, python-dotenv.

**Files to generate** (per PRD):
- `case-01-dashboard/app.py`
- `case-01-dashboard/requirements.txt`
- `case-01-dashboard/.env.example`

## Database connection

Credentials come from `.env` (variables: `SUPABASE_HOST`, `SUPABASE_PORT`, `SUPABASE_DB`, `SUPABASE_USER`, `SUPABASE_PASSWORD`). Implement a single reusable helper that reads `.env` and returns a `pandas.DataFrame` from a SQL query. Show a friendly error message when the DB is unreachable rather than letting psycopg2 stack-trace into the UI.

The Supabase MCP server is wired up in `.mcp.json` (project ref `ukjhlkniixjdvbuinoiu`) — use it to introspect schemas/tables, run exploratory SQL, and check advisors before writing queries against the three gold tables. Prefer `list_tables` before assuming column names from the PRD.

## Conventions called out in the PRD (don't drift from these)

- **No aggressive caching.** Gold data refreshes after each `dbt run`. Avoid `@st.cache_data` with long TTLs; if caching is added, keep it short and document why.
- **Brazilian number formatting.** Currency as `R$ 1.234,56` (dot thousands, comma decimal); percentages as `+1,2%`.
- **Wide layout.** `st.set_page_config(layout="wide")`.
- **Consistent chart colors across pages.**
- KPI rows use `st.columns(4)` with `st.metric`.
- Day-of-week ordering on charts: Segunda → Domingo (not alphabetical).

## Running the app (once it exists)

```bash
cd case-01-dashboard
cp .env.example .env   # fill in real Supabase credentials
pip install -r requirements.txt
streamlit run app.py   # opens http://localhost:8501
```

There is no test suite, linter, or build step defined in the PRD — don't fabricate one.

## Installed skills

`.agents/skills/` contains the Supabase agent skills (`supabase`, `supabase-postgres-best-practices`), symlinked into `.claude/skills/`. Consult them for Postgres/Supabase patterns before hand-rolling SQL or schema decisions.
