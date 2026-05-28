import pandas as pd
import requests
from datetime import datetime, timedelta

# 1. Mapeamento de Capitais por Região e Estado
mapa_brasil = {
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

# Coordenadas aproximadas
coords = {
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

# 2. Configuração do Período (5 anos)
fim = datetime.now().date()
inicio = fim - timedelta(days=5*365)

dados_finais = []

print(f"--- Coletando Histórico (Max, Min, Média) de {inicio} até {fim} ---")

for regiao, estados in mapa_brasil.items():
    for uf, cidade in estados.items():
        lat, lon = coords[cidade]
        print(f"Processando: {regiao} -> {cidade}")
        
        # Chamada da API solicitando Max e Min
        url = (f"https://archive-api.open-meteo.com/v1/archive?"
               f"latitude={lat}&longitude={lon}&start_date={inicio}&end_date={fim}&"
               f"daily=temperature_2m_max,temperature_2m_min&timezone=America%2FSao_Paulo")
        
        try:
            res = requests.get(url).json()
            datas = res['daily']['time']
            temps_max = res['daily']['temperature_2m_max']
            temps_min = res['daily']['temperature_2m_min']
            
            for i in range(len(datas)):
                dt_obj = datetime.strptime(datas[i], "%Y-%m-%d")
                t_max = temps_max[i]
                t_min = temps_min[i]
                
                # Cálculo da Média Simples
                t_media = round((t_max + t_min) / 2, 2)
                
                dados_finais.append({
                    "Regiao": regiao,
                    "Estado": uf,
                    "Cidade": cidade,
                    "Ano": dt_obj.year,
                    "Mes": dt_obj.month,
                    "Dia": dt_obj.day,
                    "Temp_Max": t_max,
                    "Temp_Min": t_min,
                    "Temp_Media": t_media
                })
        except Exception as e:
            print(f"Erro em {cidade}: {e}")

# 3. Gerar DataFrame e Salvar
if dados_finais:
    df = pd.DataFrame(dados_finais)
    
    # Organizar colunas
    df = df[['Regiao', 'Estado', 'Cidade', 'Ano', 'Mes', 'Dia', 'Temp_Max', 'Temp_Min', 'Temp_Media']]
    
    print("\n--- AMOSTRA DOS DADOS ---")
    print(df.tail(10))
    
    # Salvar em CSV
    nome_arquivo = "historico_clima_completo.csv"
    df.to_csv(nome_arquivo, index=False, encoding='utf-8-sig')
    print(f"\nSucesso! Arquivo '{nome_arquivo}' gerado com todas as temperaturas.")
else:
    print("\nFalha na coleta de dados.")