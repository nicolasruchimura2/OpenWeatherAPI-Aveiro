import os
from datetime import datetime, timezone
import requests
from pymongo import MongoClient
from dotenv import load_dotenv
import time

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")


CIDADES_AVEIRO = [
    {"nome": "Aveiro (Centro)", "lat": 40.6443, "lon": -8.6455},          # Litoral / Ria
    {"nome": "Águeda", "lat": 40.5741, "lon": -8.4536},                  # Interior / Vale
    {"nome": "Ílhavo (Praia da Barra)", "lat": 40.6413, "lon": -8.7484},  # Costa / Marítimo
    {"nome": "Santa Maria da Feira", "lat": 40.9257, "lon": -8.5431},     # Norte do Distrito
    {"nome": "Arouca", "lat": 40.9293, "lon": -8.2458}                    # Interior / Altitude
]

def obter_dados_meteorologicos(lat,lon):
    """Faz o pedido dos dados do tempo pela API da OpenWeather"""
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=pt"
    resposta = requests.get(url)

    if resposta.status_code == 200: #Sucesso
        return resposta.json()
    return None

def formatar_para_geojson(dados, nome_cidade):
    """Formata a resposta da API para um documento compativel com o padrao GeoJSON"""
    coordenadas = [dados["coord"]["lon"], dados["coord"]["lat"]]
#Os dados das coordenadas sao dados em matriz longitude x latitude
    return {
        "localizacao":{
            "type":"Point",
            "coordinates":coordenadas
        },
        "cidade": nome_cidade,
        "data_hora": datetime.now(timezone.utc).isoformat(),
        "clima":{
            "temperatura": dados["main"]["temp"],
            "humidade":dados["main"]["humidity"],
            "vento_velocidade": dados["wind"]["speed"],
            "condicao": dados["weather"][0]["description"]
        },
        # Ou o tempo extremo tem a velocidade do vento maio que 20 ou a temperatura maior que 35 graus Celsius
        "tempo_extremo": dados["wind"]["speed"] > 20 or dados["main"]["temp"] > 35
    }

def executar_ciclo():
    cliente = MongoClient(MONGO_URI)
    colecao = cliente["tabd_aveiro"]["historico_clima"]
    colecao.create_index([("localizacao", "2dsphere")])
# colecao esta adicionando cada localizacao com o historico de clima, na base de dados MONGODB
    print("Servico de Ingestao Activo. Os dados sao recolhidos a cada 30 segundos...")

    try:
        while True:
            for local in CIDADES_AVEIRO:
                dados_api = obter_dados_meteorologicos(local["lat"], local["lon"])
                if dados_api: # os dados sao adicionados na variavel doc, que formata para json e incrementa na colecao
                    doc = formatar_para_geojson(dados_api, local["nome"])
                    colecao.insert_one(doc)
                    print(f"Dados de {local['nome']} atualizados no MongoDB") 
# deixando o tempo de recolha de dados com delay
                    time.sleep(30)
    except KeyboardInterrupt:
        print("Ingestao interrompida pelo utilizador.")
    finally:
        cliente.close() # encerra a sessao utilizador-db

if __name__ == "__main__":
    executar_ciclo()
