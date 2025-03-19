# Use a imagem oficial do Airflow como base
FROM apache/airflow:2.10.5-python3.9

USER root

# Instalar dependências do sistema
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        git \
        curl \
        vim \
        wget \
        netcat-traditional \
        unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Argumentos para permitir customização de UID/GID
ARG AIRFLOW_UID=50000

# Reconfigurar o usuário airflow para corresponder ao UID do host
RUN usermod -u ${AIRFLOW_UID} airflow

# Reconfigurar o usuário airflow para corresponder ao UID do host
RUN if [ ${AIRFLOW_UID} != 50000 ]; then \
    groupmod -g 0 airflow || true && \
    usermod -u ${AIRFLOW_UID} -g 0 airflow || true ; \
    fi

# Criar diretórios necessários
RUN mkdir -p /opt/airflow/dags \
    && mkdir -p /opt/airflow/logs \
    && mkdir -p /opt/airflow/plugins \
    && mkdir -p /opt/airflow/config \
    && mkdir -p /opt/airflow/scripts

# Para produção, copie os arquivos locais
COPY --chown=${AIRFLOW_UID}:0 dags/ /opt/airflow/dags/
COPY --chown=${AIRFLOW_UID}:0 plugins/ /opt/airflow/plugins/
COPY --chown=${AIRFLOW_UID}:0 config/ /opt/airflow/config/
COPY --chown=${AIRFLOW_UID}:0 scripts/ /opt/airflow/scripts/

# Copiar os arquivos de requisitos
COPY --chown=${AIRFLOW_UID}:0 requirements.txt /opt/airflow/requirements.txt

# Ajuste as permissões 
RUN chown -R ${AIRFLOW_UID}:0 /opt/airflow/dags \
    && chown -R ${AIRFLOW_UID}:0 /opt/airflow/logs \
    && chown -R ${AIRFLOW_UID}:0 /opt/airflow/plugins \
    && chown -R ${AIRFLOW_UID}:0 /opt/airflow/config \
    && chown -R ${AIRFLOW_UID}:0 /opt/airflow/scripts \
    && chmod -R 755 /opt/airflow/dags \
    && chmod -R 755 /opt/airflow/logs \
    && chmod -R 755 /opt/airflow/plugins \
    && chmod -R 755 /opt/airflow/config \
    && chmod -R 755 /opt/airflow/scripts

# Instalar o AWS CLI
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install \
    && rm -rf aws awscliv2.zip

# Verifique a instalação do Airflow
RUN which airflow || echo "Airflow não está no PATH"

# Copiar script de entrypoint
COPY --chown=${AIRFLOW_UID}:0 scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Mudar para o usuário airflow
USER airflow

#Instalar pacotes Python
RUN pip install --no-cache-dir -r /opt/airflow/requirements.txt

# Definir variáveis de ambiente
ENV PYTHONPATH=/opt/airflow
ENV AIRFLOW_HOME=/opt/airflow

ENTRYPOINT ["/entrypoint.sh"]