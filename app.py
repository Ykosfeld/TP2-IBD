"""
TP2 - DCC011 Introdução a Banco de Dados (UFMG 2026/2)
Aplicação Streamlit: Fiscalização Ambiental e Autos de Infração do IBAMA em 2026

Como executar:
    1. Rode o notebook tp2.ipynb (ele cria o banco auto_infracao.db nesta pasta)
    2. pip install -r requirements.txt
    3. streamlit run app.py
"""
import os
import sqlite3

import altair as alt
import pandas as pd
import streamlit as st

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "auto_infracao.db")

st.set_page_config(page_title="Autos de Infração IBAMA 2026", page_icon="🌿", layout="wide")

VERDE = "#2f6b4f"
DESTAQUE = "#b8432f"


# ---------------------------------------------------------------- utilidades
def brl(valor, casas=0):
    """Formata número como moeda brasileira."""
    if valor is None or pd.isna(valor):
        return "—"
    texto = f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def brl_curto(valor):
    if valor is None or pd.isna(valor):
        return "—"
    if abs(valor) >= 1e9:
        return f"R$ {valor / 1e9:.2f} bi".replace(".", ",")
    if abs(valor) >= 1e6:
        return f"R$ {valor / 1e6:.1f} mi".replace(".", ",")
    return brl(valor)


def inteiro(n):
    return f"{int(n):,}".replace(",", ".")


@st.cache_resource
def conectar():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def consultar(sql, params=()):
    return pd.read_sql_query(sql, conectar(), params=params)


@st.cache_data
def carregar_base():
    """Junção das tabelas normalizadas, usada nas abas de exploração."""
    df = consultar("""
        SELECT a.num_auto_infracao, a.data_hora, a.valor_multa, a.tipo_auto, a.bioma,
               a.latitude, a.longitude, a.codigo_ordem,
               i.id_infrator, i.nome_infrator, i.tipo_pessoa,
               m.cod_municipio, m.nome_municipio, m.uf,
               t.tipo_infracao, t.descricao_infracao,
               o.nome_operacao, o.unidade_ordenadora
        FROM Auto_Infracao a
        JOIN Infrator i       ON a.id_infrator   = i.id_infrator
        JOIN Municipio m      ON a.cod_municipio = m.cod_municipio
        JOIN Tipo_Infracao t  ON a.id_tipo       = t.id_tipo
        LEFT JOIN Ordem_Fiscalizacao o ON a.codigo_ordem = o.codigo_ordem
    """)
    df["data"] = pd.to_datetime(df["data_hora"], errors="coerce")
    df["mes"] = df["data"].dt.to_period("M").dt.to_timestamp()
    meses = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
    df["mes_nome"] = df["data"].dt.month.map(lambda m: meses[int(m) - 1] if pd.notna(m) else None)
    # Alguns autos trazem o bioma repetido ("Amazonia, Amazonia"): fica o primeiro
    df["bioma"] = df["bioma"].fillna("Não informado").str.split(",").str[0].str.strip()
    df["nome_municipio"] = df["nome_municipio"].str.title()
    return df


# ---------------------------------------------------------------- banco ausente
if not os.path.exists(DB_PATH):
    st.title("🌿 Autos de Infração do IBAMA em 2026")
    st.error(
        "Banco `auto_infracao.db` não encontrado. Execute primeiro o notebook `tp2.ipynb` "
        "nesta mesma pasta: ele lê o `auto_infracao_2026.csv` e cria o banco."
    )
    st.stop()

base = carregar_base()

# ---------------------------------------------------------------- filtros
st.sidebar.header("Filtros")
st.sidebar.caption("Valem para as abas Visão geral, Mapa e Infratores e operações.")

data_min, data_max = base["data"].min().date(), base["data"].max().date()
periodo = st.sidebar.date_input("Período", value=(data_min, data_max),
                                min_value=data_min, max_value=data_max, format="DD/MM/YYYY")
ufs = st.sidebar.multiselect("UF", sorted(base["uf"].unique()), placeholder="Todas")
categorias = st.sidebar.multiselect("Categoria da infração", sorted(base["tipo_infracao"].unique()), placeholder="Todas")
biomas = st.sidebar.multiselect("Bioma", sorted(base["bioma"].unique()), placeholder="Todos")
pessoa = st.sidebar.radio("Tipo de pessoa", ["Todas", "PF", "PJ"], horizontal=True)

f = base
if isinstance(periodo, (tuple, list)) and len(periodo) == 2:
    f = f[(f["data"].dt.date >= periodo[0]) & (f["data"].dt.date <= periodo[1])]
if ufs:
    f = f[f["uf"].isin(ufs)]
if categorias:
    f = f[f["tipo_infracao"].isin(categorias)]
if biomas:
    f = f[f["bioma"].isin(biomas)]
if pessoa != "Todas":
    f = f[f["tipo_pessoa"] == pessoa]

st.sidebar.divider()
st.sidebar.caption(f"Fonte: IBAMA – Fiscalização: Auto de Infração (dados.gov.br), "
                   f"arquivo auto_infracao_2026.csv. Banco SQLite com "
                   f"{inteiro(len(base))} autos.")

# ---------------------------------------------------------------- cabeçalho
st.title("🌿 Autos de Infração do IBAMA em 2026")
st.caption("DCC011 – Introdução a Banco de Dados · UFMG 2026/2 · Trabalho Prático 2")

aba_geral, aba_mapa, aba_infratores, aba_consultas = st.tabs(
    ["Visão geral", "Mapa", "Infratores e operações", "As 10 consultas"]
)

# ---------------------------------------------------------------- visão geral
with aba_geral:
    if f.empty:
        st.warning("Nenhum auto com os filtros selecionados.")
    else:
        total = f["valor_multa"].sum()
        grandes = f.loc[f["valor_multa"] >= 1_000_000, "valor_multa"].sum()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Autos de infração", inteiro(len(f)))
        c2.metric("Valor total das multas", brl_curto(total))
        c3.metric("Multa mediana", brl(f["valor_multa"].median()))
        c4.metric("Valor em multas ≥ R$ 1 mi", f"{(grandes / total * 100 if total else 0):.0f}%".replace(".", ","),
                  help="Parcela do valor total que vem de autos de R$ 1 milhão ou mais.")

        st.subheader("Evolução mensal")
        mensal = (f.groupby(["mes", "mes_nome"]).agg(autos=("num_auto_infracao", "count"),
                                                    valor=("valor_multa", "sum")).reset_index())
        ordem_meses = mensal.sort_values("mes")["mes_nome"].tolist()
        mensal["valor_mi"] = mensal["valor"] / 1e6
        col_a, col_b = st.columns(2)
        col_a.altair_chart(
            alt.Chart(mensal, title="Autos lavrados por mês").mark_bar(color=VERDE).encode(
                x=alt.X("mes_nome:O", title=None, sort=ordem_meses, axis=alt.Axis(labelAngle=0)),
                y=alt.Y("autos:Q", title="Autos"),
                tooltip=[alt.Tooltip("mes_nome:O", title="Mês"),
                         alt.Tooltip("autos:Q", title="Autos", format=",")]),
            width="stretch")
        col_b.altair_chart(
            alt.Chart(mensal, title="Valor das multas por mês (R$ milhões)").mark_bar(color=VERDE).encode(
                x=alt.X("mes_nome:O", title=None, sort=ordem_meses, axis=alt.Axis(labelAngle=0)),
                y=alt.Y("valor_mi:Q", title="R$ milhões"),
                tooltip=[alt.Tooltip("mes_nome:O", title="Mês"),
                         alt.Tooltip("valor_mi:Q", title="R$ milhões", format=",.1f")]),
            width="stretch")

        st.subheader("Onde e o quê")
        col_c, col_d = st.columns(2)
        por_uf = (f.groupby("uf").agg(autos=("num_auto_infracao", "count"), valor=("valor_multa", "sum"))
                   .reset_index().sort_values("valor", ascending=False).head(10))
        por_uf["pct"] = por_uf["valor"] / total * 100
        por_uf["valor_mi"] = por_uf["valor"] / 1e6
        uf_lider = por_uf.iloc[0]["uf"]
        col_c.altair_chart(
            alt.Chart(por_uf, title="10 UFs com maior valor de multas").mark_bar().encode(
                y=alt.Y("uf:N", sort="-x", title=None),
                x=alt.X("valor_mi:Q", title="R$ milhões"),
                color=alt.condition(alt.datum.uf == uf_lider, alt.value(DESTAQUE), alt.value(VERDE)),
                tooltip=[alt.Tooltip("uf:N", title="UF"),
                         alt.Tooltip("autos:Q", title="Autos", format=","),
                         alt.Tooltip("valor_mi:Q", title="R$ milhões", format=",.1f"),
                         alt.Tooltip("pct:Q", title="% do valor", format=".1f")]),
            width="stretch")

        por_cat = (f.groupby("tipo_infracao").agg(autos=("num_auto_infracao", "count"),
                                                  valor=("valor_multa", "sum"),
                                                  media=("valor_multa", "mean"))
                    .reset_index().sort_values("valor", ascending=False))
        por_cat["valor_mi"] = por_cat["valor"] / 1e6
        col_d.altair_chart(
            alt.Chart(por_cat, title="Valor das multas por categoria").mark_bar(color=VERDE).encode(
                y=alt.Y("tipo_infracao:N", sort="-x", title=None),
                x=alt.X("valor_mi:Q", title="R$ milhões"),
                tooltip=[alt.Tooltip("tipo_infracao:N", title="Categoria"),
                         alt.Tooltip("autos:Q", title="Autos", format=","),
                         alt.Tooltip("valor_mi:Q", title="R$ milhões", format=",.1f"),
                         alt.Tooltip("media:Q", title="Multa média (R$)", format=",.0f")]),
            width="stretch")

        st.subheader("Biomas")
        por_bioma = (f.groupby("bioma").agg(autos=("num_auto_infracao", "count"), valor=("valor_multa", "sum"))
                      .reset_index().sort_values("autos", ascending=False))
        por_bioma["Valor total"] = por_bioma["valor"].map(brl)
        por_bioma["% dos autos"] = (por_bioma["autos"] / por_bioma["autos"].sum() * 100).round(1)
        st.dataframe(por_bioma.rename(columns={"bioma": "Bioma", "autos": "Autos"})[
                         ["Bioma", "Autos", "% dos autos", "Valor total"]],
                     hide_index=True, width="stretch")

# ---------------------------------------------------------------- mapa
with aba_mapa:
    pontos = f.dropna(subset=["latitude", "longitude"])
    pontos = pontos[pontos["latitude"].between(-35, 6) & pontos["longitude"].between(-75, -30)]
    st.caption(f"{inteiro(len(pontos))} autos com coordenadas válidas. "
               "Os pontos em vermelho são autos de R$ 1 milhão ou mais.")
    if pontos.empty:
        st.warning("Nenhum auto com coordenadas para os filtros selecionados.")
    else:
        pontos = pontos.assign(cor=pontos["valor_multa"].ge(1_000_000).map({True: DESTAQUE, False: VERDE}))
        pontos = pontos.sort_values("valor_multa", na_position="first")
        st.map(pontos, latitude="latitude", longitude="longitude", color="cor", size=4000)

# ---------------------------------------------------------------- infratores e operações
with aba_infratores:
    if f.empty:
        st.warning("Nenhum auto com os filtros selecionados.")
    else:
        st.subheader("Maiores infratores por valor")
        top_inf = (f.groupby(["id_infrator", "nome_infrator", "tipo_pessoa"], dropna=False)
                    .agg(autos=("num_auto_infracao", "count"), valor=("valor_multa", "sum"),
                         ufs=("uf", lambda s: ", ".join(sorted(s.unique()))))
                    .reset_index().sort_values("valor", ascending=False).head(15))
        top_inf["valor"] = top_inf["valor"].map(brl)
        st.dataframe(top_inf.rename(columns={"nome_infrator": "Infrator", "tipo_pessoa": "Tipo",
                                             "autos": "Autos", "valor": "Valor total", "ufs": "UFs"})
                     [["Infrator", "Tipo", "Autos", "Valor total", "UFs"]],
                     hide_index=True, width="stretch")

        st.subheader("Reincidência")
        minimo = st.slider("Infratores autuados em pelo menos N ordens de fiscalização", 2, 8, 2)
        # Pares infrator-ordem (relação Autuado_Em) restritos aos autos filtrados
        reinc = (f.dropna(subset=["codigo_ordem"])
                  .groupby(["id_infrator", "nome_infrator", "tipo_pessoa"], dropna=False)
                  .agg(Ordens=("codigo_ordem", "nunique"),
                       Operações=("nome_operacao", lambda s: ", ".join(sorted(s.dropna().unique()))))
                  .reset_index())
        reinc = (reinc[reinc["Ordens"] >= minimo]
                 .sort_values(["Ordens", "nome_infrator"], ascending=[False, True])
                 .rename(columns={"nome_infrator": "Infrator", "tipo_pessoa": "Tipo"})
                 [["Infrator", "Tipo", "Ordens", "Operações"]])
        st.caption(f"{inteiro(len(reinc))} infratores em {minimo} ou mais ordens.")
        st.dataframe(reinc, hide_index=True, width="stretch", height=300)

        st.subheader("Operações com mais autos")
        ops = (f.dropna(subset=["codigo_ordem"])
                .groupby(["codigo_ordem", "nome_operacao", "unidade_ordenadora"], dropna=False)
                .agg(autos=("num_auto_infracao", "count"), municipios=("cod_municipio", "nunique"),
                     valor=("valor_multa", "sum"))
                .reset_index().sort_values("autos", ascending=False).head(15))
        ops["valor"] = ops["valor"].map(brl)
        st.dataframe(ops.rename(columns={"nome_operacao": "Operação", "unidade_ordenadora": "Unidade",
                                         "autos": "Autos", "municipios": "Municípios",
                                         "valor": "Valor total"})
                     [["Operação", "Unidade", "Autos", "Municípios", "Valor total"]],
                     hide_index=True, width="stretch")

        st.subheader("Pessoa física × jurídica")
        pfpj = (f.groupby("tipo_pessoa").agg(Autos=("num_auto_infracao", "count"),
                                             media=("valor_multa", "mean"),
                                             mediana=("valor_multa", "median"))
                 .reset_index().rename(columns={"tipo_pessoa": "Tipo"}))
        pfpj["Multa média"] = pfpj["media"].map(brl)
        pfpj["Multa mediana"] = pfpj["mediana"].map(brl)
        st.dataframe(pfpj[["Tipo", "Autos", "Multa média", "Multa mediana"]],
                     hide_index=True, width="content")

# ---------------------------------------------------------------- as 10 consultas
CONSULTAS = [
    {"secao": "6.1.1", "titulo": "Consulta 1 · Multas simples de valor alto",
     "tipo": "Seleção e projeção",
     "descricao": "Autos da modalidade Multa simples com valor igual ou acima do mínimo escolhido, "
                  "ordenados do maior para o menor.",
     "sql": """SELECT num_auto_infracao, data_hora, valor_multa, tipo_auto, bioma
FROM Auto_Infracao
WHERE valor_multa >= ? AND tipo_auto = 'Multa simples'
ORDER BY valor_multa DESC
LIMIT ?;""",
     "params": ["valor_min", "limite"]},
    {"secao": "6.1.2", "titulo": "Consulta 2 · Infratores pessoa jurídica",
     "tipo": "Seleção e projeção",
     "descricao": "Infratores cadastrados como pessoa jurídica com CNPJ registrado, em ordem alfabética.",
     "sql": """SELECT id_infrator, nome_infrator, cpf_cnpj, tipo_pessoa
FROM Infrator
WHERE tipo_pessoa = 'PJ' AND cpf_cnpj IS NOT NULL
ORDER BY nome_infrator ASC
LIMIT ?;""",
     "params": ["limite"]},
    {"secao": "6.2.1", "titulo": "Consulta 3 · Maiores multas e seus infratores",
     "tipo": "Junção de duas relações",
     "descricao": "Junção entre Auto_Infracao e Infrator para ver quem recebeu as maiores multas.",
     "sql": """SELECT a.num_auto_infracao, i.nome_infrator, i.tipo_pessoa, a.valor_multa, a.data_hora, a.bioma
FROM Auto_Infracao a
JOIN Infrator i ON a.id_infrator = i.id_infrator
WHERE a.valor_multa IS NOT NULL
ORDER BY a.valor_multa DESC
LIMIT ?;""",
     "params": ["limite"]},
    {"secao": "6.2.2", "titulo": "Consulta 4 · Multas altas por município",
     "tipo": "Junção de duas relações",
     "descricao": "Junção entre Auto_Infracao e Municipio para localizar as autuações de maior valor.",
     "sql": """SELECT a.num_auto_infracao, m.nome_municipio, m.uf, a.bioma, a.valor_multa, a.descricao_fato
FROM Auto_Infracao a
JOIN Municipio m ON a.cod_municipio = m.cod_municipio
WHERE a.valor_multa >= ?
ORDER BY a.valor_multa DESC
LIMIT ?;""",
     "params": ["valor_min", "limite"]},
    {"secao": "6.2.3", "titulo": "Consulta 5 · Autos por categoria de infração",
     "tipo": "Junção de duas relações",
     "descricao": "Junção entre Auto_Infracao e Tipo_Infracao para a categoria escolhida "
                  "(no notebook: Flora).",
     "sql": """SELECT a.num_auto_infracao, a.valor_multa, t.tipo_infracao, t.descricao_infracao, a.bioma
FROM Auto_Infracao a
JOIN Tipo_Infracao t ON a.id_tipo = t.id_tipo
WHERE t.tipo_infracao = ?
ORDER BY a.valor_multa DESC
LIMIT ?;""",
     "params": ["categoria", "limite"]},
    {"secao": "6.3.1", "titulo": "Consulta 6 · Autuações graves em uma UF",
     "tipo": "Junção de três ou mais relações",
     "descricao": "Junção entre Auto_Infracao, Infrator e Municipio para a UF escolhida "
                  "(no notebook: PA, a partir de R$ 500 mil).",
     "sql": """SELECT a.num_auto_infracao, i.nome_infrator, i.tipo_pessoa, m.nome_municipio, m.uf, a.valor_multa
FROM Auto_Infracao a
JOIN Infrator i ON a.id_infrator = i.id_infrator
JOIN Municipio m ON a.cod_municipio = m.cod_municipio
WHERE m.uf = ? AND a.valor_multa >= ?
ORDER BY a.valor_multa DESC
LIMIT ?;""",
     "params": ["uf", "valor_min", "limite"]},
    {"secao": "6.3.2", "titulo": "Consulta 7 · Operações com multas milionárias",
     "tipo": "Junção de três ou mais relações",
     "descricao": "Junção entre Auto_Infracao, Ordem_Fiscalizacao e Municipio: operações de campo "
                  "que aplicaram multas acima do valor escolhido e onde atuaram.",
     "sql": """SELECT a.num_auto_infracao, o.codigo_ordem, o.nome_operacao, o.unidade_ordenadora,
       m.nome_municipio, m.uf, a.valor_multa
FROM Auto_Infracao a
JOIN Ordem_Fiscalizacao o ON a.codigo_ordem = o.codigo_ordem
JOIN Municipio m ON a.cod_municipio = m.cod_municipio
WHERE o.nome_operacao IS NOT NULL AND a.valor_multa >= ?
ORDER BY a.valor_multa DESC
LIMIT ?;""",
     "params": ["valor_min", "limite"]},
    {"secao": "6.3.3", "titulo": "Consulta 8 · Reincidentes em várias operações (M:N)",
     "tipo": "Junção de três ou mais relações",
     "descricao": "Junção entre Infrator, Autuado_Em e Ordem_Fiscalizacao: infratores autuados em "
                  "mais de uma ordem de fiscalização.",
     "sql": """SELECT i.nome_infrator,
       i.tipo_pessoa,
       COUNT(DISTINCT ae.codigo_ordem) AS total_ordens,
       GROUP_CONCAT(DISTINCT o.nome_operacao) AS operacoes
FROM Infrator i
JOIN Autuado_Em ae ON i.id_infrator = ae.id_infrator
JOIN Ordem_Fiscalizacao o ON ae.codigo_ordem = o.codigo_ordem
GROUP BY i.id_infrator, i.nome_infrator, i.tipo_pessoa
HAVING total_ordens > 1
ORDER BY total_ordens DESC
LIMIT ?;""",
     "params": ["limite"]},
    {"secao": "6.4.1", "titulo": "Consulta 9 · Valor das multas por categoria",
     "tipo": "Agregação sobre junção",
     "descricao": "Total de autos, soma e média das multas por categoria de infração, com a participação "
                  "de cada categoria no total de autos e no valor das multas.",
     "sql": """SELECT t.tipo_infracao,
       COUNT(a.num_auto_infracao) AS total_autuacoes,
       ROUND(COUNT(a.num_auto_infracao) * 100.0 / (SELECT COUNT(*) FROM Auto_Infracao), 2) AS pct_autuacoes,
       ROUND(SUM(a.valor_multa), 2) AS valor_total_multas,
       ROUND(SUM(a.valor_multa) * 100.0 / (SELECT SUM(valor_multa) FROM Auto_Infracao), 2) AS pct_valor_multas,
       ROUND(AVG(a.valor_multa), 2) AS valor_medio_multa
FROM Auto_Infracao a
JOIN Tipo_Infracao t ON a.id_tipo = t.id_tipo
GROUP BY t.tipo_infracao
ORDER BY valor_total_multas DESC;""",
     "params": [], "grafico": ("tipo_infracao", "valor_total_multas")},
    {"secao": "6.4.2", "titulo": "Consulta 10 · Valor das multas por UF",
     "tipo": "Agregação sobre junção",
     "descricao": "Total de autos, soma e média das multas por UF, com a participação de cada estado "
                  "no total nacional de autos e no valor nacional das multas.",
     "sql": """SELECT m.uf,
       COUNT(a.num_auto_infracao) AS total_autuacoes,
       ROUND(COUNT(a.num_auto_infracao) * 100.0 / (SELECT COUNT(*) FROM Auto_Infracao), 2) AS pct_autuacoes_nacional,
       ROUND(SUM(a.valor_multa), 2) AS valor_total_multas,
       ROUND(SUM(a.valor_multa) * 100.0 / (SELECT SUM(valor_multa) FROM Auto_Infracao), 2) AS pct_valor_nacional,
       ROUND(AVG(a.valor_multa), 2) AS valor_medio_multa
FROM Auto_Infracao a
JOIN Municipio m ON a.cod_municipio = m.cod_municipio
GROUP BY m.uf
ORDER BY valor_total_multas DESC
LIMIT ?;""",
     "params": ["limite"], "grafico": ("uf", "valor_total_multas")},
]

PADROES = {"6.1.1": {"valor_min": 1_000_000}, "6.2.2": {"valor_min": 2_000_000},
           "6.3.1": {"valor_min": 500_000, "uf": "PA"}, "6.3.2": {"valor_min": 1_000_000},
           "6.2.3": {"categoria": "Flora"}}

with aba_consultas:
    st.caption("As consultas do notebook, executadas direto no banco SQLite. Os parâmetros começam com os "
               "valores usados no relatório e podem ser alterados. Os filtros da barra lateral não se aplicam aqui.")
    nomes = [f"{c['secao']} – {c['titulo']}" for c in CONSULTAS]
    escolha = st.selectbox("Consulta", nomes)
    c = CONSULTAS[nomes.index(escolha)]
    padrao = PADROES.get(c["secao"], {})

    st.markdown(f"**{c['titulo']}** · *{c['tipo']}*  \n{c['descricao']}")

    valores = {}
    cols = st.columns(max(len(c["params"]), 1))
    for col, p in zip(cols, c["params"]):
        chave = f"{c['secao']}_{p}"
        if p == "valor_min":
            valores[p] = col.number_input("Valor mínimo da multa (R$)", min_value=0,
                                          value=padrao.get("valor_min", 1_000_000), step=100_000, key=chave)
        elif p == "limite":
            valores[p] = col.slider("Linhas exibidas", 5, 50, 10, key=chave)
        elif p == "uf":
            lista = sorted(base["uf"].unique())
            valores[p] = col.selectbox("UF", lista, index=lista.index(padrao.get("uf", "PA")), key=chave)
        elif p == "categoria":
            lista = sorted(base["tipo_infracao"].unique())
            valores[p] = col.selectbox("Categoria", lista, index=lista.index(padrao.get("categoria", "Flora")),
                                       key=chave)

    params = tuple(valores[p] for p in c["params"])
    with st.expander("Ver SQL", expanded=True):
        st.code(c["sql"], language="sql")

    resultado = consultar(c["sql"], params)
    st.caption(f"{inteiro(len(resultado))} linhas retornadas.")
    config = {col: st.column_config.NumberColumn(format="R$ %.2f")
              for col in resultado.columns if col.startswith("valor")}
    config.update({col: st.column_config.NumberColumn(format="%.2f%%")
                   for col in resultado.columns if col.startswith("pct")})
    st.dataframe(resultado, hide_index=True, width="stretch", column_config=config)

    if "grafico" in c and not resultado.empty:
        eixo, medida = c["grafico"]
        g = resultado.assign(valor_mi=resultado[medida] / 1e6)
        st.altair_chart(
            alt.Chart(g).mark_bar(color=VERDE).encode(
                y=alt.Y(f"{eixo}:N", sort="-x", title=None),
                x=alt.X("valor_mi:Q", title="Valor total das multas (R$ milhões)"),
                tooltip=[alt.Tooltip(f"{eixo}:N"), alt.Tooltip("total_autuacoes:Q", title="Autos", format=","),
                         alt.Tooltip("valor_mi:Q", title="R$ milhões", format=",.1f")]),
            width="stretch")
