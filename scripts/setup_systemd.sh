#!/bin/bash
# Script para configurar o serviço systemd com a URI do ECR

set -e

# Verificar se foi fornecido um caminho para o arquivo de serviço
if [ "$#" -ne 1 ]; then
    echo "Uso: $0 <caminho-do-arquivo-service>"
    exit 1
fi

SERVICE_FILE="$1"

# Verificar se o arquivo existe
if [ ! -f "$SERVICE_FILE" ]; then
    echo "Erro: Arquivo $SERVICE_FILE não encontrado"
    exit 1
fi

# Carregar variáveis de ambiente
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Verificar se a variável ECR_REPOSITORY_URI está definida
if [ -z "$ECR_REPOSITORY_URI" ]; then
    echo "Erro: ECR_REPOSITORY_URI não está definida no arquivo .env"
    exit 1
fi

# Substituir o placeholder no arquivo de serviço
sed -i "s|{{ ECR_REPOSITORY_URI }}|$ECR_REPOSITORY_URI|g" "$SERVICE_FILE"

echo "Arquivo $SERVICE_FILE configurado com ECR_REPOSITORY_URI=$ECR_REPOSITORY_URI"