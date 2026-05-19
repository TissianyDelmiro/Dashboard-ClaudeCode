# Dashboard-ClaudeCode# 📊 Dashboard E-commerce — Jornada de Dados

> Projeto da **Aula 04 — Claude Code** da [Imersão Jornada de Dados](https://github.com/lvgalvao/data-engineering-roadmap/tree/main/00-imersao-jornada/aulas/aula-04-claude-code) com Luciano Galvão.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/DB-PostgreSQL%20%7C%20Supabase-336791?logo=postgresql&logoColor=white)

---

## Sobre

Dashboard Streamlit de self-service para 3 diretores de um e-commerce, consumindo os Data Marts gold construídos nos dias anteriores da imersão. Gerado com **Claude Code** a partir de um PRD e do catálogo de dados.

Streamlit: https://dashboard-claudecode-cxkbltzemuudnekg3qjswz.streamlit.app/

<img width="1920" height="1894" alt="jornadadados" src="https://github.com/user-attachments/assets/cae7a08c-8cad-4175-83e3-b2f031bae008" />


---

## Páginas

| Página | Diretor | Dados |
|---|---|---|
| **Vendas** | Comercial | Receita, ticket médio, vendas por dia/hora |
| **Clientes** | Customer Success | Segmentação VIP/TOP_TIER/REGULAR, top 10 |
| **Pricing** | Pricing | Classificação vs. concorrência, alertas |

---

## Stack

| Componente | Tecnologia |
|---|---|
| Interface | Streamlit |
| Gráficos | Plotly |
| Banco | PostgreSQL (Supabase) |
| Conexão | psycopg2-binary |
| Ambiente | python-dotenv |

---

## Instalação

```bash
git clone <url-do-repositorio>
cd case-01-dashboard
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Editar .env com sua POSTGRES_URL
```

---

## Como Usar

```bash
streamlit run app.py
```

Acesse em `http://localhost:8501`.

---

## Estrutura

```
case-01-dashboard/
├── app.py              # Dashboard Streamlit
├── requirements.txt
├── .env.example
├── CLAUDE.md           # Contexto do projeto para o Claude Code
└── .llm/
    ├── database.md     # Schema dos 3 Data Marts gold
    └── prd.md          # Requisitos do dashboard
```

---

<p align="center">
  Desenvolvido por <a href="https://github.com/TissianyDelmiro">Tissiany Delmiro</a> 🚀
</p>
