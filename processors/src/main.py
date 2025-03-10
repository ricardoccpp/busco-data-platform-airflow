"""Controla a execução dos processos de carga das tabelas do database consumed"""
import os
import argparse
import logging
import time
from typing import Optional
import duckdb

from utils.helpers import calcula_tempo_execucao
from utils.helpers_duckdb import create_s3_secret

from bronze_to_silver.transform import processar_mock_data

# Carregar variáveis de ambiente
def get_env(name: str, default: Optional[str] = None) -> str:
    """Obtém variável de ambiente com valor padrão."""
    value = os.environ.get(name, default)
    if value is None:
        raise ValueError(f"Variável de ambiente {name} não definida")
    return value

def processar_tabelas(
        subject: str,
        source_prefix: str,
        target_prefix: str
    ) -> None:

    S3_BRONZE_BUCKET_NAME = get_env('S3_BRONZE_BUCKET_NAME', '')
    S3_SILVER_BUCKET_NAME = get_env('S3_SILVER_BUCKET_NAME', '')
    S3_GOLD_BUCKET_NAME = get_env('S3_GOLD_BUCKET_NAME', '')
    AWS_ACCESS_KEY_ID = get_env('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = get_env('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = get_env('AWS_REGION')

    try:
        db_name = f'{str.lower(subject)}_duck_db.db'

        if os.path.exists(db_name):
            os.remove(db_name)
            logging.info('DB local removido')
        else:
            logging.info('DB local não existe')

        conn = duckdb.connect(db_name)
        create_s3_secret(conn, access_key=AWS_ACCESS_KEY_ID, secret_key=AWS_SECRET_ACCESS_KEY, region=AWS_REGION)

    except Exception as e:
        conn.close()
        return

    S3_SOURCE_PATH = f'{S3_BRONZE_BUCKET_NAME}/{source_prefix}'
    S3_TARGET_PATH = f'{S3_SILVER_BUCKET_NAME}/{target_prefix}'
    logging.info(f'{S3_SOURCE_PATH=}')
    logging.info(f'{S3_TARGET_PATH=}')
    try:
        processar_mock_data(conn, S3_SOURCE_PATH, S3_TARGET_PATH)
    except Exception as e:
        logging.error(f'Falha ao processar {subject}')
        conn.close()
        raise e

    conn.close()
    ts_fim = time.time()
    logging.info('Tempo total de processamento: %s', calcula_tempo_execucao(ts_ini, ts_fim))

def parse_args():
    """Realiza o parse dos argumentos informados em linha de comando na execução do arquivo"""

    parser = argparse.ArgumentParser(description='Arguments requiridos para o script.')

    parser.add_argument('--subject',
                        default=None,
                        type=str,
                        help='Assunto')

    parser.add_argument('--source-prefix',
                        default=None,
                        type=str,
                        help='Prefixo de origem')

    parser.add_argument('--target-prefix',
                        required=True,
                        type=str,
                        help='Prefixo de destino ')

    args = parser.parse_args()
    return args.subject, args.source_prefix, args.target_prefix


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    ts_ini = time.time()

    subject, source_prefix, target_prefix = parse_args()

    logging.info(f'{subject=}')
    logging.info(f'{source_prefix=}')
    logging.info(f'{target_prefix=}')

    try:
        processar_tabelas(subject, source_prefix, target_prefix)
        ts_fim = time.time()
        logging.info('Tempo total de processamento: %s', calcula_tempo_execucao(ts_ini, ts_fim))

    except Exception as e:
        ts_fim = time.time()
        logging.info('Tempo total de processamento: %s', calcula_tempo_execucao(ts_ini, ts_fim))
        logging.error(e)

        raise