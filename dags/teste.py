from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import timedelta
from datetime import datetime


def teste(**kwargs):
    event_object = kwargs['dag_run'].conf.get('key')
    print(f'{event_object=}')

default_args = {
    "owner": "ricardo.tanaka",
    "start_date": datetime(2021, 6, 14),
    "retries": 1,
    "retry_delay": timedelta(minutes=5)
}

with DAG("teste22", default_args=default_args, schedule_interval=None, max_active_runs=30, catchup=False) as dag:
    teste_taks = PythonOperator(
        task_id = 'teste',
        python_callable = teste,
        provide_context=True
    )
