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

# Tag para a imagem (prod por padrão, ou a especificada como argumento)
TAG=${1:-latest}

# Verifica se a tag é válida
if [ "$TAG" != "dev" ] && [ "$TAG" != "prod" ] && [ "$TAG" != "latest" ]; then
  echo "Erro: Tag inválida. Use 'dev' ou 'prod' ou 'latest'"
  echo "Uso: $0 [tag]"
  exit 1
fi

# Extrai o nome do repositório e a região do URI
ECR_REPOSITORY_NAME=$(echo $ECR_REPOSITORY_URI | cut -d'/' -f2)
AWS_REGION=$(echo $ECR_REPOSITORY_URI | cut -d'.' -f4)

echo "=== Enviando imagem $TAG para ECR ==="
echo "Repositório: $ECR_REPOSITORY_NAME"
echo "Região: $AWS_REGION"
echo "Tag: $TAG"

# Verifica se a imagem local existe
docker image inspect data-platform-prod-airflow:$TAG > /dev/null 2>&1 || {
  echo "Erro: Imagem local 'data-platform-prod-airflow:$TAG' não encontrada"
  echo "Execute primeiro o script de build: ./scripts/local_build.sh"
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
TIMESTAMP=$(date +%Y%m%d%H%M%S)
echo "Adicionando tags à imagem:"
echo "- $ECR_REPOSITORY_URI:$TAG"
echo "- $ECR_REPOSITORY_URI:$TAG-$TIMESTAMP"

docker tag data-platform-prod-airflow:$TAG $ECR_REPOSITORY_URI:$TAG
docker tag data-platform-prod-airflow:$TAG $ECR_REPOSITORY_URI:$TAG-$TIMESTAMP

# Envia imagem para o ECR
echo "Enviando imagem para ECR..."
docker push $ECR_REPOSITORY_URI:$TAG
docker push $ECR_REPOSITORY_URI:$TAG-$TIMESTAMP

echo "=== Imagem enviada com sucesso! ==="
echo "URI da imagem: $ECR_REPOSITORY_URI:$TAG"
echo ""
echo "Para fazer deploy na instância EC2, execute:"
echo "./scripts/ec2_deploy.sh <ec2-host> <path-to-key.pem>"