import os
from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

app = Flask(__name__)
CORS(app) # Permite pedidos vindos da App Frontend

# Defining routes
@app.route("/api/clima", methods= ["GET"])
def obter_clima_atual():
    cliente = MongoClient(MONGO_URI)
    colecao = cliente["tabd_aveiro"]["historico_clima"]

    #Pipeline criada para obter o documento mais recente de cada cidade
    pipeline = [
        {"$sort": {"data_hora": -1}},
        {
            "$group":{
                "_id":"$cidade",
                "dados_recentes": {"$first":"$$ROOT"}
            }
        }
    ]
    
    resultados = list(colecao.aggregate(pipeline))
    dados_finais = []

    for item in resultados:
        doc = item["dados_recentes"]
        doc["_id"] = str(doc["_id"]) # Conversao do ObjectID do MongoDB para String
        dados_finais.append(doc)

    cliente.close()
    return jsonify(dados_finais)

@app.route("/api/historico/<cidade>", methods=["GET"])
def obter_historico(cidade):
    cliente = MongoClient(MONGO_URI)
    colecao = cliente["tabd_aveiro"]["historico_clima"]
# Pipeline corre o historico das ultimas 24 leituras
    pipeline = [
        {"$match":{"cidade":cidade}},
        {"$sort":{"data_hora":1}}, # 1 para ordem crescente (cronologica)
        {"$limit":24} # maximo de horas
    ]

    historico = list(colecao.aggregate(pipeline))

    for doc in historico:
        doc["_id"] = str(doc["_id"])
    cliente.close()
    return jsonify(historico)



if __name__ == "__main__":
    app.run(debug=True, port=5000)