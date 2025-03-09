#!/bin/bash

# Configurações
PROJECT_DIR="/home/ubuntu/busco-airflow"
DOMAIN="data-platform-airflow.busco.digital"
CERT_PATH="./nginx/certs/$DOMAIN/fullchain.pem"
RENEWAL_THRESHOLD=30  # Renovar se faltarem menos de 30 dias para expirar

# Verificar se o certificado existe
if [ -f "$CERT_PATH" ]; then
    # Verificar a data de expiração
    EXPIRY_DATE=$(openssl x509 -enddate -noout -in "$CERT_PATH" | cut -d= -f2)
    EXPIRY_TIMESTAMP=$(date -d "$EXPIRY_DATE" +%s)
    CURRENT_TIMESTAMP=$(date +%s)
    SECONDS_REMAINING=$((EXPIRY_TIMESTAMP - CURRENT_TIMESTAMP))
    DAYS_REMAINING=$((SECONDS_REMAINING / 86400))
    
    echo "O certificado para $DOMAIN expira em $DAYS_REMAINING dias."
    
    # Se o certificado estiver próximo da expiração ou já expirado
    if [ $DAYS_REMAINING -lt $RENEWAL_THRESHOLD ]; then
        echo "Iniciando serviço letsencrypt para renovação..."
        # Iniciar o letsencrypt
        docker compose -f docker-compose.letsencrypt.yml up -d
        
        echo "Aguardando renovação do certificado (2 minutos)..."
        sleep 120
        
        # Adicionar variáveis temporárias para o webserver
        docker compose -f docker-compose.yml exec webserver /bin/bash -c 'export LETSENCRYPT_HOST=data-platform-airflow.busco.digital && export LETSENCRYPT_EMAIL=ricardo.tanaka-partner@backlgrs.com.br'
        
        echo "Aguardando mais 3 minutos para concluir a renovação..."
        sleep 180
        
        # Parar o letsencrypt após a renovação
        docker compose -f docker-compose.letsencrypt.yml down
        
        echo "Renovação de certificado concluída e serviço letsencrypt parado."
    else
        echo "O certificado ainda é válido por $DAYS_REMAINING dias. Renovação não necessária."
    fi
else
    echo "Certificado não encontrado. Iniciando serviço letsencrypt para obtenção inicial..."
    # Verificar se o nginx-proxy está rodando
    if ! docker ps | grep -q "nginx-proxy"; then
        echo "O nginx-proxy precisa estar rodando primeiro. Iniciando..."
        docker compose -f docker-compose.yml up -d nginx-proxy
        echo "Aguardando nginx-proxy iniciar (30 segundos)..."
        sleep 30
    fi
    
    # Iniciar o letsencrypt
    docker compose -f docker-compose.letsencrypt.yml up -d
    
    # Adicionar variáveis para o webserver
    docker compose -f docker-compose.yml exec webserver /bin/bash -c 'export LETSENCRYPT_HOST=data-platform-airflow.busco.digital && export LETSENCRYPT_EMAIL=ricardo.tanaka-partner@backlgrs.com.br'
    
    echo "Aguardando obtenção do certificado (5 minutos)..."
    sleep 300
    
    # Parar o letsencrypt após a obtenção
    docker compose -f docker-compose.letsencrypt.yml down
    
    echo "Obtenção de certificado concluída e serviço letsencrypt parado."
fi