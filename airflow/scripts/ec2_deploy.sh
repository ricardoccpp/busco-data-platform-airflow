#!/bin/bash
set -e

# Configurações
EC2_USER="ubuntu"
EC2_HOST=""
PRIVATE_KEY=""
PROJECT_DIR="/home/ubuntu/busco-airflow"
DOCKER_COMPOSE_VERSION="2.23.0"

# Verificar parâmetros
if [ $# -lt 2 ]; then
    echo "Uso: $0 <ec2-host> <private-key-path>"
    exit 1
fi

EC2_HOST=$1
PRIVATE_KEY=$2

echo "=== Iniciando deploy do Airflow na instância EC2 ==="
echo "Host: $EC2_HOST"
echo "Usuário: $EC2_USER"
echo "Diretório de projeto: $PROJECT_DIR"

# Carregar variáveis de ambiente
if [ -f .env ]; then
  export $(grep -v '^#' .env.prod | xargs)
fi

# Verificar se ECR_REPOSITORY_URI está configurado
if [ -z "$ECR_REPOSITORY_URI" ]; then
  echo "Erro: ECR_REPOSITORY_URI não está definido no arquivo .env.prod"
  exit 1
fi

# Verificar se a chave privada existe
if [ ! -f "$PRIVATE_KEY" ]; then
    echo "Erro: Arquivo de chave privada não encontrado: $PRIVATE_KEY"
    exit 1
fi

# Verificar conectividade com a instância
echo "Verificando conectividade com a instância EC2..."
ssh -i "$PRIVATE_KEY" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_HOST" "echo Conectado com sucesso" || {
    echo "Erro: Não foi possível conectar à instância EC2"
    exit 1
}

# Verificar se o Docker está instalado na instância
echo "Verificando se o Docker está instalado..."
ssh -i "$PRIVATE_KEY" "$EC2_USER@$EC2_HOST" "which docker" > /dev/null || {
    echo "Docker não encontrado. Instalando Docker..."
    ssh -i "$PRIVATE_KEY" "$EC2_USER@$EC2_HOST" 'sudo apt-get update && \
sudo apt-get install ca-certificates curl && \
sudo install -m 0755 -d /etc/apt/keyrings && \
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc && \
sudo chmod a+r /etc/apt/keyrings/docker.asc && \
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null && \
sudo apt-get update && \
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin && \
sudo systemctl enable docker && \
sudo systemctl start docker && \
sudo usermod -a -G docker $USER'
    echo "Docker instalado com sucesso!"
}

# Verificar se o Docker Compose está instalado
echo "Verificando se o Docker Compose está instalado..."
ssh -i "$PRIVATE_KEY" "$EC2_USER@$EC2_HOST" "which docker-compose" > /dev/null || {
    echo "Docker Compose não encontrado. Instalando Docker Compose..."
    ssh -i "$PRIVATE_KEY" "$EC2_USER@$EC2_HOST" "sudo curl -L \"https://github.com/docker/compose/releases/download/$DOCKER_COMPOSE_VERSION/docker-compose-$(uname -s)-$(uname -m)\" -o /usr/local/bin/docker-compose && sudo chmod +x /usr/local/bin/docker-compose"
    echo "Docker Compose instalado com sucesso!"
}

# Verificar se o AWS CLI está instalado
echo "Verificando se o AWS CLI está instalado..."
ssh -i "$PRIVATE_KEY" "$EC2_USER@$EC2_HOST" "which aws" > /dev/null || {
    echo "AWS CLI não encontrado. Instalando AWS CLI..."
    ssh -i "$PRIVATE_KEY" "$EC2_USER@$EC2_HOST" "curl \"https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip\" -o \"awscliv2.zip\" && unzip awscliv2.zip && sudo ./aws/install && rm -rf aws awscliv2.zip"
    echo "AWS CLI instalado com sucesso!"
}

# Criar diretório do projeto na instância EC2
echo "Criando diretório do projeto na instância EC2..."
ssh -i "$PRIVATE_KEY" "$EC2_USER@$EC2_HOST" "mkdir -p $PROJECT_DIR"

# Copiar arquivos do projeto para a instância EC2
echo "Copiando arquivos do projeto para a instância EC2..."
rsync -avz --exclude 'logs' --exclude '.git' --exclude '__pycache__' --exclude '*.pyc' -e "ssh -i $PRIVATE_KEY" ./ "$EC2_USER@$EC2_HOST:$PROJECT_DIR/"

# Configurar permissões nos scripts
echo "Configurando permissões nos scripts..."
ssh -i "$PRIVATE_KEY" "$EC2_USER@$EC2_HOST" "chmod +x $PROJECT_DIR/scripts/*.sh $PROJECT_DIR/deployment/aws/*.sh"

# Configurar o arquivo .env na instância remota
echo "Configurando arquivo .env.prod para .env..."
scp -i "$PRIVATE_KEY" .env.prod "$EC2_USER@$EC2_HOST:$PROJECT_DIR/.env"

# Login no ECR
echo "Fazendo login no ECR..."
source .env.prod
ssh -i "$PRIVATE_KEY" "$EC2_USER@$EC2_HOST" "cd $PROJECT_DIR && export AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID && export AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY && export AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION && aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $(echo $ECR_REPOSITORY_URI | cut -d'/' -f1)"

# Configurar o arquivo de serviço systemd
echo "Configurando o arquivo de serviço systemd..."
ssh -i "$PRIVATE_KEY" "$EC2_USER@$EC2_HOST" "cd $PROJECT_DIR && ./scripts/setup_systemd.sh ./deployment/aws/systemd/airflow.service"

# Configurar o serviço systemd
echo "Instalando o serviço systemd para o Airflow..."
ssh -i "$PRIVATE_KEY" "$EC2_USER@$EC2_HOST" "sudo cp $PROJECT_DIR/deployment/aws/systemd/airflow.service /etc/systemd/system/ && sudo systemctl daemon-reload"

# Iniciar os serviços usando docker-compose.prod.yml
echo "Iniciando os serviços do Airflow..."
ssh -i "$PRIVATE_KEY" "$EC2_USER@$EC2_HOST" "cd $PROJECT_DIR && docker compose -f docker-compose.prod.yml pull && docker compose -f docker-compose.prod.yml up -d"

echo "=== Deploy concluído com sucesso! ==="
echo "O Airflow está acessível em: http://$EC2_HOST:8080"
echo "Usuário: $_AIRFLOW_WWW_USER_USERNAME (conforme definido no .env)"
echo ""
echo "Para iniciar/parar os serviços manualmente:"
echo "ssh -i $PRIVATE_KEY $EC2_USER@$EC2_HOST 'cd $PROJECT_DIR && docker compose -f docker-compose.prod.yml start|stop'"
echo ""
echo "Para iniciar automaticamente na inicialização do sistema:"
echo "ssh -i $PRIVATE_KEY $EC2_USER@$EC2_HOST 'sudo systemctl enable airflow && sudo systemctl start airflow'"
echo ""
echo "Para verificar os logs:"
echo "ssh -i $PRIVATE_KEY $EC2_USER@$EC2_HOST 'cd $PROJECT_DIR && docker compose -f docker-compose.prod.yml logs -f'"