#!/bin/bash
set -e

# Carrega variáveis de ambiente
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Verifica se o URI do repositório ECR foi definido
if [ -z "$ECR_REPOSITORY_URI" ]; then
  echo "Erro: ECR_REPOSITORY_URI não está definido. Configure-o no arquivo .env"
  exit 1
fi

# Extrai o nome do repositório e a região do URI
ECR_REPOSITORY_NAME=$(echo $ECR_REPOSITORY_URI | cut -d'/' -f2)
AWS_REGION=$(echo $ECR_REPOSITORY_URI | cut -d'.' -f4)

echo "=== Enviando imagem local para ECR ==="
echo "Repositório: $ECR_REPOSITORY_NAME"
echo "Região: $AWS_REGION"

# Verifica se a imagem local existe
docker image inspect data-platform-prod-processor:latest > /dev/null 2>&1 || {
  echo "Erro: Imagem local 'data-platform-prod-processor:latest' não encontrada"
  echo "Execute primeiro o build: docker build -t data-platform-prod-processor ."
  exit 1
}

# Autentica no ECR
echo "Autenticando no ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $(echo $ECR_REPOSITORY_URI | cut -d'/' -f1)

# Verifica se o repositório existe, caso contrário, cria
aws ecr describe-repositories --repository-names $ECR_REPOSITORY_NAME --region $AWS_REGION > /dev/null 2>&1 || {
  echo "Repositório não existe. Criando repositório $ECR_REPOSITORY_NAME..."
  aws ecr create-repository --repository-name $ECR_REPOSITORY_NAME --region $AWS_REGION
}

# Adiciona tags à imagem
IMAGE_TAG=$(date +%Y%m%d%H%M%S)
echo "Adicionando tags à imagem:"
echo "- $ECR_REPOSITORY_URI:latest"
echo "- $ECR_REPOSITORY_URI:$IMAGE_TAG"

docker tag data-platform-prod-processor:latest $ECR_REPOSITORY_URI:latest
docker tag data-platform-prod-processor:latest $ECR_REPOSITORY_URI:$IMAGE_TAG

# Envia imagem para o ECR
echo "Enviando imagem para ECR..."
docker push $ECR_REPOSITORY_URI:latest
docker push $ECR_REPOSITORY_URI:$IMAGE_TAG

echo "=== Imagem enviada com sucesso! ==="
echo "URI da imagem: $ECR_REPOSITORY_URI:$IMAGE_TAG"
echo ""
echo "Esta imagem poderá ser invocada pelo Airflow usando a URI: $ECR_REPOSITORY_URI:latest"