"""Funções úteis para uso com o duckdb"""
import time
import logging
from json import loads
from utils.helpers import calcula_tempo_execucao
from utils.helpers import delete_s3_objects_in_prefix
from duckdb import DuckDBPyConnection
import duckdb

logging.getLogger().setLevel(logging.INFO)

def create_s3_secret(
        conn_duck_db: DuckDBPyConnection,
        access_key: str = None,
        secret_key: str = None,
        region: str = 'us-east-1'
    ) -> None:
    """Registra as credenciais AWS para acessar os dados no S3

    Arguments:
    conn_duck_db -- Instância de conexão do DuckDB

    Keyword Arguments:
    access_key -- ACCESS KEY utilizada para conexão, se não informado tentará
    utilizar a access_key, secret_key e region armazenado no secrets manager
    secret_key -- SECRET KEY utilizado para conexão
    region -- Região da AWS, se não informado utilizará us-west-2
    """
    t_ini = time.time()
    secret = ''

    if access_key is None:
        logging.info('Trying to get credentials from secrets manager')
        access_key = get_parameters('system_inteligencia_access_key')
        secret_key = get_parameters('system_inteligencia_secret_key')
        secret = f'''
            CREATE SECRET secret1 (
                TYPE S3,
                KEY_ID '{access_key}',
                SECRET '{secret_key}',
                REGION '{region}'
            );
        '''
    else:
        if secret_key is not None:
            secret = f'''
                CREATE SECRET secret1 (
                    TYPE S3,
                    KEY_ID '{access_key}',
                    SECRET '{secret_key}',
                    REGION '{region}'
                );
            '''
        else:
            logging.error('Secret key is missing for the given access key')

    try:
        logging.info('Storing S3 secret at local duckdb')
        conn_duck_db.execute(secret)
        t_fim = time.time()
        logging.info('S3 secret stored in: %s', calcula_tempo_execucao(t_ini, t_fim))
    except Exception as e:
        conn_duck_db.close()
        t_fim = time.time()
        logging.info('Execution time: %s', calcula_tempo_execucao(t_ini, t_fim))
        logging.error('Error trying to store S3 secret at local duckdb')
        logging.error(e)

        raise

def create_table_local(
        conn_duck_db: DuckDBPyConnection,
        table_name: str,
        query: str,
        drop_if_exists: bool = True
    ) -> None:
    """Cria tabela na instância do DuckDB informada a partir de uma query

    Arguments:
    conn_duck_db -- Instância de conexão do DuckDB
    table_name -- Nome da tabela a ser criada
    query -- Query utilizada para criar a tabela

    Keyword Arguments:
    drop_if_exists -- Se True, dropa a tabela no DuckDB antes de criá-la
    """
    t_ini = time.time()
    logging.info('Creating local table %s by query statement', table_name)

    query = f'create table {table_name} as {query}'

    if drop_if_exists:
        try:
            conn_duck_db.execute(f'drop table if exists {table_name};')
        except Exception as e:
            conn_duck_db.close()
            t_fim = time.time()
            logging.info('Execution time: %s', calcula_tempo_execucao(t_ini, t_fim))
            logging.error('Error trying to run: drop table if exists %s ;', table_name)
            logging.error(e)

            raise

    try:
        logging.info('Running query %s', query)
        conn_duck_db.execute(query)
        t_fim = time.time()
        logging.info('Local table %s created in: %s',
                     table_name,
                     calcula_tempo_execucao(t_ini, t_fim))
    except Exception as e:
        conn_duck_db.close()
        t_fim = time.time()
        logging.info('Execution time: %s', calcula_tempo_execucao(t_ini, t_fim))
        logging.error('Error trying to run: %s', query)
        logging.error(e)

        raise

def delete_s3_partitions(
        conn_duck_db: DuckDBPyConnection,
        table_name: str,
        s3_path: str,
        partitions: 'list[str]' = None
    ) -> None:
    """Deleta arquivos no S3 de acordo com as partições que serão gravadas

    Arguments:
    conn_duck_db -- Instância de conexão do DuckDB
    table_name -- Nome da tabela que contém as partições a serem gravadas no S3
    s3_path -- Bucket + Prefixo do S3 onde a tabela está armazenada e será gravada no S3

    Keyword Arguments:
    partitions -- Lista de colunas utilizadas como partições
    """
    t_ini = time.time()
    logging.info('Deleting S3 objects')

    s3_bucket = s3_path.replace('s3://', '')[:(s3_path.replace('s3://', '')).find('/')]
    s3_prefix = s3_path.replace('s3://', '')[(s3_path.replace('s3://', '')).find('/') + 1:]

    if partitions is not None:
        query = f'select distinct {", ".join(partitions)} from {table_name}'

        df = conn_duck_db.execute(query).fetch_df()

        for c in df.columns:
            if 'datetime' in df[c].dtypes.name:
                df[c] = df[c].dt.strftime('%Y-%m-%d')

        json_partition_values = loads(df.to_json(orient='records'))

        s3_prefixes = []
        for j in json_partition_values:
            l_chave_valor = []
            for k, v in zip(j.keys(), j.values()):
                l_chave_valor.append(f'{k}={v}')
            s3_prefixes.append(f'{s3_prefix}/{"/".join(l_chave_valor)}/')

        delete_s3_objects_in_prefix(s3_bucket, s3_prefixes)
    else:
        delete_s3_objects_in_prefix(s3_bucket, prefixes=None, prefix=f'{s3_prefix}/')

    t_fim = time.time()
    logging.info('S3 objects deleted in: %s', calcula_tempo_execucao(t_ini, t_fim))

def write_parquet_to_s3(
        conn_duck_db: DuckDBPyConnection,
        table_name: str,
        s3_path: str,
        partitions: 'list[str]' = None
    ) -> None:
    """Exporta tabela da instância do DuckDB informada em arquivos parquet no S3

    Arguments:
    conn_duck_db -- Instância de conexão do DuckDB
    table_name -- Nome da tabela a ser exportada
    s3_path -- URL do S3 onde os arquivos serão gravados

    Keyword Arguments:
    partitions -- Lista de colunas utilizadas para particionar a tabela
    """
    t_ini = time.time()
    logging.info('Writing table %s at S3', table_name)

    # TODO por enquanto o overwrite nao esta funcionando para particoes em file system cloud
    # ficar de olho nos updates do duckdb
    if partitions is not None:
        query = f'''
            COPY {table_name} TO '{s3_path}' (
                FORMAT PARQUET,
                OVERWRITE_OR_IGNORE true,
                PARTITION_BY ({", ".join(partitions)})
            );
        '''
    else:
        query = f'''
            COPY {table_name} TO '{s3_path}' (
                FORMAT PARQUET,
                OVERWRITE_OR_IGNORE true,
                PER_THREAD_OUTPUT
            );
        '''

    delete_s3_partitions(conn_duck_db, table_name, s3_path, partitions)

    try:
        logging.info('Running query: %s', query)
        conn_duck_db.execute(query)
        t_fim = time.time()
        logging.info('Parquet files wrote at S3 in: %s', calcula_tempo_execucao(t_ini, t_fim))
    except Exception as e:
        conn_duck_db.close()
        t_fim = time.time()
        logging.info('Execution time: %s', calcula_tempo_execucao(t_ini, t_fim))
        logging.error('Error trying to run: %s', query)
        logging.error(e)

        raise

def get_table_count_rows(
        conn_duck_db: DuckDBPyConnection,
        table_name: str
    ) -> int:
    """Retornar a quantidade de linhas de uma tabela

    Arguments:
    conn_duck_db -- Instância de conexão do DuckDB
    table_name -- Nome da tabela a ser consultada
    """
    t_ini = time.time()
    logging.info('Counting rows from local table %s', table_name)

    query = f'select count(*) as num_rows from {table_name}'

    try:
        logging.info('Running query %s', query)
        num_rows = conn_duck_db.execute(query).fetchone()[0]
        t_fim = time.time()
        logging.info('Count rows from %s executed in: %s',
                     table_name,
                     calcula_tempo_execucao(t_ini, t_fim))
        return num_rows
    except Exception as e:
        conn_duck_db.close()
        t_fim = time.time()
        logging.info('Execution time: %s', calcula_tempo_execucao(t_ini, t_fim))
        logging.error('Error trying to run: %s', query)
        logging.error(e)

        raise

def print_table_contents(conn_duck_db, table_name: str) -> None:
    try:
        result = conn_duck_db.execute(f"SELECT * FROM {table_name}").fetchall()
        logging.info(f"Contents of table {table_name}:")
        for row in result:
            print(row)
    except Exception as e:
        logging.error(f'Error printing table {table_name}: {e}')
        raise

def create_table_from_s3(
        conn_duck_db: duckdb.DuckDBPyConnection,
        table_name: str,
        s3_path: str = None,
        hive_partition: bool = True,
        query: str = None,
        drop_if_exists: bool = True
    ) -> None:
    """Cria tabela na instância do DuckDB informada a partir de uma query ou tabela no S3

    Arguments:
    conn_duck_db -- Instância de conexão do DuckDB
    table_name -- Nome da tabela a ser criada

    Keyword Arguments:
    hive_partition -- Indica se a tabela está particionada com estilo hive (hive-style partition)
    query -- Query utilizada para criar a tabela
    drop_if_exists -- Se True, dropa a tabela no DuckDB antes de criá-la
    """
    t_ini = time.time()
    logging.info('Creating local table %s by reading S3 parquet files', table_name)
    if query is None:
        query = f'''
                    select *
                    from read_parquet("{s3_path}/*.parquet", hive_partitioning = {str(hive_partition).lower()})
                    ;
                '''
    query = f'create table {table_name} as {query}'

    if drop_if_exists:
        try:
            # Verificar se a conexão está aberta tentando executar um comando simples
            conn_duck_db.execute('select 1;')
            conn_duck_db.execute(f'drop table if exists {table_name};')
        except duckdb.ConnectionException as e:
            logging.error('Connection error: %s', e)
            raise
        except Exception as e:
            t_fim = time.time()
            logging.info('Execution time: %s', calcula_tempo_execucao(t_ini, t_fim))
            logging.error('Error trying to run: drop table if exists %s ;', table_name)
            logging.error(e)
            raise

    try:
        logging.info('Running query %s', query)
        # Verificar se a conexão está aberta tentando executar um comando simples
        conn_duck_db.execute('select 1;')
        conn_duck_db.execute(query)
        t_fim = time.time()
        logging.info('Local table %s created in: %s',
                     table_name,
                     calcula_tempo_execucao(t_ini, t_fim))
    except duckdb.ConnectionException as e:
        logging.error('Connection error: %s', e)
        raise
    except Exception as e:
        t_fim = time.time()
        logging.info('Execution time: %s', calcula_tempo_execucao(t_ini, t_fim))
        logging.error('Error trying to run: %s', query)
        logging.error(e)
        raise