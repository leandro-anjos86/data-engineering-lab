with teste as (
select
      id as bronze_id
    , ingested_at
    , (raw_data->>'id')::int as id
    , raw_data->>'nome_da_vaga' as nome_da_vaga
    , raw_data->>'status' as status
    , raw_data->>'empresa' as empresa
    , raw_data->>'cargo' as cargo
    , raw_data->>'nivel' as nivel
    , raw_data->>'modelo_de_trabalho' as modelo_de_trabalho
    , raw_data->>'local_de_trabalho' as local_de_trabalho
    , to_timestamp((raw_data->>'data_de_inscricao')::bigint/1000)::timestamp as data_de_inscricao
    , to_timestamp((raw_data->>'data_entrevista')::bigint/1000)::timestamp as data_entrevista
    , to_timestamp((raw_data->>'data_de_encerramento')::bigint/1000)::timestamp as data_de_encerramento
    , (raw_data->>'pretensao_salarial')::numeric as pretensao_salarial
    , (raw_data->>'salario_oferecido')::numeric as salario_oferecido
    , raw_data->>'linkedin_empresa' as linkedin_empresa
    , raw_data->>'linkedin_vaga' as linkedin_vaga
    , raw_data->>'site_empresa' as site_empresa
    , raw_data->>'plataforma' as plataforma
    , raw_data->>'site_inscricao' as site_inscricao
    , to_timestamp((raw_data->>'criado_em')::bigint/1000)::timestamp as criado_em
    , to_timestamp((raw_data->>'ultima_edicao')::bigint/1000)::timestamp as ultima_edicao
    , to_timestamp((raw_data->>'data_atualizacao_base')::bigint/1000)::timestamp as data_atualizacao_base
    , to_timestamp((raw_data->>'data_demissao')::bigint/1000)::timestamp as data_demissao
    , (raw_data->>'flag_entrevista')::int as flag_entrevista
    , (raw_data->>'flg_apos_demissao')::int as flg_apos_demissao 
from {{ source('notion', 'source_notion') }}
order by 5 asc, 11 desc,21 desc
)

select
  /*fnv_hash(md5(concat(nome_da_vaga,'|',empresa,'|',data_de_inscricao))) as pk_campo_concat
  , */md5(concat(nome_da_vaga,'|',empresa,'|',data_de_inscricao,'|',criado_em)) as campo_md5 
, *
from teste