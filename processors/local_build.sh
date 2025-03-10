#!/bin/bash
set -e

# Identificar o diretório atual e o diretório do script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROCESSORS_DIR="$(cd "${SCRIPT_DIR}/" && pwd)"

# Mudar para o diretório do Processors
cd "$PROCESSORS_DIR"
echo "Trabalhando no diretório: $(pwd)"

echo "=== Iniciando build local da imagem Processors ==="

# Verificar se estamos no diretório correto que contém o Dockerfile
if [ ! -f "Dockerfile" ]; then
  echo "Erro: Dockerfile não encontrado no diretório atual."
  echo "Diretório atual: $(pwd)"
  echo "Verifique se a estrutura do projeto está correta."
  exit 1
fi

# Carregar variáveis de ambiente se .env existir
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
  echo "Variáveis de ambiente carregadas do arquivo .env"
else
  echo "Arquivo .env não encontrado. Usando valores padrão."
fi

# Verificar se requirements.txt existe
if [ ! -f "requirements.txt" ]; then
  echo "Aviso: requirements.txt não encontrado. Criando arquivo padrão com dependências essenciais."
  cat > requirements.txt << 'EOL'
# AWS
boto3>=1.24.0
s3fs>=2022.5.0

# DuckDB
duckdb==1.1.3

EOL
  echo "Arquivo requirements.txt criado."
fi

# Construir a imagem Docker
echo "Construindo a imagem Docker..."
docker build -t data-platform-prod-processors:latest -f Dockerfile .

# Verificar se a build foi bem-sucedida
if [ $? -eq 0 ]; then
  echo "=== Build concluído com sucesso! ==="
  echo "Imagem local: data-platform-prod-processors:latest"
  
  # Verificar se ECR_REPOSITORY_URI existe para sugerir o próximo passo
  if [ -n "$ECR_REPOSITORY_URI" ]; then
    echo ""
    echo "Para enviar a imagem para o ECR, execute:"
    echo "./deployment/ecr_push.sh"
  fi

else
  echo "=== Erro durante o build da imagem! ==="
  exit 1
fi