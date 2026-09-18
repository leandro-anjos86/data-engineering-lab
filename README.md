# Data Engineering Lab — Notion Analytics & Medallion Architecture

Projeto prático de Engenharia de Dados focado no ecossistema AWS local, práticas de Analytics Engineering com **dbt** e orquestração. O objetivo principal é ingerir dados brutos da API do Notion (formato JSONB) e transformá-los utilizando a Arquitetura Medallion.

---

## 🏗️ Arquitetura da Solução

```text
[ Notion API / Source ] 
          │
          ▼
 [ Floci / Redshift Raw ] (schema: public)
          │
          ▼
   [ dbt Core / Postgres Adapter ]
     ├── 00_sources       (Declarações e Data Quality Tests)
     ├── 01_staging       (stg_notion__pages — Views)
     ├── 02_intermediate  (Transformações e Regras de Negócio)
     └── 03_marts         (Modelagem Dimensional — Tables)
```
🛠️ Tecnologias Utilizadas
* Ambiente OS: WSL2 (Ubuntu)
* Engine/Database: Floci (Emulador do Amazon Redshift com wire protocol PostgreSQL)
* Transformação de Dados: dbt-core (dbt-postgres adapter)
* Linguagem & Scripting: Python 3.x, SQL, Bash
* Versionamento: Git & GitHub

---
```text
📁 Estrutura do Repositório
data-engineering-lab/
├── .env                        # Arquivo que carregará as variáveis/tokens/id (etc) no ambiente
├── .gitignore                  # Ignora ambientes virtuais, caches e builds do dbt
├── README.md                   # Documentação principal da solução
├── dbt_lab/                    # Projeto dbt
│   ├── dbt_project.yml         # Configurações do dbt e materializações por camada
│   ├── profiles.yml.sample     # Modelo de perfil de conexão do dbt (copiar para ~/.dbt/)
│   ├── models/
│   │   ├── 00_sources/         # Fontes e testes de qualidade da camada Raw
│   │   ├── 01_staging/         # Views de limpeza e unboxing inicial do JSONB
│   │   ├── 02_intermediate/    # Regras de negócio e desaninhamento intermediário
│   │   └── 03_marts/           # Tabelas dimensionais finais para BI/Analytics
└── src/                        # Scripts em Python para ingestão e cargas auxiliares
```
---

⚡ Pré-requisitos & Infraestrutura Local
Esta solução depende de uma infraestrutura global emulada via LocalStack/Floci para os serviços da AWS rodando na máquina local.
Navegue até a pasta da sua infraestrutura local (ex: ~/localstack) e inicie os serviços:

1. Subir os serviços de infraestrutura:
```Bash
docker compose up -d
```

2. Ativar o Ambiente Virtual:
```Bash
source .venv/bin/activate
```

3. Validar a conexão com o dbt:
```Bash
cd dbt_lab
dbt debug
```
---

🧪 Executando os Testes e Modelos dbt
Rodar os modelos Staging:
```Bash
dbt run --select staging
```

Executar testes de qualidade de dados (Data Quality):
```Bash
# Testar apenas o modelo de staging do Notion
dbt test --select stg_notion__pages

# Testar as declarações da camada de Sources
dbt test --select source:notion

# Rodar todos os testes do projeto
dbt test
```
---

Desenvolvido por Leandro Anjos como parte dos laboratórios práticos de Engenharia e Arquitetura de Dados/ Analytics Engineering.