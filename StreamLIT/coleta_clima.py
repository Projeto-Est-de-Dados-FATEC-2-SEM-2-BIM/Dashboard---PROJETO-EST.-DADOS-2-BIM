
from __future__ import annotations

from datetime import date
from pathlib import Path
from time import sleep
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import requests


API_URL = "https://archive-api.open-meteo.com/v1/archive"
TIMEZONE = "America/Sao_Paulo"

ANOS_HISTORICO = 15
USAR_ANOS_COMPLETOS = True

PASTA_DADOS = Path("dados")
ARQUIVO_DIARIO = PASTA_DADOS / "historico_clima_completo.csv"
ARQUIVO_RESUMO_ANUAL = PASTA_DADOS / "resumo_anual_cidades.csv"
ARQUIVO_RESUMO_MENSAL = PASTA_DADOS / "resumo_mensal_cidades.csv"
ARQUIVO_TENDENCIA_CIDADES = PASTA_DADOS / "tendencia_cidades.csv"
ARQUIVO_RESUMO_BRASIL_ANUAL = PASTA_DADOS / "resumo_brasil_anual.csv"

MESES_PT = {
    1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"
}


VARIAVEIS_DIARIAS = [
    "weather_code",
    "temperature_2m_mean",
    "temperature_2m_max",
    "temperature_2m_min",
    "apparent_temperature_mean",
    "apparent_temperature_max",
    "apparent_temperature_min",
    "precipitation_sum",
    "rain_sum",
    "precipitation_hours",
    "wind_speed_10m_max",
    "relative_humidity_2m_mean",
    "cloud_cover_mean",
]

RNM_COLUM = {
    "time": "Data",
    "weather_code": "Codigo_Clima",
    "temperature_2m_mean": "Temp_Media",
    "temperature_2m_max": "Temp_Max",
    "temperature_2m_min": "Temp_Min",
    "apparent_temperature_mean": "Sensacao_Media",
    "apparent_temperature_max": "Sensacao_Max",
    "apparent_temperature_min": "Sensacao_Min",
    "precipitation_sum": "Precipitacao",
    "rain_sum": "Chuva",
    "precipitation_hours": "Horas_Precipitacao",
    "wind_speed_10m_max": "Vento_Max",
    "relative_humidity_2m_mean": "Umidade_Media",
    "cloud_cover_mean": "Nuvens_Media",
}


mapa_brasil: Dict[str, Dict[str, str]] = {
    "Norte": {
        "AC": "Rio Branco", "AM": "Manaus", "AP": "Macapa",
        "PA": "Belem", "RO": "Porto Velho", "RR": "Boa Vista", "TO": "Palmas"
    },
    "Nordeste": {
        "AL": "Maceio", "BA": "Salvador", "CE": "Fortaleza", "MA": "Sao Luis",
        "PB": "Joao Pessoa", "PE": "Recife", "PI": "Teresina", "RN": "Natal", "SE": "Aracaju"
    },
    "Centro-Oeste": {
        "DF": "Brasilia", "GO": "Goiania", "MT": "Cuiaba", "MS": "Campo Grande"
    },
    "Sudeste": {
        "ES": "Vitoria", "MG": "Belo Horizonte", "RJ": "Rio de Janeiro", "SP": "Sao Paulo"
    },
    "Sul": {
        "PR": "Curitiba", "RS": "Porto Alegre", "SC": "Florianopolis"
    }
}

coords: Dict[str, Tuple[float, float]] = {
    "Rio Branco": [-9.97, -67.81], "Manaus": [-3.11, -60.02], "Macapa": [0.03, -51.06],
    "Belem": [-1.27, -48.50], "Porto Velho": [-8.76, -63.90], "Boa Vista": [2.82, -60.67],
    "Palmas": [-10.16, -48.33], "Maceio": [-9.66, -35.73], "Salvador": [-12.97, -38.50],
    "Fortaleza": [-3.71, -38.54], "Sao Luis": [-2.53, -44.30], "Joao Pessoa": [-7.11, -34.86],
    "Recife": [-8.05, -34.88], "Teresina": [-5.09, -42.80], "Natal": [-5.79, -35.20],
    "Aracaju": [-10.91, -37.07], "Brasilia": [-15.78, -47.93], "Goiania": [-16.68, -49.25],
    "Cuiaba": [-15.60, -56.09], "Campo Grande": [-20.44, -54.64], "Vitoria": [-20.31, -40.31],
    "Belo Horizonte": [-19.92, -43.94], "Rio de Janeiro": [-22.90, -43.17], "Sao Paulo": [-23.55, -46.63],
    "Curitiba": [-25.42, -49.27], "Porto Alegre": [-30.03, -51.22], "Florianopolis": [-27.59, -48.54]
}



def calcular_periodo(
    anos: int = ANOS_HISTORICO,
    usar_anos_completos: bool = USAR_ANOS_COMPLETOS,
) -> Tuple[date, date]:
    """Define o período de coleta.

    Para evitar comparar o ano atual incompleto com anos fechados,
    o padrão usa apenas anos completos. Exemplo em 2026: 2011-01-01 a 2025-12-31.
    """
    hoje = date.today()

    if usar_anos_completos:
        ano_final = hoje.year - 1
        fim = date(ano_final, 12, 31)
        inicio = date(ano_final - anos + 1, 1, 1)
    else:
        # Pequena folga porque alguns modelos históricos não atualizam o dia atual imediatamente.
        fim = hoje
        inicio = date(hoje.year - anos, hoje.month, hoje.day)

    return inicio, fim


def listar_capitais() -> List[dict]:
    """Transforma o dicionário original em uma lista tabular de capitais."""
    capitais = []

    for regiao, estados in mapa_brasil.items():
        for estado, cidade in estados.items():
            latitude, longitude = coords[cidade]
            capitais.append({
                "Regiao": regiao,
                "Estado": estado,
                "Cidade": cidade,
                "Latitude": latitude,
                "Longitude": longitude,
            })

    return capitais


def montar_parametros(latitude: float, longitude: float, inicio: date, fim: date) -> dict:
    """Monta os parâmetros da chamada da API."""
    parametros = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": inicio.isoformat(),
        "end_date": fim.isoformat(),
        "daily": ",".join(VARIAVEIS_DIARIAS),
        "timezone": TIMEZONE,
        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh",
        "precipitation_unit": "mm",
    }

    return parametros


def requisitar_api(parametros: dict) -> dict:
    """Executa a requisição HTTP com tentativas automáticas.

    Esta função trata instabilidades comuns em APIs públicas:
    - HTTP 429: limite de requisições atingido;
    - ReadTimeout/ConnectTimeout: demora na resposta ou conexão;
    - HTTP 500/502/503/504: instabilidade temporária do servidor.

    A coleta só falha de verdade depois que todas as tentativas acabam.
    """
    max_tentativas = 12
    espera_inicial = 5
    espera_maxima = 180

    for tentativa in range(1, max_tentativas + 1):
        try:
            resposta = requests.get(
                API_URL,
                params=parametros,
                # timeout=(tempo para conectar, tempo para ler a resposta)
                timeout=(15, 180),
            )

            if resposta.status_code == 200:
                dados = resposta.json()

                if "daily" not in dados:
                    raise RuntimeError(f"Resposta sem chave 'daily': {dados}")

                return dados

            if resposta.status_code == 429:
                retry_after = resposta.headers.get("Retry-After")

                if retry_after is not None and retry_after.isdigit():
                    tempo_espera = int(retry_after)
                else:
                    tempo_espera = min(espera_inicial * tentativa, espera_maxima)

                print(
                    f"    HTTP 429: limite da API atingido. "
                    f"Aguardando {tempo_espera}s antes de tentar novamente "
                    f"({tentativa}/{max_tentativas})..."
                )
                sleep(tempo_espera)
                continue

            if resposta.status_code in [500, 502, 503, 504]:
                tempo_espera = min(espera_inicial * tentativa, espera_maxima)

                print(
                    f"    HTTP {resposta.status_code}: instabilidade temporária da API. "
                    f"Aguardando {tempo_espera}s antes de tentar novamente "
                    f"({tentativa}/{max_tentativas})..."
                )
                sleep(tempo_espera)
                continue

            raise RuntimeError(
                f"Erro HTTP {resposta.status_code}: {resposta.text[:500]}"
            )

        except requests.exceptions.ReadTimeout:
            tempo_espera = min(espera_inicial * tentativa, espera_maxima)

            print(
                f"    Timeout de leitura: a API demorou para responder. "
                f"Aguardando {tempo_espera}s antes de tentar novamente "
                f"({tentativa}/{max_tentativas})..."
            )
            sleep(tempo_espera)
            continue

        except requests.exceptions.ConnectTimeout:
            tempo_espera = min(espera_inicial * tentativa, espera_maxima)

            print(
                f"    Timeout de conexão. "
                f"Aguardando {tempo_espera}s antes de tentar novamente "
                f"({tentativa}/{max_tentativas})..."
            )
            sleep(tempo_espera)
            continue

        except requests.exceptions.ConnectionError as erro:
            tempo_espera = min(espera_inicial * tentativa, espera_maxima)

            print(
                f"    Erro de conexão: {erro}. "
                f"Aguardando {tempo_espera}s antes de tentar novamente "
                f"({tentativa}/{max_tentativas})..."
            )
            sleep(tempo_espera)
            continue

    raise RuntimeError(
        f"API não respondeu corretamente após {max_tentativas} tentativas."
    )


def coletar_cidade(cidade_info: dict, inicio: date, fim: date) -> pd.DataFrame:
    """Coleta e processa os dados de uma única capital."""
    parametros = montar_parametros(
        latitude=cidade_info["Latitude"],
        longitude=cidade_info["Longitude"],
        inicio=inicio,
        fim=fim,
    )

    dados = requisitar_api(parametros)
    df = pd.DataFrame(dados["daily"])
    df = df.rename(columns=RNM_COLUM)

    # Garante que as colunas esperadas existam mesmo se a API deixar de retornar alguma variável.
    for coluna_api, coluna_final in RNM_COLUM.items():
        if coluna_final not in df.columns:
            df[coluna_final] = pd.NA

    df["Data"] = pd.to_datetime(df["Data"])

    # Metadados geográficos
    df.insert(0, "Regiao", cidade_info["Regiao"])
    df.insert(1, "Estado", cidade_info["Estado"])
    df.insert(2, "Cidade", cidade_info["Cidade"])
    df.insert(3, "Latitude", cidade_info["Latitude"])
    df.insert(4, "Longitude", cidade_info["Longitude"])

    return preparar_dados_diarios(df)


def preparar_dados_diarios(df: pd.DataFrame) -> pd.DataFrame:
    """Cria colunas temporais, indicadores de extremos e faz limpeza básica."""
    df = df.copy()
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")

    colunas_numericas = [
        "Temp_Media", "Temp_Max", "Temp_Min", "Sensacao_Media", "Sensacao_Max", "Sensacao_Min",
        "Precipitacao", "Chuva", "Horas_Precipitacao", "Vento_Max", "Umidade_Media", "Nuvens_Media"
    ]

    for coluna in colunas_numericas:
        if coluna in df.columns:
            df[coluna] = pd.to_numeric(df[coluna], errors="coerce")

    # Fallback: se a média vier vazia, usa a média simples entre máxima e mínima.
    if "Temp_Media" in df.columns:
        df["Temp_Media"] = df["Temp_Media"].fillna((df["Temp_Max"] + df["Temp_Min"]) / 2)

    df = df.dropna(subset=["Data", "Temp_Media", "Temp_Max", "Temp_Min"])
    df = df.drop_duplicates(subset=["Cidade", "Estado", "Data"])

    df["Ano"] = df["Data"].dt.year
    df["Mes"] = df["Data"].dt.month
    df["Nome_Mes"] = df["Mes"].map(MESES_PT)
    df["Dia"] = df["Data"].dt.day
    df["Mes_Ano"] = df["Data"].dt.to_period("M").astype(str)

    df["Amplitude_Termica"] = df["Temp_Max"] - df["Temp_Min"]

    # Indicadores simples de eventos extremos.
    # Critérios didáticos e fáceis de explicar na apresentação.
    df["Dia_Quente"] = df["Temp_Max"] >= 30
    df["Dia_Muito_Quente"] = df["Temp_Max"] >= 35
    df["Dia_Frio"] = df["Temp_Min"] <= 10
    df["Dia_Chuvoso"] = df["Precipitacao"].fillna(0) >= 1
    df["Dia_Chuva_Forte"] = df["Precipitacao"].fillna(0) >= 20
    df["Dia_Extremo"] = (
        df["Dia_Muito_Quente"] | df["Dia_Frio"] | df["Dia_Chuva_Forte"]
    )

    return df


def calcular_tendencia(grupo: pd.DataFrame) -> pd.Series:
    """Calcula tendência linear simples da temperatura média anual.

    Retorna:
    - Tendencia_C_por_Ano: inclinação da reta em °C por ano.
    - Variacao_Estimada_C: variação estimada no período analisado.
    """
    grupo = grupo.dropna(subset=["Ano", "Temp_Media_Anual"]).sort_values("Ano")

    if grupo["Ano"].nunique() < 2:
        return pd.Series({
            "Tendencia_C_por_Ano": np.nan,
            "Variacao_Estimada_C": np.nan,
            "Anos_Analisados": grupo["Ano"].nunique(),
        })

    x = grupo["Ano"].astype(float).to_numpy()
    y = grupo["Temp_Media_Anual"].astype(float).to_numpy()
    inclinacao = np.polyfit(x, y, 1)[0]
    variacao = inclinacao * (x.max() - x.min())

    return pd.Series({
        "Tendencia_C_por_Ano": round(inclinacao, 4),
        "Variacao_Estimada_C": round(variacao, 2),
        "Anos_Analisados": grupo["Ano"].nunique(),
    })


def gerar_resumos(df: pd.DataFrame) -> dict:
    """Gera bases resumidas para o dashboard e para análises do README."""
    df = preparar_dados_diarios(df)

    resumo_anual_cidades = (
        df.groupby(["Regiao", "Estado", "Cidade", "Latitude", "Longitude", "Ano"], as_index=False)
        .agg(
            Temp_Media_Anual=("Temp_Media", "mean"),
            Temp_Max_Media_Anual=("Temp_Max", "mean"),
            Temp_Min_Media_Anual=("Temp_Min", "mean"),
            Maior_Temp_Max=("Temp_Max", "max"),
            Menor_Temp_Min=("Temp_Min", "min"),
            Precipitacao_Total=("Precipitacao", "sum"),
            Dias_Quentes=("Dia_Quente", "sum"),
            Dias_Muito_Quentes=("Dia_Muito_Quente", "sum"),
            Dias_Frios=("Dia_Frio", "sum"),
            Dias_Chuva_Forte=("Dia_Chuva_Forte", "sum"),
            Dias_Extremos=("Dia_Extremo", "sum"),
            Amplitude_Media=("Amplitude_Termica", "mean"),
        )
    )

    resumo_mensal_cidades = (
        df.groupby(["Regiao", "Estado", "Cidade", "Latitude", "Longitude", "Ano", "Mes", "Nome_Mes"], as_index=False)
        .agg(
            Temp_Media_Mensal=("Temp_Media", "mean"),
            Temp_Max_Media_Mensal=("Temp_Max", "mean"),
            Temp_Min_Media_Mensal=("Temp_Min", "mean"),
            Maior_Temp_Max=("Temp_Max", "max"),
            Menor_Temp_Min=("Temp_Min", "min"),
            Precipitacao_Total=("Precipitacao", "sum"),
            Dias_Quentes=("Dia_Quente", "sum"),
            Dias_Muito_Quentes=("Dia_Muito_Quente", "sum"),
            Dias_Frios=("Dia_Frio", "sum"),
            Dias_Chuva_Forte=("Dia_Chuva_Forte", "sum"),
            Dias_Extremos=("Dia_Extremo", "sum"),
            Amplitude_Media=("Amplitude_Termica", "mean"),
        )
    )

    resumo_brasil_anual = (
        df.groupby("Ano", as_index=False)
        .agg(
            Temp_Media_Brasil=("Temp_Media", "mean"),
            Temp_Max_Media_Brasil=("Temp_Max", "mean"),
            Temp_Min_Media_Brasil=("Temp_Min", "mean"),
            Precipitacao_Total=("Precipitacao", "sum"),
            Dias_Extremos=("Dia_Extremo", "sum"),
        )
    )

    linhas_tendencia = []
    for chaves, grupo in resumo_anual_cidades.groupby(["Regiao", "Estado", "Cidade", "Latitude", "Longitude"]):
        regiao, estado, cidade, latitude, longitude = chaves
        tendencia = calcular_tendencia(grupo)
        linhas_tendencia.append({
            "Regiao": regiao,
            "Estado": estado,
            "Cidade": cidade,
            "Latitude": latitude,
            "Longitude": longitude,
            "Tendencia_C_por_Ano": tendencia["Tendencia_C_por_Ano"],
            "Variacao_Estimada_C": tendencia["Variacao_Estimada_C"],
            "Anos_Analisados": tendencia["Anos_Analisados"],
        })

    tendencia_cidades = pd.DataFrame(linhas_tendencia)

    return {
        "diario": df,
        "resumo_anual_cidades": resumo_anual_cidades,
        "resumo_mensal_cidades": resumo_mensal_cidades,
        "resumo_brasil_anual": resumo_brasil_anual,
        "tendencia_cidades": tendencia_cidades,
    }


def salvar_bases(resumos: dict) -> None:
    """Salva os CSVs dentro da pasta dados."""
    PASTA_DADOS.mkdir(exist_ok=True)

    resumos["diario"].to_csv(ARQUIVO_DIARIO, index=False, encoding="utf-8-sig")
    resumos["resumo_anual_cidades"].to_csv(ARQUIVO_RESUMO_ANUAL, index=False, encoding="utf-8-sig")
    resumos["resumo_mensal_cidades"].to_csv(ARQUIVO_RESUMO_MENSAL, index=False, encoding="utf-8-sig")
    resumos["resumo_brasil_anual"].to_csv(ARQUIVO_RESUMO_BRASIL_ANUAL, index=False, encoding="utf-8-sig")
    resumos["tendencia_cidades"].to_csv(ARQUIVO_TENDENCIA_CIDADES, index=False, encoding="utf-8-sig")


def coletar_todas_capitais() -> pd.DataFrame:
    """Coleta dados de todas as capitais brasileiras."""
    inicio, fim = calcular_periodo()
    capitais = listar_capitais()
    bases = []
    erros = []

    print("=" * 70)
    print("COLETA HISTÓRICA DE CLIMA - CAPITAIS BRASILEIRAS")
    print("=" * 70)
    print(f"Período: {inicio} até {fim}")
    print(f"Capitais: {len(capitais)}")
    print(f"Variáveis: {', '.join(VARIAVEIS_DIARIAS)}")
    print("=" * 70)

    for indice, cidade_info in enumerate(capitais, start=1):
        cidade = cidade_info["Cidade"]
        estado = cidade_info["Estado"]
        regiao = cidade_info["Regiao"]

        print(f"[{indice:02d}/{len(capitais)}] Coletando {cidade}/{estado} - {regiao}...")

        try:
            df_cidade = coletar_cidade(cidade_info, inicio, fim)
            bases.append(df_cidade)
            print(f"    OK: {len(df_cidade):,} linhas")
        except Exception as erro:
            mensagem = f"Erro em {cidade}/{estado}: {erro}"
            erros.append(mensagem)
            print(f"    FALHA: {mensagem}")

        # Pausa entre cidades para reduzir chance de HTTP 429.
        sleep(1.5)

    if not bases:
        raise RuntimeError("Nenhuma cidade foi coletada com sucesso.")

    df_final = pd.concat(bases, ignore_index=True)

    if erros:
        print("\nATENÇÃO: algumas cidades falharam:")
        for erro in erros:
            print(f"- {erro}")

    return df_final


# ==========================================================
# 4. EXECUÇÃO DIRETA
# ==========================================================

if __name__ == "__main__":
    df_diario = coletar_todas_capitais()
    resumos = gerar_resumos(df_diario)
    salvar_bases(resumos)

    print("\n" + "=" * 70)
    print("COLETA FINALIZADA COM SUCESSO")
    print("=" * 70)
    print(f"Arquivo diário: {ARQUIVO_DIARIO}")
    print(f"Resumo anual por cidade: {ARQUIVO_RESUMO_ANUAL}")
    print(f"Resumo mensal por cidade: {ARQUIVO_RESUMO_MENSAL}")
    print(f"Resumo anual Brasil: {ARQUIVO_RESUMO_BRASIL_ANUAL}")
    print(f"Tendência por cidade: {ARQUIVO_TENDENCIA_CIDADES}")
    print("\nAmostra dos dados diários:")
    print(resumos["diario"].tail(10))
