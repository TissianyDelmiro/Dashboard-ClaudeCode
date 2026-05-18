"""E-commerce Analytics — dashboard Streamlit (case 01).

Lê os 3 Data Marts gold do Supabase e serve 3 diretores (Comercial / CS / Pricing).
Cada página tem KPIs, gráficos e (quando aplicável) tabelas de detalhe.
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import psycopg2
import psycopg2.extensions
import streamlit as st
from dotenv import load_dotenv

# ─── Setup ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="E-commerce Analytics",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded",
)
load_dotenv(Path(__file__).parent / ".env")

# Converte NUMERIC do Postgres para float (evita Decimal em pandas/plotly).
psycopg2.extensions.register_type(
    psycopg2.extensions.new_type(
        psycopg2.extensions.DECIMAL.values,
        "DEC2FLOAT",
        lambda v, _: float(v) if v is not None else None,
    )
)

# Paleta profissional (Tailwind-inspired) — funciona bem em fundo escuro.
PALETA = [
    "#60A5FA",  # blue-400
    "#34D399",  # emerald-400
    "#FBBF24",  # amber-400
    "#A78BFA",  # violet-400
    "#F472B6",  # pink-400
    "#22D3EE",  # cyan-400
    "#FB923C",  # orange-400
    "#94A3B8",  # slate-400
]
COR_PRIMARIA = PALETA[0]
COR_POSITIVA = "#10B981"  # emerald-500 — mais barato = bom
COR_NEUTRA = "#1F2937"    # gray-800 — perto do fundo
COR_NEGATIVA = "#EF4444"  # red-500 — mais caro = atenção

DIAS_SEMANA = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
MESES_PT = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
    5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
    9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro",
}


# ─── CSS de polimento ─────────────────────────────────────────────────────
# Direção: SaaS ops tool para uso diário — denso, quieto, escaneável.
# Sem gradientes decorativos, sem motion gratuito, tabular-nums nos números.
CUSTOM_CSS = """
<style>
/* Container principal — denser */
.main .block-container {
    padding-top: 1.5rem;
    padding-bottom: 3rem;
    max-width: 1400px;
}

/* Cards de métricas — sutis, sem gradiente */
div[data-testid="stMetric"] {
    background: rgba(22, 25, 34, 0.55);
    border: 1px solid rgba(148, 163, 184, 0.12);
    border-radius: 12px;
    padding: 14px 16px;
    transition: border-color 0.15s ease;
}
div[data-testid="stMetric"]:hover {
    border-color: rgba(148, 163, 184, 0.28);
}
div[data-testid="stMetric"] label {
    color: rgba(229, 231, 235, 0.6) !important;
    font-size: 0.72rem !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
div[data-testid="stMetricValue"] {
    font-size: 1.55rem !important;
    font-weight: 600 !important;
    color: #F9FAFB !important;
    font-variant-numeric: tabular-nums;
    letter-spacing: -0.01em;
    line-height: 1.2 !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #07090E;
    border-right: 1px solid rgba(148, 163, 184, 0.08);
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2 {
    font-size: 1.05rem;
    font-weight: 700;
}

/* Headers das páginas — discretos */
h1 {
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
    color: #F9FAFB !important;
    margin-bottom: 0.15rem !important;
    font-size: 1.65rem !important;
}
h2, h3 {
    font-weight: 600 !important;
    color: #E5E7EB !important;
}

/* Tabelas — tabular-nums em todos os números */
div[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid rgba(148, 163, 184, 0.12);
}
div[data-testid="stDataFrame"] [role="cell"],
div[data-testid="stDataFrame"] [role="columnheader"] {
    font-variant-numeric: tabular-nums;
}

/* Containers de gráfico — só borda fina, sem fundo decorativo */
div[data-testid="stPlotlyChart"] {
    border: 1px solid rgba(148, 163, 184, 0.08);
    border-radius: 12px;
    padding: 4px 8px;
}

/* Divider mais sutil */
hr {
    border-color: rgba(148, 163, 184, 0.06) !important;
    margin: 1rem 0 !important;
}

/* Inputs e selects */
div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div {
    border-radius: 8px !important;
    border-color: rgba(148, 163, 184, 0.18) !important;
}

/* Caption sutil */
div[data-testid="stCaptionContainer"] {
    color: rgba(229, 231, 235, 0.5);
    font-size: 0.82rem;
}

/* Foco visível em controles (acessibilidade) */
button:focus-visible,
[role="combobox"]:focus-visible,
[role="listbox"]:focus-visible,
input:focus-visible {
    outline: 2px solid rgba(96, 165, 250, 0.55);
    outline-offset: 2px;
}

/* Telas estreitas (responsive) */
@media (max-width: 768px) {
    div[data-testid="stMetric"] { padding: 10px 12px; }
    div[data-testid="stMetricValue"] { font-size: 1.25rem !important; }
    div[data-testid="stMetric"] label { font-size: 0.68rem !important; }
    .main .block-container { padding-top: 1rem; }
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ─── Formatação BR ────────────────────────────────────────────────────────
def fmt_brl(valor) -> str:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        valor = 0
    s = f"{float(valor):,.2f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_pct(valor) -> str:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        valor = 0
    sinal = "+" if valor >= 0 else ""
    return f"{sinal}{float(valor):.1f}%".replace(".", ",")


def fmt_int(valor) -> str:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        valor = 0
    return f"{int(valor):,}".replace(",", ".")


# ─── Styling helper para Plotly ──────────────────────────────────────────
def style_fig(fig: go.Figure) -> go.Figure:
    """Aplica visual consistente (dark, transparente, denso) em todos os gráficos."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
                  color="#E5E7EB", size=11),
        title=dict(font=dict(size=13, color="#F3F4F6"), x=0.0, xanchor="left",
                   pad=dict(t=4, b=4)),
        margin=dict(l=8, r=12, t=42, b=32),
        xaxis=dict(gridcolor="rgba(148, 163, 184, 0.06)",
                   linecolor="rgba(148, 163, 184, 0.12)",
                   zerolinecolor="rgba(148, 163, 184, 0.12)",
                   tickfont=dict(size=10)),
        yaxis=dict(gridcolor="rgba(148, 163, 184, 0.06)",
                   linecolor="rgba(148, 163, 184, 0.12)",
                   zerolinecolor="rgba(148, 163, 184, 0.12)",
                   tickfont=dict(size=10),
                   tickformat="~s"),  # 1k, 1M etc onde fizer sentido
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="rgba(148, 163, 184, 0.12)",
                    borderwidth=1, font=dict(size=10)),
        hoverlabel=dict(bgcolor="#1F2937", bordercolor="#374151",
                        font=dict(color="#F3F4F6", size=11)),
        bargap=0.35,  # barras mais finas, menos amontoadas
    )
    return fig


def chart(fig: go.Figure) -> None:
    """Atalho — aplica style_fig e renderiza."""
    st.plotly_chart(style_fig(fig), use_container_width=True, theme=None)


# ─── Conexão com o Supabase ───────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def _get_connection():
    return psycopg2.connect(
        host=os.getenv("SUPABASE_HOST"),
        port=os.getenv("SUPABASE_PORT", "5432"),
        dbname=os.getenv("SUPABASE_DB", "postgres"),
        user=os.getenv("SUPABASE_USER"),
        password=os.getenv("SUPABASE_PASSWORD"),
        connect_timeout=10,
    )


def run_query(sql: str, params: tuple | None = None) -> pd.DataFrame:
    """Executa SQL e devolve DataFrame. Em caso de erro, mostra mensagem amigável e encerra."""
    try:
        conn = _get_connection()
        with conn.cursor() as cur:
            cur.execute(sql, params)
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
        return pd.DataFrame(rows, columns=cols)
    except psycopg2.Error as e:
        try:
            _get_connection().rollback()
        except Exception:
            pass
        _get_connection.clear()
        st.error(
            "❌ Não foi possível consultar o banco. Verifique o arquivo `.env` e "
            "a conectividade com o Supabase."
        )
        st.caption(f"Detalhe técnico ({type(e).__name__}): {e}")
        st.stop()


# ─── Página: Vendas (Diretor Comercial) ───────────────────────────────────
def page_vendas() -> None:
    st.title("📈 Vendas")
    st.caption("Diretor Comercial · Fonte: `public_gold_sales.vendas_temporais`")

    df = run_query("SELECT * FROM public_gold_sales.vendas_temporais")
    if df.empty:
        st.warning("Sem dados de vendas para exibir.")
        return

    meses_disp = sorted(int(m) for m in df["mes_venda"].dropna().unique())
    opcoes = ["Todos"] + [f"{m:02d} - {MESES_PT.get(m, m)}" for m in meses_disp]
    escolha = st.selectbox("Filtrar por mês", opcoes, index=0)
    if escolha != "Todos":
        mes_num = int(escolha.split(" - ")[0])
        df = df[df["mes_venda"] == mes_num]

    receita = df["receita_total"].sum()
    vendas = int(df["total_vendas"].sum())
    clientes = int(df["total_clientes_unicos"].sum())
    ticket = receita / vendas if vendas else 0

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    c1.metric("Receita Total", fmt_brl(receita))
    c2.metric("Total de Vendas", fmt_int(vendas))
    c3.metric("Ticket Médio", fmt_brl(ticket))
    c4.metric("Clientes Únicos (∑ diário)", fmt_int(clientes))

    st.divider()

    df_dia = (
        df.groupby("data_venda", as_index=False)["receita_total"]
        .sum()
        .sort_values("data_venda")
    )
    fig1 = px.line(
        df_dia, x="data_venda", y="receita_total",
        title="Receita Diária", markers=True,
        color_discrete_sequence=[COR_PRIMARIA],
    )
    fig1.update_traces(line=dict(width=2.5),
                       marker=dict(size=7, line=dict(width=0)))
    fig1.update_layout(xaxis_title="Data", yaxis_title="Receita (R$)")
    chart(fig1)

    col_a, col_b = st.columns(2, gap="medium")
    with col_a:
        df_dow = df.groupby("dia_semana_nome", as_index=False)["receita_total"].sum()
        fig2 = px.bar(
            df_dow, x="dia_semana_nome", y="receita_total",
            title="Receita por Dia da Semana",
            category_orders={"dia_semana_nome": DIAS_SEMANA},
            color_discrete_sequence=[PALETA[1]],
        )
        fig2.update_layout(xaxis_title="Dia da Semana", yaxis_title="Receita (R$)")
        fig2.update_traces(marker=dict(line=dict(width=0)))
        chart(fig2)

    with col_b:
        df_hora = (
            df.groupby("hora_venda", as_index=False)["total_vendas"]
            .sum()
            .sort_values("hora_venda")
        )
        fig3 = px.bar(
            df_hora, x="hora_venda", y="total_vendas",
            title="Volume de Vendas por Hora",
            color_discrete_sequence=[PALETA[2]],
        )
        fig3.update_layout(
            xaxis_title="Hora", yaxis_title="Vendas",
            xaxis=dict(tickmode="linear", dtick=1,
                       gridcolor="rgba(148, 163, 184, 0.08)"),
        )
        fig3.update_traces(marker=dict(line=dict(width=0)))
        chart(fig3)


# ─── Página: Clientes (Diretora de Customer Success) ──────────────────────
def page_clientes() -> None:
    st.title("👥 Clientes")
    st.caption("Diretora de Customer Success · Fonte: `public_gold_cs.clientes_segmentacao`")

    df = run_query("SELECT * FROM public_gold_cs.clientes_segmentacao")
    if df.empty:
        st.warning("Sem dados de clientes para exibir.")
        return

    total = len(df)
    vips = int((df["segmento_cliente"] == "VIP").sum())
    receita_vip = df.loc[df["segmento_cliente"] == "VIP", "receita_total"].sum()
    ticket_medio = df["ticket_medio"].mean() if total else 0

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    c1.metric("Total Clientes", fmt_int(total))
    c2.metric("Clientes VIP", fmt_int(vips))
    c3.metric("Receita VIP", fmt_brl(receita_vip))
    c4.metric("Ticket Médio Geral", fmt_brl(ticket_medio))

    st.divider()

    col_a, col_b = st.columns(2, gap="medium")
    with col_a:
        df_seg = (
            df.groupby("segmento_cliente", as_index=False)
            .size()
            .rename(columns={"size": "qtd"})
        )
        fig1 = px.pie(
            df_seg, names="segmento_cliente", values="qtd",
            title="Distribuição de Clientes por Segmento",
            hole=0.55, color_discrete_sequence=PALETA,
        )
        fig1.update_traces(textposition="outside", textinfo="label+percent",
                           marker=dict(line=dict(color="#0B0D12", width=2)))
        chart(fig1)

    with col_b:
        df_seg_rec = (
            df.groupby("segmento_cliente", as_index=False)["receita_total"]
            .sum()
            .sort_values("receita_total", ascending=False)
        )
        fig2 = px.bar(
            df_seg_rec, x="segmento_cliente", y="receita_total",
            title="Receita por Segmento", color="segmento_cliente",
            color_discrete_sequence=PALETA,
        )
        fig2.update_layout(
            xaxis_title="Segmento", yaxis_title="Receita (R$)", showlegend=False
        )
        fig2.update_traces(marker=dict(line=dict(width=0)))
        chart(fig2)

    col_c, col_d = st.columns(2, gap="medium")
    with col_c:
        df_top = (
            df.dropna(subset=["ranking_receita"])
            .sort_values("ranking_receita")
            .head(10)
        )
        fig3 = px.bar(
            df_top, x="receita_total", y="nome_cliente",
            orientation="h", title="Top 10 Clientes por Receita",
            color_discrete_sequence=[PALETA[0]],
        )
        fig3.update_layout(
            yaxis={"categoryorder": "total ascending"},
            xaxis_title="Receita (R$)", yaxis_title="",
        )
        fig3.update_traces(marker=dict(line=dict(width=0)))
        chart(fig3)

    with col_d:
        df_est = (
            df.dropna(subset=["estado"])
            .groupby("estado", as_index=False)
            .size()
            .rename(columns={"size": "qtd"})
            .sort_values("qtd", ascending=False)
        )
        fig4 = px.bar(
            df_est, x="estado", y="qtd",
            title="Clientes por Estado",
            color_discrete_sequence=[PALETA[3]],
        )
        fig4.update_layout(xaxis_title="Estado", yaxis_title="Clientes")
        fig4.update_traces(marker=dict(line=dict(width=0)))
        chart(fig4)

    st.divider()
    st.subheader("Detalhes")
    segs = sorted(df["segmento_cliente"].dropna().unique().tolist())
    filtro = st.selectbox("Filtrar por segmento", ["Todos"] + segs)
    df_view = df if filtro == "Todos" else df[df["segmento_cliente"] == filtro]
    df_view = df_view.sort_values("ranking_receita", na_position="last")
    st.dataframe(df_view, use_container_width=True, hide_index=True)


# ─── Página: Pricing (Diretor de Pricing) ─────────────────────────────────
def page_pricing() -> None:
    st.title("💰 Pricing")
    st.caption("Diretor de Pricing · Fonte: `public_gold_pricing.precos_competitividade`")

    df_full = run_query("SELECT * FROM public_gold_pricing.precos_competitividade")
    if df_full.empty:
        st.warning("Sem dados de preços para exibir.")
        return

    cats_disp = sorted(df_full["categoria"].dropna().unique().tolist())
    cats_sel = st.multiselect(
        "Filtrar por categoria(s) — vazio = todas", cats_disp, default=[]
    )
    df = df_full if not cats_sel else df_full[df_full["categoria"].isin(cats_sel)]

    total = len(df)
    caros = int((df["classificacao_preco"] == "MAIS_CARO_QUE_TODOS").sum())
    baratos = int((df["classificacao_preco"] == "MAIS_BARATO_QUE_TODOS").sum())
    diff_media = df["diferenca_percentual_vs_media"].mean() if total else 0

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    c1.metric("Total Produtos Monitorados", fmt_int(total))
    c2.metric("Mais Caros que Todos", fmt_int(caros))
    c3.metric("Mais Baratos que Todos", fmt_int(baratos))
    c4.metric("Diferença Média vs Mercado", fmt_pct(diff_media))

    st.divider()

    col_a, col_b = st.columns(2, gap="medium")
    with col_a:
        df_cls = (
            df.groupby("classificacao_preco", as_index=False)
            .size()
            .rename(columns={"size": "qtd"})
        )
        fig1 = px.pie(
            df_cls, names="classificacao_preco", values="qtd",
            title="Posicionamento vs Concorrência",
            hole=0.55, color_discrete_sequence=PALETA,
        )
        fig1.update_traces(textposition="outside", textinfo="label+percent",
                           marker=dict(line=dict(color="#0B0D12", width=2)))
        chart(fig1)

    with col_b:
        df_cat = (
            df.groupby("categoria", as_index=False)["diferenca_percentual_vs_media"]
            .mean()
            .sort_values("diferenca_percentual_vs_media")
        )
        fig2 = px.bar(
            df_cat, x="categoria", y="diferenca_percentual_vs_media",
            title="Competitividade por Categoria (média % vs mercado)",
            color="diferenca_percentual_vs_media",
            color_continuous_scale=[
                [0.0, COR_POSITIVA],
                [0.5, COR_NEUTRA],
                [1.0, COR_NEGATIVA],
            ],
            color_continuous_midpoint=0,
        )
        fig2.update_layout(
            xaxis_title="Categoria", yaxis_title="Diferença % média",
            coloraxis_showscale=False,
        )
        fig2.update_traces(marker=dict(line=dict(width=0)))
        chart(fig2)

    df_sc = df.dropna(
        subset=["diferenca_percentual_vs_media", "quantidade_total", "receita_total"]
    )
    fig3 = px.scatter(
        df_sc,
        x="diferenca_percentual_vs_media", y="quantidade_total",
        color="classificacao_preco", size="receita_total",
        hover_data=["nome_produto", "categoria", "nosso_preco"],
        title="Competitividade × Volume de Vendas",
        color_discrete_sequence=PALETA,
        size_max=40,
    )
    fig3.update_layout(
        xaxis_title="Diferença % vs média mercado",
        yaxis_title="Quantidade vendida",
    )
    fig3.update_traces(marker=dict(line=dict(width=1, color="rgba(11, 13, 18, 0.6)"),
                                   opacity=0.85))
    chart(fig3)

    st.divider()
    st.subheader("⚠️ Produtos em Alerta — mais caros que todos os concorrentes")
    df_alert = (
        df[df["classificacao_preco"] == "MAIS_CARO_QUE_TODOS"][
            [
                "produto_id", "nome_produto", "categoria",
                "nosso_preco", "preco_maximo_concorrentes",
                "diferenca_percentual_vs_media",
            ]
        ]
        .sort_values("diferenca_percentual_vs_media", ascending=False)
    )
    if df_alert.empty:
        st.info("Nenhum produto na categoria selecionada está classificado como MAIS_CARO_QUE_TODOS.")
    else:
        st.dataframe(df_alert, use_container_width=True, hide_index=True)


# ─── Roteamento ───────────────────────────────────────────────────────────
st.sidebar.title("📊 E-commerce Analytics")
st.sidebar.caption("Dashboard self-service")
st.sidebar.divider()
pagina = st.sidebar.radio(
    "Página", ["Vendas", "Clientes", "Pricing"], label_visibility="collapsed"
)

if pagina == "Vendas":
    page_vendas()
elif pagina == "Clientes":
    page_clientes()
else:
    page_pricing()
