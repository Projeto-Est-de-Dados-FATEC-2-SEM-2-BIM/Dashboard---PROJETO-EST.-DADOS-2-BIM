# Dashboard Climático das Capitais Brasileiras

## Tema do projeto

Análise histórica do clima nas capitais brasileiras, com foco em temperatura média, extremos climáticos, cidades mais quentes, sazonalidade e identificação do ano mais quente no período analisado.

A escolha do tema se justifica pela relevância social das discussões sobre clima, ondas de calor, períodos extremos e impactos urbanos. O dashboard busca transformar dados meteorológicos em informações claras para estudantes, população em geral e possíveis tomadores de decisão.

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

## Estrutura do projeto

```text
.
├── coleta_clima.py
├── dashboard_clima.py
├── requirements.txt
└── dados/
    ├── historico_clima_completo.csv
    ├── resumo_anual_cidades.csv
    ├── resumo_mensal_cidades.csv
    ├── resumo_brasil_anual.csv
    └── tendencia_cidades.csv
```

## Como rodar localmente

### 1. Criar ambiente virtual

```bash
python -m venv .venv
```

### 2. Ativar ambiente virtual

No Windows:

```bash
.venv\Scripts\activate
```

No Linux/Mac:

```bash
source .venv/bin/activate
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Coletar e salvar os dados

```bash
python coleta_clima.py
```

Esse comando cria a pasta `dados/` e salva os arquivos CSV usados pelo dashboard.

### 5. Rodar o dashboard

```bash
streamlit run dashboard_clima.py
```

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

Adicionar aqui as capturas do dashboard final depois de rodar o projeto.

Sugestão:

```text
/imagens/tela_inicial.png
/imagens/tendencia_anual.png
/imagens/cidades_mais_quentes.png
/imagens/meses_extremos.png
/imagens/sazonalidade.png
```

## Contexto das telas

- Tela inicial: apresenta os principais KPIs do período filtrado.
- Tendência anual: mostra se a temperatura média está aumentando ou diminuindo.
- Cidades mais quentes: compara capitais por temperatura média e tendência de aquecimento.
- Meses extremos: identifica meses com mais dias de calor forte, frio intenso ou chuva forte.
- Sazonalidade: mostra padrões mensais de temperatura e precipitação.
- Base de dados: permite verificar e baixar os dados filtrados usados nas análises.
