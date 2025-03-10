from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.providers.amazon.aws.operators.ecs import EcsRunTaskOperator


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

    # ECS Container overrides para chamada do processo para a tabela wrk_movimento
    MOCK_DATA = {
        "containerOverrides": [
            { #"python", "src/main.py", "--subject", "teste", "--source-prefix", "dev-ricardo/cliente-02/2025/03/05/", "--target-prefix", "dev-ricardo/cliente-02/2025/03/05/"
                "name": "data-platform-prod-processor-container",
                "environment": [
                    {
                        "name": "AWS_REGION",
                        "value" : "us-east-1"
                    },
                    {
                        "name": "AWS_ACCESS_KEY_ID",
                        "value": "AKIAWX2IFI2JCEOAJTPS"
                    },
                    {
                        "name": "AWS_SECRET_ACCESS_KEY",
                        "value": "octakOytMEMrX0I5kuF2vvRVzrzQwATSvLZDTKKj"
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
                    "dev-ricardo/cliente-02/2025/03/05/MOCK_DATA.csv",
                    "--target-prefix",
                    "dev-ricardo/cliente-02/year=2025/month=03/day=05"
                ]
            }
        ]
    }

    NETWORK_CONFIGURATION = {
        "awsvpcConfiguration": {
            "subnets": ["subnet-06104d7dcef4c7a33", "subnet-094976734555dce73"],
            "securityGroups": ["sg-0fc6b6b4e1d401581"],
            "assignPublicIp": "ENABLED"
        }
    }

    
    # Start ECS task - wrk_movimento
    bronze_to_silver = EcsRunTaskOperator(
        task_id='bronze_to_silver',
        aws_conn_id='aws_default',
        cluster='data-platform-prod-cluster',
        overrides=MOCK_DATA,
        network_configuration=NETWORK_CONFIGURATION,
        task_definition='data-platform-prod-processor',
        launch_type='FARGATE',
        propagate_tags='TASK_DEFINITION',
        retries = 1
    )

    start_data_pipeline >> bronze_to_silver