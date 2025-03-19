#!/bin/bash
set -e

# Exporte do PATH para garantir que o airflow seja encontrado
export PATH="/home/airflow/.local/bin:$PATH"

# Carregar variáveis de ambiente do arquivo .env se existir
if [ -f /opt/airflow/.env ]; then
  echo "Carregando variáveis de ambiente de /opt/airflow/.env"
  export $(grep -v '^#' /opt/airflow/.env | grep -v '^\s*$' | xargs)
fi

if ! whoami &> /dev/null; then
  if [ -w /etc/passwd ]; then
    echo "${USER_NAME:-airflow}:x:$(id -u):$(id -g):${USER_NAME:-airflow} user:${HOME}:/sbin/nologin" >> /etc/passwd
  fi
fi

# Função para aguardar a disponibilidade do PostgreSQL
wait_for_postgres() {
  echo "Verificando conexão com PostgreSQL..."
  while ! nc -z "$POSTGRES_HOST" "$POSTGRES_PORT"; do
    echo "PostgreSQL não está disponível ainda - aguardando..."
    sleep 2
  done
  echo "PostgreSQL está disponível!"
}

# Função para aguardar Redis
wait_for_redis() {
  echo "Verificando conexão com Redis..."
  while ! nc -z "redis" 6379; do
    echo "Redis não está disponível ainda - aguardando..."
    sleep 2
  done
  echo "Redis está disponível!"
}

# Verificar quais dependências são necessárias com base no comando
case "$1" in
  webserver)
    # O webserver precisa do PostgreSQL
    wait_for_postgres
    ;;
  scheduler)
    # O scheduler precisa do PostgreSQL
    wait_for_postgres
    ;;
  worker)
    # O worker precisa do PostgreSQL e Redis
    wait_for_postgres
    wait_for_redis
    ;;
  flower)
    # Flower precisa do Redis
    wait_for_redis
    ;;
  version)
    # Comando version não precisa verificar dependências
    # exec airflow "$@"
    exit 0
    ;;
esac

# Executar o comando fornecido ao contêiner
exec airflow "$@"