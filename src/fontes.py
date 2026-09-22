import io
import json
import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import execute_values
from s3_client import S3ClientFactory

# carrega as variáveis do arquivo .env
load_dotenv()

def carregar_notion_para_redshift():
    # instancia a conexão com o S3 com a classe reutilizável
    s3_client = S3ClientFactory.get_client()

    # baixar parquet do S3 e ler em memória
    buffer = io.BytesIO()
    s3_client.download_fileobj(
        Bucket=os.getenv("AWS_S3_BUCKET"),
        Key=os.getenv("AWS_S3_BUCKET_KEY_NOTION"),
        Fileobj=buffer,
    )
    buffer.seek(0)

    df = pd.read_parquet(buffer)
    # converte o df para JSON corrigindo NaN -> null e datas automaticamente
    records = json.loads(df.to_json(orient="records"))

    # gera a lista de tuplas para o PostgreSQL
    data_tuples = [(json.dumps(record),) for record in records]

    # conectar ao redshift do floci
    conn = psycopg2.connect(
        host=os.getenv("REDSHIFT_HOST"),
        port=os.getenv("REDSHIFT_PORT"),
        dbname=os.getenv("REDSHIFT_DB"),
        user=os.getenv("REDSHIFT_USER"),
        password=os.getenv("REDSHIFT_PASSWORD"),
    )

    try:
        with conn.cursor() as cursor:
            # criar a tabela automaticamente se ela não existir
            create_table_query = """
            CREATE TABLE IF NOT EXISTS source_notion (
                id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
                raw_data JSONB NOT NULL,
                ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """
            cursor.execute(create_table_query)
            cursor.execute("TRUNCATE TABLE source_notion;")

            # inserir os registros na coluna JSONB
            insert_query = "INSERT INTO source_notion (raw_data) VALUES %s"
            execute_values(cursor, insert_query, data_tuples)
            conn.commit()
            print(f"Carga concluída com sucesso! {len(data_tuples)} registros inseridos em source_notion.")
    except Exception as e:
        conn.rollback()
        print(f"Erro ao inserir dados no Redshift: {e}")
        raise
    finally:
        conn.close()
        
if __name__ == "__main__":
    carregar_notion_para_redshift()