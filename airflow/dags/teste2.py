from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import timedelta
from datetime import datetime


def teste():
    print('teste')

default_args = {
    "owner": "ricardo.tanaka",
    "start_date": datetime(2021, 6, 14),
    "retries": 1,
    "retry_delay": timedelta(minutes=5)
}

with DAG("teste", default_args=default_args, schedule_interval=None, max_active_runs=30, catchup=False) as dag:
    teste_taks = PythonOperator(
        task_id = 'blablabla',
        python_callable = teste
    )
