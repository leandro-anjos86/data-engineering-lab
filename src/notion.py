from dotenv import load_dotenv
from notion_client import Client
from notion_client.helpers import iterate_paginated_api
import pandas as pd
import io
from pandas._libs import properties
from datetime import datetime, date, time, timedelta
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import boto3
from botocore.client import Config
import os

load_dotenv()

s3_client = boto3.client(
    "s3",
    endpoint_url=os.getenv("AWS_ENDPOINT_URL"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_DEFAULT_REGION"),
    config=Config(signature_version="s3v4"),
)

#token da integração
NOTION_TOKEN = os.getenv("NOTION_TOKEN")

# Database ID
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

#tabela
dados = []

#campos
nome_da_vaga = ''
cargo = None
criado_em = None
data_de_encerramento = None
data_de_inscricao = None
data_entrevista = None
empresa = ''
linkedin_empresa = ''
linkedin_vaga = ''
local_de_trabalho = ''
modelo_de_trabalho = ''
nivel = None
plataforma = None
pretensao_salarial = 0
salario_oferecido = 0
site_empresa = ''
site_inscricao = ''
status = ''
tempo_total_dias = 0
ultima_edicao = None
data_demissao = '2026-04-28'
flag_entrevista = 0

#conexão
notion = Client(auth=NOTION_TOKEN)

#consulta com paginação automática para trazer todos os registros
results = []
has_more = True
start_cursor = None

while has_more:
    #prepara os parâmetros da consulta
    kwargs = {"data_source_id": DATABASE_ID}
    
    #se houver um próximo cursor, adiciona na requisição
    if start_cursor:
        kwargs["start_cursor"] = start_cursor
        
    #executa a consulta mantendo o método original do seu código
    res = notion.data_sources.query(**kwargs)
    
    #acumula os resultados
    results.extend(res.get("results", []))
    
    #atualiza as variáveis de controle
    has_more = res.get("has_more", False)
    start_cursor = res.get("next_cursor")

response = results

#consulta
for row in response:
    data_de_encerramento = None
    data_entrevista = None
    plataforma = None
    props = row["properties"]

    nome_da_vaga = props["Nome da Vaga"]["title"][0]["plain_text"]
    status = props["Status"]["status"]["name"]
    empresa = props["Empresa"]["rich_text"][0]["plain_text"]
    cargo = props["Cargo"]["select"]["name"]
    site_empresa = props["Site Empresa"]["url"]
    linkedin_vaga = props["Linkedin Vaga"]["url"]
    linkedin_empresa = props["Linkedin Empresa"]["url"]
    site_inscricao = props["Site Inscrição"]["url"]
    modelo_de_trabalho = props["Modelo de Trabalho"]["select"]["name"]
    data_de_inscricao = props["Data de Inscrição"]["date"]["start"]
    if props["Data de Encerramento"] and props["Data de Encerramento"]["date"] is not None: data_de_encerramento = props["Data de Encerramento"]["date"]["start"]
    if props["Data Entrevista"] and props["Data Entrevista"]["date"] is not None: data_entrevista = props["Data Entrevista"]["date"]["start"]
    if props["Plataforma"] and props["Plataforma"]["select"] is not None: plataforma = props["Plataforma"]["select"]["name"]
    pretensao_salarial = props["Pretensão Salarial"]["number"]
    salario_oferecido = props["Salário Oferecido"]["number"]
    criado_em = props["Criado em"]["created_time"]
    ultima_edicao = props["Última edição"]["last_edited_time"]
    tempo_total_dias = props["Tempo Total (Dias)"]["formula"]["number"]
    local_de_trabalho = props["Local de Trabalho"]["select"]["name"]
    nivel = props["Nível"]["select"]["name"]
    flag_entrevista = props["Flag Entrevista"]["formula"]["number"]
    
    #montagem da tabela
    dados.append({
        "nome_da_vaga": nome_da_vaga,
        "status": status,
        "empresa": empresa,
        "cargo": cargo,
        "nivel": nivel,
        "modelo_de_trabalho": modelo_de_trabalho,
        "local_de_trabalho": local_de_trabalho,
        "data_de_inscricao": data_de_inscricao,
        "data_entrevista": data_entrevista,
        "data_de_encerramento": data_de_encerramento,
        "tempo_total_dias": tempo_total_dias,
        "pretensao_salarial": pretensao_salarial,
        "salario_oferecido": salario_oferecido,
        "linkedin_empresa": linkedin_empresa,
        "linkedin_vaga": linkedin_vaga,
        "site_empresa": site_empresa,
        "plataforma": plataforma,
        "site_inscricao": site_inscricao,  
        "criado_em": criado_em,        
        "ultima_edicao": ultima_edicao,
        "flag_entrevista": flag_entrevista,
    })

#dataframe
df = pd.DataFrame(dados)

#tratamento de colunas de datas vindas do Notion
df["data_de_inscricao"] = pd.to_datetime(df["data_de_inscricao"])
df["data_entrevista"] = pd.to_datetime(df["data_entrevista"])
df["data_de_encerramento"] = pd.to_datetime(df["data_de_encerramento"])
df["criado_em"] = pd.to_datetime(df["criado_em"], utc=True).dt.tz_convert("America/Sao_Paulo").dt.tz_localize(None)
df["ultima_edicao"] = pd.to_datetime(df["ultima_edicao"], utc=True).dt.tz_convert("America/Sao_Paulo").dt.tz_localize(None)

#converte a variável data_demissao para Timestamp
dt_demissao = pd.to_datetime(data_demissao)
df["data_demissao"] = dt_demissao

#carimbo no formato BIGINT em milissegundos
agora = datetime.now()
df["data_atualizacao_base"] = int(agora.timestamp() * 1000)

#flag de inscrição pós-demissão
df["flg_apos_demissao"] = (df["data_de_inscricao"] >= dt_demissao).astype(int)

#ordenação e id
df_filtrado = df[(df["flg_apos_demissao"] >= 0)].copy()
df_filtrado = df_filtrado.sort_values(by=["status", "data_de_inscricao", "criado_em"], ascending=[True, False, False])
df_filtrado.insert(0, "id", range(1, len(df_filtrado) + 1))

""""
df = pd.DataFrame(dados)
df["data_de_inscricao"] = pd.to_datetime(df["data_de_inscricao"])
df["data_entrevista"] = pd.to_datetime(df["data_entrevista"])
df["data_de_encerramento"] = pd.to_datetime(df["data_de_encerramento"])
df["criado_em"] = pd.to_datetime(df["criado_em"], utc=True).dt.tz_convert("America/Sao_Paulo").dt.tz_localize(None)
df["ultima_edicao"] = pd.to_datetime(df["ultima_edicao"], utc=True).dt.tz_convert("America/Sao_Paulo").dt.tz_localize(None)
df["data_atualizacao_base"] = pd.Timestamp.now().floor("s") #pd.to_datetime(pd.Timestamp("today")).normalize()
df["data_demissao"] = pd.to_datetime(data_demissao)
df["qtd_dias_demissao"] = (df["data_atualizacao_base"] - df["data_demissao"]).dt.days
df["flg_apos_demissao"] = (df["data_de_inscricao"] >= df["data_demissao"]).astype(int) #df["data_de_inscricao"].apply(lambda x: 1 if x >= pd.to_datetime(data_demissao) else 0)

#df["x"] = if(isnull(df["data_de_encerramento"]), pd.to_datetime(pd.Timestamp("today")).normalize(), df["data_de_encerramento"]) - df["data_de_inscricao"]).dt.days

df_filtrado = df[(df["flg_apos_demissao"] >= 0)].copy() #df[(df["flg_apos_demissao"] >= 0)]
df_filtrado = df_filtrado.sort_values(by=["status","data_de_inscricao","criado_em"], ascending=[True,False, False])
df_filtrado.insert(0, "id", range(1, len(df_filtrado) + 1))
#print(df.head(5))

"""

#converte o df para parquet em memória
buffer = io.BytesIO()
df_filtrado.to_parquet(buffer, index=False, engine="pyarrow")
buffer.seek(0)  # Volta o ponteiro para o início do arquivo em memória

#faz o upload para o bucket
s3_client.upload_fileobj(
    Fileobj=buffer,
    Bucket=os.getenv("AWS_S3_BUCKET"),
    Key=os.getenv("AWS_S3_BUCKET_KEY_NOTION"),
)