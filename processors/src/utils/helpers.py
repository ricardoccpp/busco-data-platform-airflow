import boto3
import logging

logging.getLogger().setLevel(logging.INFO)

def calcula_tempo_execucao(inicio, fim):

    tempo_decorrido_segundos = fim - inicio
    minutos = int(tempo_decorrido_segundos // 60)
    segundos = tempo_decorrido_segundos % 60

    return minutos, segundos


def delete_s3_objects_in_prefix(
        bucket_name: str,
        prefixes: 'list[str]' = None,
        prefix: str = None
    ):

    s3_client = boto3.client('s3')
    paginator = s3_client.get_paginator('list_objects_v2')

    if prefix is not None:
        delete_us = {'Objects': []}
        for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
            if 'Contents' in page:
                for obj in page['Contents']:
                    delete_us['Objects'].append({'Key': obj['Key']})

                    # Delete em lotes de 1000
                    if len(delete_us['Objects']) == 1000:
                        s3_client.delete_objects(Bucket=bucket_name, Delete=delete_us)
                        print('if')
                        print(f'{bucket_name=}')
                        print(f'{delete_us=}')
                        delete_us = {'Objects': []}

        # Delete qualquer objeto restante
        if delete_us['Objects']:
            s3_client.delete_objects(Bucket=bucket_name, Delete=delete_us)
            print(f'{bucket_name=}')
            print(f'{delete_us=}')

        logging.info(f'Deleted all objects in prefix {prefix} from {bucket_name}')

    elif prefixes is not None:
        for prefix in prefixes:
            delete_us = {'Objects': []}
            for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
                if 'Contents' in page:
                    for obj in page['Contents']:
                        delete_us['Objects'].append({'Key': obj['Key']})

                        # Delete em lotes de 1000
                        if len(delete_us['Objects']) == 1000:
                            s3_client.delete_objects(Bucket=bucket_name, Delete=delete_us)
                            logging.info('if')
                            logging.info(f'{bucket_name=}')
                            logging.info(f'{delete_us=}')
                            delete_us = {'Objects': []}

            # Delete qualquer objeto restante
            if delete_us['Objects']:
                s3_client.delete_objects(Bucket=bucket_name, Delete=delete_us)
                logging.info(f'{bucket_name=}')
                logging.info(f'{delete_us=}')

            logging.info(f'Deleted all objects in prefix {prefix} from {bucket_name}')



def add_glue_partition_batch(
        database_name: str,
        table_name: str,
        partition_values: 'list[str]',
        s3_locations: 'list[str]'
    ):

    glue_client = boto3.client('glue')

    try:
        response = glue_client.get_table(
            DatabaseName=database_name,
            Name=table_name
        )
    except Exception as error:
        logging.error('Exception while fetching table info')
        logging.error(error)
        raise error

    # Parsing table info required to create partitions from table
    table_data = {}
    table_data['input_format'] = response['Table']['StorageDescriptor']['InputFormat']
    table_data['output_format'] = response['Table']['StorageDescriptor']['OutputFormat']
    table_data['serde_info'] = response['Table']['StorageDescriptor']['SerdeInfo']

    # Define a estrutura da partição
    partition_input = [{
        'Values': values,
        'StorageDescriptor': {
            'Location': location,
            'InputFormat': table_data['input_format'],
            'OutputFormat': table_data['output_format'],
            'SerdeInfo': table_data['serde_info']
        }
    } for values, location,  in zip(partition_values, s3_locations) ]

    # Adiciona a partição
    try:
        response = glue_client.batch_create_partition(
            DatabaseName=database_name,
            TableName=table_name,
            PartitionInputList=partition_input
        )

        # Verificar se há erros na resposta
        errors = response.get('Errors', [])
        for error in errors:
            error_type = error.get('ErrorDetail', {}).get('ErrorCode', '')
            error_partition_values = error.get('PartitionValues', [])

            # Ignorar erros de partição já existente
            if error_type == 'AlreadyExistsException':
                logging.info(f'Ignorando erro de partição já existente: {error_partition_values}')
            else:
                logging.info(f"Erro ao adicionar partição {error_partition_values}: {error.get('ErrorDetail', {}).get('ErrorMessage', '')}")
                raise

    except Exception as e:
        logging.info(f'Erro ao chamar a API do Glue: {e}')
