"""
dashboard_clima.py

Dashboard Streamlit para análise histórica do clima nas capitais brasileiras.

Antes de abrir o dashboard, execute:
    python coleta_clima.py

Depois execute:
    streamlit run dashboard_clima.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from coleta_clima import ARQUIVO_DIARIO, MESES_PT, preparar_dados_diarios


# ==========================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==========================================================

st.set_page_config(
    page_title="Dashboard Climático do Brasil",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
        .main {
            background: linear-gradient(180deg, #f7f7fa 0%, #fff7f5 100%);
        }

        .block-container {
            padding-top: 1.3rem;
            padding-bottom: 2rem;
            max-width: 1380px;
        }

        .hero {
            padding: 26px 30px;
            border-radius: 24px;
            background: linear-gradient(135deg, #590000 0%, #a4262c 55%, #d96b4c 100%);
            color: white;
            box-shadow: 0 14px 36px rgba(89,0,0,0.24);
            margin-bottom: 20px;
        }

        .hero h1 {
            margin: 0;
            font-size: 2.15rem;
            font-weight: 800;
            letter-spacing: -0.04em;
        }

        .hero p {
            margin-top: 10px;
            margin-bottom: 0;
            color: rgba(255,255,255,0.88);
            font-size: 1.02rem;
            line-height: 1.45;
        }

        .kpi-card {
            padding: 18px 18px 16px 18px;
            border-radius: 20px;
            background: rgba(255,255,255,0.92);
            border: 1px solid rgba(89,0,0,0.10);
            box-shadow: 0 10px 25px rgba(89,0,0,0.10);
            min-height: 128px;
        }

        .kpi-label {
            color: #6d6d6d;
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-weight: 700;
        }

        .kpi-value {
            color: #590000;
            font-size: 1.72rem;
            line-height: 1.15;
            font-weight: 850;
            margin-top: 8px;
        }

        .kpi-help {
            color: #777;
            font-size: 0.88rem;
            margin-top: 8px;
        }

        .question-box {
            padding: 16px 18px;
            border-radius: 18px;
            border: 1px solid rgba(164,38,44,0.18);
            background: linear-gradient(135deg, rgba(255,255,255,0.98), rgba(255,247,245,0.98));
            margin-bottom: 14px;
        }

        .question-box b {
            color: #590000;
        }

        div[data-testid="stMetric"] {
            background: white;
            border-radius: 18px;
            padding: 14px 16px;
            border: 1px solid rgba(89,0,0,0.08);
            box-shadow: 0 8px 20px rgba(89,0,0,0.07);
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==========================================================
# 2. FUNÇÕES DE DADOS
# ==========================================================

@st.cache_data(show_spinner=False)
def carregar_dados(caminho: str | Path) -> pd.DataFrame:
    caminho = Path(caminho)

    if not caminho.exists():
        return pd.DataFrame()

    df = pd.read_csv(caminho)
    df = preparar_dados_diarios(df)
    return df


def calcular_tendencia_anual(df_anual: pd.DataFrame, coluna_temperatura: str) -> tuple[float, float]:
    """Calcula inclinação anual e variação estimada no período filtrado."""
    df_anual = df_anual.dropna(subset=["Ano", coluna_temperatura]).sort_values("Ano")

    if df_anual["Ano"].nunique() < 2:
        return np.nan, np.nan

    x = df_anual["Ano"].astype(float).to_numpy()
    y = df_anual[coluna_temperatura].astype(float).to_numpy()
    inclinacao = np.polyfit(x, y, 1)[0]
    variacao = inclinacao * (x.max() - x.min())
    return inclinacao, variacao


def calcular_tendencia_cidades(df: pd.DataFrame) -> pd.DataFrame:
    anual = (
        df.groupby(["Regiao", "Estado", "Cidade", "Latitude", "Longitude", "Ano"], as_index=False)
        .agg(Temp_Media_Anual=("Temp_Media", "mean"))
    )

    linhas = []
    for chaves, grupo in anual.groupby(["Regiao", "Estado", "Cidade", "Latitude", "Longitude"]):
        inclinacao, variacao = calcular_tendencia_anual(grupo, "Temp_Media_Anual")
        regiao, estado, cidade, lat, lon = chaves
        linhas.append({
            "Regiao": regiao,
            "Estado": estado,
            "Cidade": cidade,
            "Latitude": lat,
            "Longitude": lon,
            "Tendencia_C_por_Ano": inclinacao,
            "Variacao_Estimada_C": variacao,
            "Anos_Analisados": grupo["Ano"].nunique(),
        })

    return pd.DataFrame(linhas)


def formatar_numero(valor: float, casas: int = 2, sufixo: str = "") -> str:
    if pd.isna(valor):
        return "Sem dados"
    texto = f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{texto}{sufixo}"


def kpi_card(titulo: str, valor: str, ajuda: str) -> None:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{titulo}</div>
            <div class="kpi-value">{valor}</div>
            <div class="kpi-help">{ajuda}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==========================================================
# 3. CARREGAMENTO
# ==========================================================

df_original = carregar_dados(ARQUIVO_DIARIO)

st.markdown(
    """
    <div class="hero">
        <h1>🌡️ Dashboard Climático das Capitais Brasileiras</h1>
        <p>
            Análise histórica de temperatura, extremos climáticos, chuva e sazonalidade nas capitais do Brasil.
            O objetivo é responder se as temperaturas médias estão aumentando, quais cidades estão mais quentes,
            quais meses são mais extremos, se há padrões sazonais e qual foi o ano mais quente no período analisado.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

if df_original.empty:
    st.error("Base de dados não encontrada.")
    st.markdown(
        """
        Para gerar a base local exigida pelo projeto, rode primeiro no terminal:

        ```bash
        python coleta_clima.py
        ```

        Depois abra o dashboard:

        ```bash
        streamlit run dashboard_clima.py
        ```
        """
    )
    st.stop()


# ==========================================================
# 4. FILTROS INTERATIVOS
# ==========================================================

st.sidebar.title("🔎 Filtros do dashboard")
st.sidebar.caption("Use os filtros para explorar regiões, cidades, anos, meses e indicadores.")

anos_disponiveis = sorted(df_original["Ano"].dropna().astype(int).unique())
ano_min, ano_max = min(anos_disponiveis), max(anos_disponiveis)

intervalo_anos = st.sidebar.slider(
    "Intervalo de anos",
    min_value=ano_min,
    max_value=ano_max,
    value=(ano_min, ano_max),
    step=1,
)

regioes_disponiveis = sorted(df_original["Regiao"].dropna().unique())
regioes_selecionadas = st.sidebar.multiselect(
    "Regiões",
    options=regioes_disponiveis,
    default=regioes_disponiveis,
)

base_pos_regiao = df_original[df_original["Regiao"].isin(regioes_selecionadas)]

cidades_disponiveis = sorted(base_pos_regiao["Cidade"].dropna().unique())
cidades_selecionadas = st.sidebar.multiselect(
    "Capitais",
    options=cidades_disponiveis,
    default=cidades_disponiveis,
)

meses_disponiveis = list(range(1, 13))
meses_selecionados = st.sidebar.multiselect(
    "Meses",
    options=meses_disponiveis,
    default=meses_disponiveis,
    format_func=lambda mes: MESES_PT.get(mes, str(mes)),
)

metrica_opcoes = {
    "Temperatura média": "Temp_Media",
    "Temperatura máxima": "Temp_Max",
    "Temperatura mínima": "Temp_Min",
    "Sensação térmica média": "Sensacao_Media",
}
metrica_label = st.sidebar.radio(
    "Indicador principal dos gráficos",
    options=list(metrica_opcoes.keys()),
    index=0,
)
metrica = metrica_opcoes[metrica_label]

mostrar_dados = st.sidebar.checkbox("Mostrar tabela de dados filtrados", value=False)


df = df_original[
    (df_original["Ano"].between(intervalo_anos[0], intervalo_anos[1]))
    & (df_original["Regiao"].isin(regioes_selecionadas))
    & (df_original["Cidade"].isin(cidades_selecionadas))
    & (df_original["Mes"].isin(meses_selecionados))
].copy()

if df.empty:
    st.warning("Nenhum dado encontrado para os filtros selecionados.")
    st.stop()


# ==========================================================
# 5. KPIs PRINCIPAIS
# ==========================================================

anual_brasil = (
    df.groupby("Ano", as_index=False)
    .agg(
        Temp_Media_Anual=("Temp_Media", "mean"),
        Temp_Max_Anual=("Temp_Max", "mean"),
        Temp_Min_Anual=("Temp_Min", "mean"),
        Dias_Extremos=("Dia_Extremo", "sum"),
        Precipitacao_Total=("Precipitacao", "sum"),
    )
)

ano_mais_quente_linha = anual_brasil.sort_values("Temp_Media_Anual", ascending=False).iloc[0]
ano_mais_quente = int(ano_mais_quente_linha["Ano"])
temp_ano_mais_quente = ano_mais_quente_linha["Temp_Media_Anual"]

cidade_mais_quente = (
    df.groupby(["Cidade", "Estado"], as_index=False)
    .agg(Temp_Media=("Temp_Media", "mean"))
    .sort_values("Temp_Media", ascending=False)
    .iloc[0]
)

mes_extremo = (
    df.groupby(["Mes", "Nome_Mes"], as_index=False)
    .agg(
        Dias_Extremos=("Dia_Extremo", "sum"),
        Temp_Max_Media=("Temp_Max", "mean"),
        Precipitacao_Total=("Precipitacao", "sum"),
    )
    .sort_values(["Dias_Extremos", "Temp_Max_Media"], ascending=False)
    .iloc[0]
)

tendencia_geral, variacao_geral = calcular_tendencia_anual(anual_brasil, "Temp_Media_Anual")
tendencia_cidades = calcular_tendencia_cidades(df)
cidade_maior_aquecimento = tendencia_cidades.sort_values("Tendencia_C_por_Ano", ascending=False).iloc[0]

col1, col2, col3, col4 = st.columns(4)

with col1:
    sinal = "+" if tendencia_geral > 0 else ""
    kpi_card(
        "Tendência geral",
        f"{sinal}{formatar_numero(tendencia_geral, 3, ' °C/ano')}",
        f"Variação estimada no período: {formatar_numero(variacao_geral, 2, ' °C')}",
    )

with col2:
    kpi_card(
        "Ano mais quente",
        str(ano_mais_quente),
        f"Temperatura média: {formatar_numero(temp_ano_mais_quente, 2, ' °C')}",
    )

with col3:
    kpi_card(
        "Cidade mais quente",
        f"{cidade_mais_quente['Cidade']}/{cidade_mais_quente['Estado']}",
        f"Média no filtro: {formatar_numero(cidade_mais_quente['Temp_Media'], 2, ' °C')}",
    )

with col4:
    kpi_card(
        "Mês mais extremo",
        str(mes_extremo["Nome_Mes"]),
        f"{int(mes_extremo['Dias_Extremos'])} dias extremos no filtro",
    )

st.caption(
    "Critério de dia extremo usado no dashboard: temperatura máxima ≥ 35 °C, ou temperatura mínima ≤ 10 °C, ou precipitação diária ≥ 20 mm."
)


# ==========================================================
# 6. ABAS DE ANÁLISE
# ==========================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Tendência anual",
    "🏙️ Cidades mais quentes",
    "🔥 Meses extremos",
    "🗓️ Sazonalidade",
    "📋 Base de dados",
])


with tab1:
    st.markdown(
        """
        <div class="question-box">
            <b>Pergunta respondida:</b> As temperaturas médias estão aumentando ao longo dos anos?
            <br>O gráfico abaixo compara a temperatura média anual no período filtrado e calcula uma tendência linear simples.
        </div>
        """,
        unsafe_allow_html=True,
    )

    fig_tendencia = px.line(
        anual_brasil,
        x="Ano",
        y="Temp_Media_Anual",
        markers=True,
        title="Temperatura média anual no período filtrado",
        labels={"Temp_Media_Anual": "Temperatura média anual (°C)", "Ano": "Ano"},
    )
    fig_tendencia.update_traces(line_width=3)
    fig_tendencia.update_layout(height=460, hovermode="x unified")
    st.plotly_chart(fig_tendencia, use_container_width=True)

    if tendencia_geral > 0:
        st.success(
            f"No recorte selecionado, a tendência é de aumento: aproximadamente "
            f"{formatar_numero(tendencia_geral, 3, ' °C por ano')} "
            f"({formatar_numero(variacao_geral, 2, ' °C')} no período)."
        )
    elif tendencia_geral < 0:
        st.info(
            f"No recorte selecionado, a tendência calculada é de queda: aproximadamente "
            f"{formatar_numero(tendencia_geral, 3, ' °C por ano')} "
            f"({formatar_numero(variacao_geral, 2, ' °C')} no período)."
        )
    else:
        st.info("No recorte selecionado, a tendência ficou praticamente estável.")

    top_aquecimento = tendencia_cidades.sort_values("Tendencia_C_por_Ano", ascending=False).head(10)

    fig_aquecimento = px.bar(
        top_aquecimento,
        x="Tendencia_C_por_Ano",
        y="Cidade",
        orientation="h",
        title="Capitais com maior tendência de aquecimento",
        labels={"Tendencia_C_por_Ano": "Tendência (°C/ano)", "Cidade": "Capital"},
        hover_data=["Estado", "Regiao", "Variacao_Estimada_C"],
    )
    fig_aquecimento.update_layout(height=470, yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_aquecimento, use_container_width=True)


with tab2:
    st.markdown(
        """
        <div class="question-box">
            <b>Perguntas respondidas:</b> Quais cidades estão ficando mais quentes? Quais cidades são mais quentes no recorte analisado?
            <br>Aqui o dashboard combina média de temperatura e tendência de aquecimento por capital.
        </div>
        """,
        unsafe_allow_html=True,
    )

    cidade_media = (
        df.groupby(["Regiao", "Estado", "Cidade", "Latitude", "Longitude"], as_index=False)
        .agg(
            Temp_Media=("Temp_Media", "mean"),
            Temp_Max=("Temp_Max", "mean"),
            Temp_Min=("Temp_Min", "mean"),
            Dias_Extremos=("Dia_Extremo", "sum"),
            Precipitacao_Total=("Precipitacao", "sum"),
        )
        .merge(
            tendencia_cidades[["Cidade", "Estado", "Tendencia_C_por_Ano", "Variacao_Estimada_C"]],
            on=["Cidade", "Estado"],
            how="left",
        )
    )

    ranking_cidades = cidade_media.sort_values("Temp_Media", ascending=False).head(15)

    col_bar, col_map = st.columns([1.05, 1])

    with col_bar:
        fig_ranking = px.bar(
            ranking_cidades,
            x="Temp_Media",
            y="Cidade",
            orientation="h",
            title="Ranking de capitais por temperatura média",
            labels={"Temp_Media": "Temperatura média (°C)", "Cidade": "Capital"},
            hover_data=["Estado", "Regiao", "Temp_Max", "Temp_Min", "Tendencia_C_por_Ano"],
        )
        fig_ranking.update_layout(height=520, yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_ranking, use_container_width=True)

    with col_map:
        fig_mapa = px.scatter_geo(
            cidade_media,
            lat="Latitude",
            lon="Longitude",
            size="Temp_Media",
            color="Temp_Media",
            hover_name="Cidade",
            hover_data={
                "Estado": True,
                "Regiao": True,
                "Temp_Media": ":.2f",
                "Tendencia_C_por_Ano": ":.4f",
                "Latitude": False,
                "Longitude": False,
            },
            title="Distribuição das temperaturas médias nas capitais",
            projection="natural earth",
        )
        fig_mapa.update_geos(fitbounds="locations", visible=False)
        fig_mapa.update_layout(height=520, margin=dict(l=0, r=0, t=55, b=0))
        st.plotly_chart(fig_mapa, use_container_width=True)

    st.dataframe(
        cidade_media.sort_values("Tendencia_C_por_Ano", ascending=False)[[
            "Regiao", "Estado", "Cidade", "Temp_Media", "Tendencia_C_por_Ano", "Variacao_Estimada_C", "Dias_Extremos"
        ]],
        use_container_width=True,
        hide_index=True,
    )


with tab3:
    st.markdown(
        """
        <div class="question-box">
            <b>Pergunta respondida:</b> Quais meses são mais extremos climaticamente?
            <br>O mês extremo considera calor forte, frio intenso ou chuva forte dentro do recorte selecionado.
        </div>
        """,
        unsafe_allow_html=True,
    )

    mensal_extremos = (
        df.groupby(["Mes", "Nome_Mes"], as_index=False)
        .agg(
            Dias_Extremos=("Dia_Extremo", "sum"),
            Dias_Muito_Quentes=("Dia_Muito_Quente", "sum"),
            Dias_Frios=("Dia_Frio", "sum"),
            Dias_Chuva_Forte=("Dia_Chuva_Forte", "sum"),
            Temp_Max_Media=("Temp_Max", "mean"),
            Precipitacao_Total=("Precipitacao", "sum"),
        )
        .sort_values("Mes")
    )

    fig_extremos = px.bar(
        mensal_extremos,
        x="Nome_Mes",
        y=["Dias_Muito_Quentes", "Dias_Frios", "Dias_Chuva_Forte"],
        title="Quantidade de eventos extremos por mês",
        labels={"value": "Quantidade de dias", "Nome_Mes": "Mês", "variable": "Tipo de extremo"},
    )
    fig_extremos.update_layout(height=480, barmode="stack")
    st.plotly_chart(fig_extremos, use_container_width=True)

    matriz = (
        df.groupby(["Ano", "Mes"], as_index=False)
        .agg(Temp_Media=("Temp_Media", "mean"))
        .pivot(index="Ano", columns="Mes", values="Temp_Media")
        .sort_index()
    )
    matriz = matriz.rename(columns=MESES_PT)

    fig_heat = go.Figure(
        data=go.Heatmap(
            z=matriz.values,
            x=list(matriz.columns),
            y=list(matriz.index),
            colorbar=dict(title="°C"),
            hovertemplate="Ano: %{y}<br>Mês: %{x}<br>Temp. média: %{z:.2f} °C<extra></extra>",
        )
    )
    fig_heat.update_layout(
        title="Mapa de calor: temperatura média por ano e mês",
        xaxis_title="Mês",
        yaxis_title="Ano",
        height=520,
    )
    st.plotly_chart(fig_heat, use_container_width=True)


with tab4:
    st.markdown(
        """
        <div class="question-box">
            <b>Pergunta respondida:</b> Existem padrões sazonais bem definidos?
            <br>Esta visão mostra a média histórica por mês, permitindo observar meses mais quentes, frios e chuvosos.
        </div>
        """,
        unsafe_allow_html=True,
    )

    agrupamento_sazonal = st.radio(
        "Comparar sazonalidade por:",
        options=["Brasil filtrado", "Região", "Cidade"],
        horizontal=True,
    )

    if agrupamento_sazonal == "Brasil filtrado":
        sazonal = (
            df.groupby(["Mes", "Nome_Mes"], as_index=False)
            .agg(
                Temp_Media=("Temp_Media", "mean"),
                Temp_Max=("Temp_Max", "mean"),
                Temp_Min=("Temp_Min", "mean"),
                Precipitacao=("Precipitacao", "mean"),
            )
            .sort_values("Mes")
        )
        linha = None
    elif agrupamento_sazonal == "Região":
        sazonal = (
            df.groupby(["Regiao", "Mes", "Nome_Mes"], as_index=False)
            .agg(Temp_Media=("Temp_Media", "mean"), Precipitacao=("Precipitacao", "mean"))
            .sort_values("Mes")
        )
        linha = "Regiao"
    else:
        sazonal = (
            df.groupby(["Cidade", "Mes", "Nome_Mes"], as_index=False)
            .agg(Temp_Media=("Temp_Media", "mean"), Precipitacao=("Precipitacao", "mean"))
            .sort_values("Mes")
        )
        linha = "Cidade"

    fig_sazonal_temp = px.line(
        sazonal,
        x="Nome_Mes",
        y="Temp_Media",
        color=linha,
        markers=True,
        title="Sazonalidade da temperatura média",
        labels={"Nome_Mes": "Mês", "Temp_Media": "Temperatura média (°C)"},
    )
    fig_sazonal_temp.update_traces(line_width=3)
    fig_sazonal_temp.update_layout(height=460, hovermode="x unified")
    st.plotly_chart(fig_sazonal_temp, use_container_width=True)

    fig_sazonal_chuva = px.bar(
        sazonal,
        x="Nome_Mes",
        y="Precipitacao",
        color=linha,
        title="Média diária de precipitação por mês",
        labels={"Nome_Mes": "Mês", "Precipitacao": "Precipitação média diária (mm)"},
    )
    fig_sazonal_chuva.update_layout(height=440)
    st.plotly_chart(fig_sazonal_chuva, use_container_width=True)


with tab5:
    st.markdown(
        """
        <div class="question-box">
            <b>Base de dados local:</b> esta aba ajuda a comprovar o requisito do projeto de armazenar os dados em arquivo CSV antes de carregá-los no dashboard.
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Linhas filtradas", f"{len(df):,}".replace(",", "."))
    col_b.metric("Capitais filtradas", df["Cidade"].nunique())
    col_c.metric("Período filtrado", f"{df['Ano'].min()} - {df['Ano'].max()}")

    if mostrar_dados:
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Ative 'Mostrar tabela de dados filtrados' na barra lateral para visualizar a base diária completa.")

    csv_filtrado = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button(
        label="⬇️ Baixar dados filtrados em CSV",
        data=csv_filtrado,
        file_name="dados_clima_filtrados.csv",
        mime="text/csv",
    )
