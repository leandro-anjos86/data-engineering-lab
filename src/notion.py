import io
import os
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
from notion_client import Client
from s3_client import S3ClientFactory

# carrega as variáveis do arquivo .env
load_dotenv()

def extrair_notion_para_s3():
    """
    Realiza a extração dos dados de vagas do Notion, aplica os tratamentos de colunas,
    converte para o formato Parquet e faz o upload para o S3/Floci.
    """
    # instancia o cliente do S3 utilizando a classe de conexão
    s3_client = S3ClientFactory.get_client()

    # token da integração
    NOTION_TOKEN = os.getenv("NOTION_TOKEN")
    # Database ID no notion
    DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

    if not NOTION_TOKEN or not DATABASE_ID:
        raise ValueError("NOTION_TOKEN e/ou NOTION_DATABASE_ID devem estar listados no arquivo .env")

    #conexão
    notion = Client(auth=NOTION_TOKEN)

    # consulta com paginação automática para trazer todos os registros
    print("Iniciando consulta paginada na API do Notion...")
    results = []
    has_more = True
    start_cursor = None

    while has_more:
        # prepara os parâmetros da consulta
        kwargs = {"data_source_id": DATABASE_ID}
        
        # se houver um próximo cursor, adiciona na requisição
        if start_cursor:
            kwargs["start_cursor"] = start_cursor

        # executa a consulta mantendo o método original do seu código
        res = notion.data_sources.query(**kwargs)
        
        # acumula os resultados
        results.extend(res.get("results", []))
        
        #atualiza as variáveis de controle
        has_more = res.get("has_more", False)
        start_cursor = res.get("next_cursor")

    print(f"Total de registros obtidos da API: {len(results)}")

    # processamento dos registros retornados
    dados = []
    data_demissao = "2026-04-28" # data fixa

    # consulta
    for row in results:
        data_de_encerramento = None
        data_entrevista = None
        plataforma = None
        props = row["properties"]

        # extração tratada dos campos JSON do Notion
        nome_da_vaga = props["Nome da Vaga"]["title"][0]["plain_text"] if props.get("Nome da Vaga", {}).get("title") else ""
        status = props["Status"]["status"]["name"] if props.get("Status", {}).get("status") else ""
        empresa = props["Empresa"]["rich_text"][0]["plain_text"] if props.get("Empresa", {}).get("rich_text") else ""
        cargo = props["Cargo"]["select"]["name"] if props.get("Cargo", {}).get("select") else None
        site_empresa = props["Site Empresa"]["url"] if props.get("Site Empresa") else ""
        linkedin_vaga = props["Linkedin Vaga"]["url"] if props.get("Linkedin Vaga") else ""
        linkedin_empresa = props["Linkedin Empresa"]["url"] if props.get("Linkedin Empresa") else ""
        site_inscricao = props["Site Inscrição"]["url"] if props.get("Site Inscrição") else ""
        modelo_de_trabalho = props["Modelo de Trabalho"]["select"]["name"] if props.get("Modelo de Trabalho", {}).get("select") else ""
        data_de_inscricao = props["Data de Inscrição"]["date"]["start"] if props.get("Data de Inscrição", {}).get("date") else None

        if props.get("Data de Encerramento") and props["Data de Encerramento"].get("date"):
            data_de_encerramento = props["Data de Encerramento"]["date"]["start"]

        if props.get("Data Entrevista") and props["Data Entrevista"].get("date"):
            data_entrevista = props["Data Entrevista"]["date"]["start"]

        if props.get("Plataforma") and props["Plataforma"].get("select"):
            plataforma = props["Plataforma"]["select"]["name"]

        pretensao_salarial = props["Pretensão Salarial"]["number"] if props.get("Pretensão Salarial") else 0
        salario_oferecido = props["Salário Oferecido"]["number"] if props.get("Salário Oferecido") else 0
        criado_em = props["Criado em"]["created_time"] if props.get("Criado em") else None
        ultima_edicao = props["Última edição"]["last_edited_time"] if props.get("Última edição") else None
        tempo_total_dias = props["Tempo Total (Dias)"]["formula"]["number"] if props.get("Tempo Total (Dias)", {}).get("formula") else 0
        local_de_trabalho = props["Local de Trabalho"]["select"]["name"] if props.get("Local de Trabalho", {}).get("select") else ""
        nivel = props["Nível"]["select"]["name"] if props.get("Nível", {}).get("select") else None
        flag_entrevista = props["Flag Entrevista"]["formula"]["number"] if props.get("Flag Entrevista", {}).get("formula") else 0

        # montagem da tabela
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

    # dataframe - transformação com pandas
    df = pd.DataFrame(dados)

    # tratamento de colunas de datas vindas do Notion
    df["data_de_inscricao"] = pd.to_datetime(df["data_de_inscricao"])
    df["data_entrevista"] = pd.to_datetime(df["data_entrevista"])
    df["data_de_encerramento"] = pd.to_datetime(df["data_de_encerramento"])
    df["criado_em"] = pd.to_datetime(df["criado_em"], utc=True).dt.tz_convert("America/Sao_Paulo").dt.tz_localize(None)
    df["ultima_edicao"] = pd.to_datetime(df["ultima_edicao"], utc=True).dt.tz_convert("America/Sao_Paulo").dt.tz_localize(None)

    # converte a variável data_demissao para Timestamp
    dt_demissao = pd.to_datetime(data_demissao)
    df["data_demissao"] = dt_demissao

    #c arimbo no formato BIGINT em milissegundos
    agora = datetime.now()
    df["data_atualizacao_base"] = int(agora.timestamp() * 1000)
    
    # flag de inscrição pós-demissão
    df["flg_apos_demissao"] = (df["data_de_inscricao"] >= dt_demissao).astype(int)

    # Ordenação e criação do ID numérico
    df_filtrado = df[(df["flg_apos_demissao"] >= 0)].copy()
    df_filtrado = df_filtrado.sort_values(by=["status", "data_de_inscricao", "criado_em"], ascending=[True, False, False])
    df_filtrado.insert(0, "id", range(1, len(df_filtrado) + 1))

    # conversão para parquet em memória
    buffer = io.BytesIO()
    df_filtrado.to_parquet(buffer, index=False, engine="pyarrow")
    buffer.seek(0)

    # upload para o S3/Floci
    bucket_name = os.getenv("AWS_S3_BUCKET")
    s3_key = os.getenv("AWS_S3_BUCKET_KEY_NOTION")

    s3_client.upload_fileobj(
        Fileobj=buffer,
        Bucket=bucket_name,
        Key=s3_key,
    )
    print(f"Extração concluída com sucesso! {len(df_filtrado)} registros salvos em s3://{bucket_name}/{s3_key}")


if __name__ == "__main__":
    try:
        extrair_notion_para_s3()
    except Exception as err:
        print(f"Falha ao executar a extração do Notion: {err}")

#----
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