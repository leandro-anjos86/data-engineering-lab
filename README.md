# Data Engineering Lab — Notion Analytics & Medallion Architecture

Projeto prático de Engenharia de Dados focado na construção de um pipeline *end-to-end* num ecossistema AWS emulado localmente. A solução realiza a ingestão automatizada de dados da API do Notion (formato JSONB) para o S3, carrega os dados brutos no Amazon Redshift e aplica transformações usando **dbt Core** na Arquitetura Medallion, tudo orquestrado pelo **Apache Airflow**.

---

## 🏗️ Arquitetura da Solução

```text
 [ Notion API ]
       │
       ▼
 [ Python Extractor ] ──► [ AWS S3 (Bucket: Raw) ]
                               │
                               ▼
                    [ Floci / Amazon Redshift (Raw) ] (schema: public)
                               │
                               ▼
                 [ dbt Core / Postgres Adapter ]
                   ├── 00_sources       (Declarações & Quality Tests)
                   ├── 01_staging       (stg_notion__pages — Views)
                   ├── 02_intermediate  (Regras de Negócio & Parsing JSONB)
                   └── 03_marts         (Modelagem Dimensional — Tables)
                               ▲
                               │
                [ Apache Airflow Orchestration ]
```
🛠️ Tecnologias Utilizadas

* Contentores & Ambiente: Docker, Docker Compose, WSL2 (Ubuntu)
* Infraestrutura Cloud Local: Floci / LocalStack (Emulador AWS: S3 & Amazon Redshift)
* Transformação de Dados: dbt Core (adapter dbt-postgres / dbt-redshift)
* Linguagens & Bibliotecas: Python 3.10, SQL, boto3, psycopg2, pandas
* Orquestração: Apache Airflow 2.8.1
* Versionamento: Git & GitHub

---
## 📁 Estrutura do Repositório
```text
data-engineering-lab/
├── .env.example                # Modelo de variáveis de ambiente para configuração
├── .gitignore                  # Estratégia de exclusão de binários, logs e dados sensíveis
├── README.md                   # Documentação do projeto
├── docker-compose.yml          # Setup unificado (Airflow + Floci/AWS)
├── airflow/                    # Módulo de orquestração do Airflow
│   ├── dags/                   # DAGs de orquestração (ex: dag_notion_pipeline.py)
│   └── requirements.txt      # Dependências Python adicionais do Airflow
├── dbt_lab/                    # Projeto dbt
│   ├── dbt_project.yml         # Configurações gerais e materializações do dbt
│   └── models/
│       ├── 00_sources/         # Declarações da camada Raw e testes
│       ├── 01_staging/         # Views de limpeza e unboxing inicial do JSONB
│       ├── 02_intermediate/    # Regras de negócio e desaninhamento
│       └── 03_marts/           # Tabelas dimensionais para Analytics/BI
└── src/                        # Módulos Python de extração, carga e gestão de infraestrutura
    ├── s3_client.py            # S3ClientFactory (Auto-provisionamento de S3 e Redshift)
    ├── notion.py               # Extração paginada da API do Notion e envio para o S3
    └── fontes.py               # Carga dos dados brutos do S3 para o Redshift
```
---
## ⚡ Pré-requisitos & Execução Simplificada (One-Command Setup)

Este projeto foi desenhado de forma totalmente modular e portátil. A infraestrutura inteira (orquestrador, motor de dados e emulador cloud) é inicializada a partir da raiz do repositório.

### 1. Ativar o Ambiente Virtual:
```Bash
source .venv/bin/activate
```

### 2. Configurar as Variáveis de Ambiente
Crie um ficheiro .env na raiz do projeto com base no modelo .env.example:
```Bash
cp .env.example .env
```

### 3. Inicializar o Ambiente Emulado (Docker)
Execute o comando abaixo na raiz do repositório para subir os contentores do Floci e do Airflow:
```Bash
docker compose up -d
```

### 4. Acessar a Interface e Validar
* Apache Airflow Webserver: http://localhost:8080
* Os recursos na nuvem local (Bucket S3 e Cluster Redshift na porta 7100) são auto-provisionados na primeira execução dos pipelines via S3ClientFactory.

---

## 🧪 Executando o Pipeline e dbt via CLI (Opcional)
Também é possível executar os comandos do dbt diretamente dentro do container do Airflow ou na máquina local:

### Entrar no container do Airflow
```Bash
docker exec -it airflow_local bash
```

### Navegar até ao projeto dbt
```Bash
cd /opt/airflow/dbt_lab
```

### Testar a conexão com o banco
```Bash
dbt debug
```

### Compilar e executar os modelos de staging
```Bash
dbt build --select 01_staging
```

### Executar todos os testes de qualidade de dados
```Bash
dbt test
```

---
*Desenvolvido por Leandro Anjos como parte dos laboratórios práticos de Engenharia e Arquitetura de Dados/ Analytics Engineering.*
