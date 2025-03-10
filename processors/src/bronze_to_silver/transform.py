"""Realiza o ETL"""
import logging
import time
from pathlib import Path
from utils.helpers_duckdb import create_table_from_s3
from utils.helpers_duckdb import create_table_local
from utils.helpers_duckdb import write_parquet_to_s3
from utils.helpers_duckdb import get_table_count_rows
from utils.helpers import calcula_tempo_execucao
from duckdb import DuckDBPyConnection

logging.getLogger().setLevel(logging.INFO)
QUERY_FOLDER = Path(__file__).parent / 'sql'

def criar_stg_mock_data(
        conn_duck_db: DuckDBPyConnection,
        s3_read_path: str
    ) -> None:
    """Prepara a stage principal através de uma query no S3

    Arguments:
    conn_duck_db -- Instância de conexão do DuckDB
    s3_read_path -- Caminho no S3 onde estão os dados de origem
    """
    logging.info(f'Criando tabela stg_mock_data')

    query_file = QUERY_FOLDER / 'stg_mock_data.sql'
    # Leitura da query com passagem de parametros
    query_stg_mock_data = open(query_file, 'rb').read().decode('UTF-8').format(s3_read_path=s3_read_path)
    create_table_from_s3(conn_duck_db, 'stg_mock_data', query=query_stg_mock_data)


def criar_silver_mock_data(
        conn_duck_db: DuckDBPyConnection
    ) -> None:
    """Prepara a tabela final

    Arguments:
    conn_duck_db -- Instância de conexão do DuckDB
    """
    logging.info(f'Formando silver_mock_data')

    query_file = QUERY_FOLDER / 'silver_mock_data.sql'
    query_silver_mock_data = open(query_file, 'rb').read().decode('UTF-8')
    create_table_local(conn_duck_db, 'silver_mock_data', query=query_silver_mock_data)

    logging.info('Linhas na tabela silver_mock_data: %s', get_table_count_rows(conn_duck_db, 'silver_mock_data'))


def processar_mock_data(
        conn_duck_db: DuckDBPyConnection,
        s3_read_path: str,
        s3_write_path: str,
    ) -> None:
    """processar_mock_data Função responsável por processar a os dados de teste
    Esta função é somente para fins didáticos e geração de conteúdo enquanto não há casos de uso e dados reais para processamento

    Arguments:
        conn_duck_db -- Conexão para o duckdb
        s3_read_path -- Caminho no S3 para leitura dos dados
        s3_write_path -- Caminho no S3 para escrita dos dados
    """
    logging.info(f'Iniciando processar_mock_data')
    ts_ini = time.time()

    try:
        ts_ini = time.time()
        criar_stg_mock_data(conn_duck_db, s3_read_path)
        criar_silver_mock_data(conn_duck_db)

        write_parquet_to_s3(conn_duck_db,
                            'silver_mock_data',
                            s3_write_path,
                            partitions=None)
        ts_fim = time.time()
        logging.info('Tempo total de processamento: %s', calcula_tempo_execucao(ts_ini, ts_fim))

    except Exception as e:
        conn_duck_db.close()
        ts_fim = time.time()
        logging.info('Tempo total de processamento: %s', calcula_tempo_execucao(ts_ini, ts_fim))
        logging.error(e)
