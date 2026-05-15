Camada de Ingestão (ingestion.py): Serviço autónomo em Python que consome a API da OpenWeather de 30 em 30 segundos para 5 localizações representativas do distrito, modela os dados para o formato GeoJSON e injeta-os no MongoDB local.

    Camada de Armazenamento (MongoDB Compass): Base de dados NoSQL orientada a documentos que armazena o histórico completo. Utiliza indexação geográfica para otimização espacial.

    Camada de Serviço (Backend - app.py): API RESTful construída em Flask que disponibiliza os dados processados através de agregações nativas do MongoDB.

    Camada de Apresentação (Frontend - index.html): Painel analítico interativo (Dashboard) baseado em tecnologias web padrão que renderiza um mapa dinâmico e gráficos de linhas temporais.

## Tecnologias Utilizadas

    Python 3.11+: Utilizado pela sua robustez no ecossistema de dados e facilidade de integração com APIs externas.

    MongoDB (NoSQL): Justificado pela natureza fluida e semiestruturada dos dados meteorológicos (JSON) e pelo seu motor nativo de processamento de coordenadas geográficas.

    Flask: Micro-framework web para Python de execução leve, ideal para expor endpoints de dados sem a sobrecarga de servidores corporativos complexos.

    Leaflet.js: Biblioteca JavaScript de código aberto para mapas interativos, de carregamento rápido e altamente compatível com objetos geográficos.

    Chart.js: Motor gráfico em HTML5 Canvas, utilizado para renderizar tendências e séries temporais de forma limpa e responsiva.

## Estrutura de Ficheiros
Plaintext

projeto-tabd/
│
├── web/
│   └── index.html             # Interface Web Frontend (Mapa + Painel de Gráficos)
│
└── scripts/
    ├── .env                   # Variáveis de ambiente locais (Chaves e URIs)
    ├── requirements.txt       # Dependências de bibliotecas Python
    ├── ingestion.py           # Script de captura e população de dados no MongoDB
    └── app.py                 # Servidor Flask API Backend

## Pormenores Críticos e Sintaxes com Atenção Especial

Vários detalhes técnicos e de sintaxe são cruciais para o funcionamento estável do ecossistema e constituem a base de diferenciação técnica para a defesa do projeto:
1. Separação Estrita de Bibliotecas (Python Imports)

A classe MongoClient pertence estritamente ao driver nativo pymongo, enquanto a extensão flask_cors serve exclusivamente para gerir políticas de segurança de navegadores.

    Sintaxe Correta:
    Python

    from flask import Flask, jsonify
    from flask_cors import CORS
    from pymongo import MongoClient  # Importado obrigatoriamente da pymongo

2. O Ciclo de Retorno das Funções (Retorno vs None)

Ao formatar os dados brutos da API para a estrutura documental GeoJSON, a ausência explícita da instrução return faz com que o Python devolva um objeto nulo (None). Isto quebra a execução do MongoDB ao tentar efetuar a inserção (insert_one), disparando um erro de tipo (TypeError). A palavra-chave return deve encapsular diretamente a abertura do dicionário.
3. Formatação Rígida da URI do MongoDB

A especificação da Connection String (MONGO_URI) no ficheiro .env exige atenção minuciosa. Para ligações a instâncias locais autónomas sem autenticação prévia de base de dados, a presença de uma barra inclinada (/) no final da URI (ex: mongodb://127.0.0.1:27017/) pode induzir o driver a procurar um mapeamento de base de dados inexistente, resultando em erros de ligação recusada.

    Configuração Estável no .env:
    Plaintext

    MONGO_URI=mongodb://127.0.0.1:27017

4. Gestão Espacial no Leaflet.js (O Contentor CSS)

A biblioteca Leaflet necessita de calcular o espaço de desenho para renderizar os azulejos (tiles) do OpenStreetMap. Se o identificador do mapa não contiver uma regra de altura fixa definida no CSS, o elemento colapsa para 0 píxeis, tornando o mapa e os marcadores invisíveis.

    Regra CSS Obrigatória:
    CSS

    #map { width: 70%; height: 100%; } /* Altura associada ao flexbox pai */

5. Delegação de Eventos de Carga (popupopen vs click)

A associação do gráfico Chart.js ao evento de clique padrão (click) no marcador gera conflito, porque o Leaflet consome o evento de clique prioritariamente para abrir a janela informativa (Popup). O gatilho foi estrategicamente movido para o evento popupopen. Isto garante que, sempre que uma janela informativa se abre, o gráfico lê e processa as métricas sem falhas.
6. Codificação de Caracteres Especiais em URLs (encodeURIComponent)

As cidades do distrito de Aveiro possuem caracteres acentuados e espaços (ex: Águeda, Ílhavo (Praia da Barra)). O envio destes nomes em bruto através de pedidos HTTP quebra a estrutura da URL no navegador. O JavaScript exige o uso de encodeURIComponent(cidade) para converter caracteres especiais em sequências seguras (ex: espaços passam a %20), permitindo que a API Flask efetue o casamento de padrões (pattern matching) corretamente.
7. Ciclo de Vida do Chart.js (destroy)

O Chart.js armazena instâncias de desenho no elemento <canvas>. Tentar criar um gráfico novo por cima de um ativo causa sobreposição de dados na memória gráfica, gerando falhas visuais. A variável global graficoInstancia verifica a existência prévia e limpa o gráfico antigo antes de instanciar o novo:
JavaScript
        ```
            if (graficoInstancia) { graficoInstancia.destroy(); }
        ```
📈 Processamento Avançado: Pipelines de Agregação

Para justificar a complexidade académica exigida na cadeira, a API utiliza o framework de agregação nativo do MongoDB:
Obtenção do Estado Atual (/api/clima)

Utiliza um fluxo de ordenação inversa e agrupamento por cidade para extrair apenas a leitura mais recente de cada ponto geográfico, minimizando o tráfego de dados.
Python
        ```
            pipeline = [
                {"$sort": {"data_hora": -1}},
                {"$group": {
                    "_id": "$cidade",
                    "dados_recentes": {"$first": "$$ROOT"}
                }}
            ]
        ```
Histórico para o Gráfico (/api/historico/<cidade>)

Filtra os dados pela cidade selecionada, ordena de forma cronológica ascendente para o gráfico desenhar a linha corretamente da esquerda para a direita, e limita o resultado aos últimos 24 registos (representando o ciclo do dia).
Python
        ```
            pipeline = [
                {"$match": {"cidade": cidade}},
                {"$sort": {"data_hora": 1}},
                {"$limit": 24}
            ]
        ```
## Como Executar o Projeto

    Instalar Dependências: No terminal, navegue até à pasta scripts/ e execute:
    Bash

    pip install -r requirements.txt

    Configurar o Ambiente: Edite o ficheiro scripts/.env com as suas credenciais e a URI local correta.

    Iniciar a Ingestão de Dados: Num terminal dedicado, execute:
    Bash

    python scripts/ingestion.py

    Iniciar o Servidor API Backend: Num segundo terminal em simultâneo, execute:
    Bash

    python scripts/app.py

    Visualizar a Plataforma: Abra o ficheiro web/index.html num navegador de internet (através da extensão Live Server).