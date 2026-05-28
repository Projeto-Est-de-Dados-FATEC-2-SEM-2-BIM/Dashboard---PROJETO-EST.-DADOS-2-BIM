# Dashboard Climático das Capitais Brasileiras

## Tema do projeto

Análise histórica do clima nas capitais brasileiras, com foco em temperatura média, extremos climáticos, cidades mais quentes, sazonalidade e identificação do ano mais quente no período analisado.

## Fonte dos dados

Os dados são coletados pela API pública Open-Meteo Historical Weather API.

Fonte: https://open-meteo.com/en/docs/historical-weather-api

A API retorna dados históricos por latitude e longitude, incluindo variáveis diárias como temperatura média, temperatura máxima, temperatura mínima, precipitação, chuva, vento, umidade e cobertura de nuvens.

## Perguntas-chave respondidas pelo dashboard

1. As temperaturas médias estão aumentando ao longo dos anos?
2. Quais cidades estão ficando mais quentes?
3. Quais cidades apresentam maiores temperaturas médias?
4. Quais meses são mais extremos climaticamente?
5. Existem padrões sazonais bem definidos?
6. Qual foi o ano mais quente registrado no período analisado?


## Como rodar localmente

### 1. Criar ambiente virtual

python -m venv .venv

### 2. Ativar ambiente virtual

.venv\Scripts\activate


### 3. Instalar dependências

pip install -r requirements.txt


### 4. Coletar e salvar os dados

python coleta_clima.py


Esse comando cria a pasta dados e salva os arquivos CSV usados pelo dashboard.

### 5. Rodar o dashboard

streamlit run dashboard_clima.py

## Tratamento dos dados

O projeto realiza as seguintes etapas de tratamento:

- Conversão da coluna de data para formato datetime.
- Conversão de colunas climáticas para valores numéricos.
- Remoção de linhas sem temperatura média, máxima ou mínima.
- Remoção de duplicidades por cidade, estado e data.
- Criação de colunas auxiliares: ano, mês, nome do mês, dia e mês/ano.
- Cálculo da amplitude térmica diária.
- Criação de indicadores de extremos climáticos:
  - dia quente: temperatura máxima maior ou igual a 30 °C;
  - dia muito quente: temperatura máxima maior ou igual a 35 °C;
  - dia frio: temperatura mínima menor ou igual a 10 °C;
  - dia chuvoso: precipitação maior ou igual a 1 mm;
  - dia de chuva forte: precipitação maior ou igual a 20 mm;
  - dia extremo: dia muito quente, ou dia frio, ou dia de chuva forte.

## Capturas de tela

tela_inicial.png
tendencia_anual.png
cidades_mais_quentes.png
meses_extremos.png
sazonalidade.png


## Contexto das telas

- Tela inicial: apresenta os principais KPIs do período filtrado.
- Tendência anual: mostra se a temperatura média está aumentando ou diminuindo.
- Cidades mais quentes: compara capitais por temperatura média e tendência de aquecimento.
- Meses extremos: identifica meses com mais dias de calor forte, frio intenso ou chuva forte.
- Sazonalidade: mostra padrões mensais de temperatura e precipitação.
- Base de dados: permite verificar e baixar os dados filtrados usados nas análises.
