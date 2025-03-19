import os
import urllib.parse
import unicodedata
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.operators.ecs import EcsRunTaskOperator

# Função para obter apenas o prefixo do caminho S3
def get_s3_prefix(s3_key):
    """
    Retorna apenas o prefixo do caminho S3, removendo o nome do arquivo.
    """
    return os.path.dirname(s3_key)

# Função para processar a chave S3 completa
def process_s3_key(**context):
    # Extrai a chave da configuração
    encoded_key = context['dag_run'].conf.get('key')
    print(f"Chave original: {encoded_key}")
    
    # Decodifica a chave
    decoded_key = urllib.parse.unquote(urllib.parse.unquote(encoded_key))
    print(f"Chave decodificada: {decoded_key}")
    
    # Normaliza a string conforme Unicode NFC
    normalized_key = unicodedata.normalize('NFC', decoded_key)
    print(f"Chave normalizada: {normalized_key}")
    
    # Extrai o prefixo (diretório) removendo o nome do arquivo
    prefix = get_s3_prefix(normalized_key)
    print(f"Prefixo S3: {prefix}")
    
    # Armazena no XCom para uso posterior
    context['ti'].xcom_push(key='s3_key_full', value=normalized_key)
    context['ti'].xcom_push(key='s3_prefix', value=prefix)
    
    return {
        'full_key': normalized_key,
        'prefix': prefix
    }

NETWORK_CONFIGURATION = {
    "awsvpcConfiguration": {
        "subnets": ["subnet-094976734555dce73", "subnet-06104d7dcef4c7a33"],
        "securityGroups": ["sg-0fc6b6b4e1d401581"],
        "assignPublicIp": "ENABLED"
    }
}

default_args = {
    "owner": "ricardo.tanaka",
    "start_date": datetime(2025, 3, 8),
    "retries": 0,
    "retry_delay": timedelta(minutes=5)
}

with DAG(
    'etl_mock_data_example',
    tags=['ETL', 'teste'],
    default_args=default_args,
    schedule_interval=None,
    max_active_runs=1,
    catchup=False
) as dag:

    start_data_pipeline = EmptyOperator(
        task_id="start_data_pipeline"
    )
    
    # Tarefa para decodificar e normalizar a chave S3
    process_key_task = PythonOperator(
        task_id='process_s3_key',
        python_callable=process_s3_key,
        provide_context=True
    )
   
    # Usar a chave processada no EcsRunTaskOperator
    bronze_to_silver = EcsRunTaskOperator(
        task_id='bronze_to_silver',
        aws_conn_id='aws_default',
        cluster='data-platform-prod-cluster',
        task_definition='data-platform-prod-processor',
        launch_type='FARGATE',
        overrides={
            "containerOverrides": [
                {
                    "name": "data-platform-prod-processor-container",
                    "environment": [
                        {
                            "name": "AWS_REGION",
                            "value": "us-east-1"
                        },
                        {
                            "name": "AWS_ACCESS_KEY_ID",
                            "value": ""
                        },
                        {
                            "name": "AWS_SECRET_ACCESS_KEY",
                            "value": ""
                        },
                        {
                            "name": "S3_BRONZE_BUCKET_NAME",
                            "value": "s3://data-platform-prod-datalake-bronze-463470937746"
                        },
                        {
                            "name": "S3_SILVER_BUCKET_NAME",
                            "value": "s3://data-platform-prod-datalake-silver-463470937746"
                        },
                        {
                            "name": "S3_GOLD_BUCKET_NAME",
                            "value": "s3://data-platform-prod-datalake-gold-463470937746"
                        }
                    ],
                    "command": [
                        "python",
                        "src/main.py",
                        "--subject",
                        "teste",
                        "--source-prefix",
                        "{{ ti.xcom_pull(task_ids='process_s3_key', key='s3_key_full') }}",
                        "--target-prefix",
                        "{{ ti.xcom_pull(task_ids='process_s3_key', key='s3_prefix') }}"
                    ]
                }
            ]
        },
        network_configuration=NETWORK_CONFIGURATION,
        propagate_tags='TASK_DEFINITION',
        retries=1
    )

    start_data_pipeline >> process_key_task >> bronze_to_silver