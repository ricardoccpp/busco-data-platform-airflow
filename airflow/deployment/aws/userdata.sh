#!/bin/bash
# Script de inicialização para instância EC2
# Pode ser usado como User Data ao criar uma nova instância EC2

# Atualizar o sistema
yum update -y

# Instalar ferramentas básicas
yum install -y git jq vim htop

# Instalar o Docker
amazon-linux-extras install docker -y
systemctl enable docker
systemctl start docker
usermod -a -G docker ec2-user

# Instalar Docker Compose
DOCKER_COMPOSE_VERSION="2.23.0"
curl -L "https://github.com/docker/compose/releases/download/$DOCKER_COMPOSE_VERSION/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Instalar AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
./aws/install
rm -rf aws awscliv2.zip

# Criar diretório para o projeto Airflow
mkdir -p /home/ec2-user/busco-airflow
chown -R ec2-user:ec2-user /home/ec2-user/busco-airflow

# Criar diretórios para logs e dados persistentes
mkdir -p /mnt/data/airflow/logs
mkdir -p /mnt/data/airflow/dags
mkdir -p /mnt/data/airflow/plugins
chown -R ec2-user:ec2-user /mnt/data/airflow

# Configurar limites de arquivo e usuário para o Airflow
cat > /etc/security/limits.d/airflow.conf << 'EOL'
ec2-user soft nofile 65536
ec2-user hard nofile 65536
root soft nofile 65536
root hard nofile 65536
EOL

# Configurar parâmetros de memória para o sistema
cat >> /etc/sysctl.conf << 'EOL'
vm.max_map_count=262144
EOL
sysctl -p

# Clone do repositório (opcional, se você tiver um repositório Git)
# git clone https://github.com/seuusuario/busco-data-platform-pipeline.git /home/ec2-user/busco-airflow
# chown -R ec2-user:ec2-user /home/ec2-user/busco-airflow

# Mensagem de conclusão
echo "Configuração inicial concluída. Faça login na instância e execute o deploy do Airflow."