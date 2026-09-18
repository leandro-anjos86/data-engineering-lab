# %%
from dotenv import load_dotenv
import os
import io
import json
import pandas as pd
import psycopg2
import boto3
from botocore.client import Config
from psycopg2.extras import execute_values

# %%
load_dotenv()

s3_client = boto3.client(
    "s3",
    endpoint_url=os.getenv("AWS_ENDPOINT_URL"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_DEFAULT_REGION"),
    config=Config(signature_version="s3v4"),
)

# %%
# 1. Baixar Parquet e ler em memória
buffer = io.BytesIO()
s3_client.download_fileobj(
    Bucket=os.getenv("AWS_S3_BUCKET"),
    Key=os.getenv("AWS_S3_BUCKET_KEY_NOTION"),
    Fileobj=buffer,
)
buffer.seek(0)

df = pd.read_parquet(buffer)
records = df.to_dict(orient="records")

# %%
# 2. Conectar ao Redshift do Floci
conn = psycopg2.connect(
    host=os.getenv("REDSHIFT_HOST"),
    port=os.getenv("REDSHIFT_PORT"),
    dbname=os.getenv("REDSHIFT_DB"),
    user=os.getenv("REDSHIFT_USER"),
    password=os.getenv("REDSHIFT_PASSWORD"),
)

cursor = conn.cursor()

# %%
# 3. Criar a tabela automaticamente se ela não existir
create_table_query = """
CREATE TABLE IF NOT EXISTS source_notion (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    raw_data JSONB NOT NULL,
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
"""
cursor.execute(create_table_query)
cursor.execute("TRUNCATE TABLE source_notion;")

# %%
# 4. Inserir os registros na coluna JSONB
insert_query = "INSERT INTO source_notion (raw_data) VALUES %s"
# 1. Converte o DataFrame para JSON corrigindo NaN -> null e datas automaticamente
records = json.loads(df.to_json(orient="records"))

# 2. Gera a lista de tuplas para o PostgreSQL
data_tuples = [(json.dumps(record),) for record in records]

execute_values(cursor, insert_query, data_tuples)

# %%
# 5. Confirmar transação e fechar conexão
conn.commit()
cursor.close()
conn.close()