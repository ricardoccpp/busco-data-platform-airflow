#!/bin/bash
set -e

# Identificar o diretório atual e o diretório do script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AIRFLOW_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Mudar para o diretório do Airflow
cd "$AIRFLOW_DIR"
echo "Trabalhando no diretório: $(pwd)"

echo "=== Iniciando build local da imagem Airflow ==="

# Verificar se estamos no diretório correto que contém o Dockerfile
if [ ! -f "Dockerfile" ]; then
  echo "Erro: Dockerfile não encontrado no diretório atual."
  echo "Diretório atual: $(pwd)"
  echo "Verifique se a estrutura do projeto está correta."
  exit 1
fi

# Verificar docker-compose.yml
if [ ! -f "docker-compose.yml" ]; then
  echo "Erro: docker-compose.yml não encontrado no diretório atual."
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

# Preparar diretórios
echo "Preparando diretórios..."
mkdir -p dags plugins logs config

# Verificar se requirements.txt existe
if [ ! -f "requirements.txt" ]; then
  echo "Aviso: requirements.txt não encontrado. Criando arquivo padrão com dependências essenciais."
  cat > requirements.txt << 'EOL'
# AWS
apache-airflow-providers-amazon>=2.0.0
boto3>=1.24.0
s3fs>=2022.5.0

# Database
apache-airflow-providers-postgres>=2.0.0
psycopg2-binary>=2.9.0
sqlalchemy>=1.4.0

# Redis/Celery
apache-airflow-providers-redis>=2.0.0
redis>=4.2.0

# Operadores adicionais
apache-airflow-providers-http>=2.1.0
apache-airflow-providers-slack>=4.2.0
EOL
  echo "Arquivo requirements.txt criado."
fi

# Verificar se entrypoint.sh existe
if [ ! -f "scripts/entrypoint.sh" ]; then
  echo "Erro: scripts/entrypoint.sh não encontrado."
  echo "Verifique se a estrutura do projeto está correta."
  exit 1
fi

# Verificar permissões dos scripts
echo "Configurando permissões nos scripts..."
chmod +x scripts/*.sh 2>/dev/null || echo "Aviso: Não foi possível alterar permissões de scripts/*.sh"
[ -d "deployment/aws" ] && chmod +x deployment/aws/*.sh 2>/dev/null || echo "Aviso: Não foi possível alterar permissões de deployment/aws/*.sh"

# Construir a imagem Docker
echo "Construindo a imagem Docker..."
docker build -t data-platform-prod-airflow:latest -f Dockerfile .

# Verificar se a build foi bem-sucedida
if [ $? -eq 0 ]; then
  echo "=== Build concluído com sucesso! ==="
  echo "Imagem local: data-platform-prod-airflow:latest"
  
  # Verificar se ECR_REPOSITORY_URI existe para sugerir o próximo passo
  if [ -n "$ECR_REPOSITORY_URI" ]; then
    echo ""
    echo "Para enviar a imagem para o ECR, execute:"
    echo "./scripts/ecr_push.sh"
  fi
  
  echo ""
  echo "Para testar a imagem de produção localmente, execute:"
  echo "docker-compose -f docker-compose.prod.yml up -d"
  echo ""
  echo "Para verificar os logs:"
  echo "docker-compose -f docker-compose.prod.yml logs -f"
else
  echo "=== Erro durante o build da imagem! ==="
  exit 1
fi