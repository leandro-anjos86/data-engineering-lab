from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

# Importação das funções da pasta src/
from src.notion import extrair_notion_para_s3
from src.fontes import carregar_notion_para_redshift

default_args = {
    'owner': 'leandro_anjos',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

with DAG(
    'pipeline_notion_to_dbt',
    default_args=default_args,
    description='Pipeline de Ingestão do Notion para S3, Redshift e Transformação no dbt',
    schedule_interval='0 7 * * *',  # Executa diariamente às 07h
    catchup=False,
) as dag:

    # Task 1: Ingestão Notion -> S3 (Parquet)
    task_extrair_notion = PythonOperator(
        task_id='extrair_notion_para_s3',
        python_callable=extrair_notion_para_s3,
    )

    # Task 2: Carga S3 -> Redshift (JSONB)
    task_carregar_redshift = PythonOperator(
        task_id='carregar_notion_para_redshift',
        python_callable=carregar_notion_para_redshift,
    )

    # Task 3: Execução do dbt Staging
    task_dbt_run_staging = BashOperator(
        task_id='dbt_run_staging',
        bash_command='cd /opt/airflow/dbt_lab && dbt build --select 01_staging',
    )

    # Ordem de Execução
    task_extrair_notion >> task_carregar_redshift >> task_dbt_run_staging