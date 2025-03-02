#!/usr/bin/env python3
"""
Script para configurar conexões no Airflow.

Este script configura as conexões necessárias para o Airflow
interagir com vários serviços AWS e bancos de dados.

Exemplo de uso:
    python setup_connections.py

Variáveis de ambiente:
    AIRFLOW_HOME: Diretório base do Airflow (opcional)
    AWS_REGION: Região da AWS
    AWS_ACCESS_KEY_ID: Access Key da AWS
    AWS_SECRET_ACCESS_KEY: Secret Key da AWS
    POSTGRES_HOST: Host do PostgreSQL
    POSTGRES_PORT: Porta do PostgreSQL
    POSTGRES_USER: Usuário do PostgreSQL
    POSTGRES_PASSWORD: Senha do PostgreSQL
    POSTGRES_DB: Nome do banco de dados PostgreSQL
"""
import json
import os
import subprocess
from typing import Dict, List, Optional

# Verificar se estamos em um contêiner
IN_CONTAINER = os.path.exists('/.dockerenv')

# Carregar variáveis de ambiente
def get_env(name: str, default: Optional[str] = None) -> str:
    """Obtém variável de ambiente com valor padrão."""
    value = os.environ.get(name, default)
    if value is None:
        raise ValueError(f"Variável de ambiente {name} não definida")
    return value

# Configurar conexões
def setup_connections() -> None:
    """Configura as conexões do Airflow."""
    connections = [
        {
            'conn_id': 'aws_default',
            'conn_type': 'aws',
            'extra': {
                'region_name': get_env('AWS_REGION', 'us-east-1'),
                'aws_access_key_id': get_env('AWS_ACCESS_KEY_ID', ''),
                'aws_secret_access_key': get_env('AWS_SECRET_ACCESS_KEY', '')
            }
        },
        {
            'conn_id': 'postgres_default',
            'conn_type': 'postgres',
            'host': get_env('POSTGRES_HOST', 'localhost'),
            'port': int(get_env('POSTGRES_PORT', '5432')),
            'login': get_env('POSTGRES_USER', 'airflow'),
            'password': get_env('POSTGRES_PASSWORD', 'airflow'),
            'schema': get_env('POSTGRES_DB', 'airflow')
        },
        {
            'conn_id': 'ecs_default',
            'conn_type': 'aws',
            'extra': {
                'region_name': get_env('AWS_REGION', 'us-east-1'),
                'aws_access_key_id': get_env('AWS_ACCESS_KEY_ID', ''),
                'aws_secret_access_key': get_env('AWS_SECRET_ACCESS_KEY', ''),
                'service_name': 'ecs'
            }
        },
        {
            'conn_id': 's3_default',
            'conn_type': 'aws',
            'extra': {
                'region_name': get_env('AWS_REGION', 'us-east-1'),
                'aws_access_key_id': get_env('AWS_ACCESS_KEY_ID', ''),
                'aws_secret_access_key': get_env('AWS_SECRET_ACCESS_KEY', ''),
                'service_name': 's3'
            }
        }
    ]

    # Tentar obter conexões existentes
    for conn in connections:
        conn_id = conn['conn_id']
        
        # Construir o comando de conexão add
        cmd = ['airflow', 'connections', 'add']
        cmd.extend(['--conn-id', conn_id])
        cmd.extend(['--conn-type', conn['conn_type']])
        
        if 'host' in conn:
            cmd.extend(['--conn-host', str(conn['host'])])
        
        if 'port' in conn:
            cmd.extend(['--conn-port', str(conn['port'])])
        
        if 'login' in conn:
            cmd.extend(['--conn-login', str(conn['login'])])
        
        if 'password' in conn:
            cmd.extend(['--conn-password', str(conn['password'])])
        
        if 'schema' in conn:
            cmd.extend(['--conn-schema', str(conn['schema'])])
        
        if 'extra' in conn:
            extra_json = json.dumps(conn['extra'])
            cmd.extend(['--conn-extra', extra_json])
        
        # Verificar se a conexão já existe e removê-la
        try:
            subprocess.run(['airflow', 'connections', 'get', conn_id], 
                          check=False, capture_output=True)
            
            # Se a execução chegar aqui, a conexão existe, então vamos deletá-la
            print(f"Conexão {conn_id} já existe. Removendo...")
            subprocess.run(['airflow', 'connections', 'delete', conn_id], check=True)
        except subprocess.CalledProcessError:
            # A conexão não existe, o que é bom
            pass
        
        # Adicionar a conexão
        print(f"Adicionando conexão: {conn_id}")
        subprocess.run(cmd, check=True)
        print(f"Conexão {conn_id} configurada com sucesso!")

if __name__ == "__main__":
    print("Configurando conexões do Airflow...")
    setup_connections()
    print("Configuração de conexões concluída!")