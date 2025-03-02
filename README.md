# Busco Data Platform Pipeline

Plataforma de processamento de dados completa, incluindo orquestração de pipelines com Apache Airflow (2.10.5) e processadores de dados usando DuckDB para transformações no datalake da Busco.

## Arquitetura

O projeto implementa uma arquitetura moderna de datalake com três camadas:

* **Bronze**: Dados brutos ingeridos dos sistemas de origem
* **Silver**: Dados limpos, normalizados e validados
* **Gold**: Dados agregados e modelados para consumo

```
┌─────────────────┐                ┌───────────────────┐
│    Airflow      │                │  ECS Processors   │
│   (Orquestrador)│◄──Invoca────►  │     (DuckDB)      │
└────────┬────────┘                └─────────┬─────────┘
         │                                    │
         │                                    ▼
         │                         ┌──────────────────┐
         │                         │     DuckDB       │
         │                         │  (Processamento) │
         │                         └─────────┬────────┘
         │                                   │
         ▼                                   ▼
┌────────────────────────────────────────────────────┐
│                     Data Lake                       │
├────────────────┬────────────────┬─────────────────┐
│    Bronze      │     Silver     │      Gold       │
│  (Raw Data)    │  (Cleansed)    │  (Consumption)  │
└────────────────┴────────────────┴─────────────────┘
         │                                   │
         ▼                                   ▼
┌────────────────┐               ┌────────────────────┐
│  Glue/Athena   │               │  BI/Analytics      │
│  (Discovery)   │               │  (Visualização)    │
└────────────────┘               └────────────────────┘
```

## Componentes do Sistema

### 1. Airflow

* **Função**: Orquestrador de pipelines de dados
* **Versão**: Apache Airflow 2.10.5 com Python 3.9
* **Infraestrutura**: 
  * **Desenvolvimento**: Contêineres Docker com PostgreSQL 16.3-alpine local
  * **Produção**: Contêineres Docker em EC2 com RDS PostgreSQL
* **Configurações**:
  * **Desenvolvimento** (`Dockerfile` + `docker-compose.yml`): Monta volumes locais
  * **Produção** (`Dockerfile.prod` + `docker-compose.prod.yml`): Copia arquivos na imagem

### 2. Processadores DuckDB

* **Função**: Processamento eficiente de dados nas camadas do datalake
* **Infraestrutura**: Contêineres ECS executados sob demanda (invocados pelo Airflow)
* **Organização**:
  * Processadores separados por camada (bronze_to_silver, silver_to_gold)
  * Componentes modulares para transformações específicas
  * Adaptadores para diferentes fontes de dados

## Estrutura do Projeto

```
busco-data-platform-pipeline/
├── airflow/                     # Projeto Airflow containerizado
│   ├── Dockerfile               # Imagem de dev baseada em apache/airflow:2.10.5-python3.9
│   ├── Dockerfile.prod          # Imagem de prod com arquivos copiados
│   ├── docker-compose.yml       # Configuração para dev com PostgreSQL local
│   ├── docker-compose.prod.yml  # Configuração para produção com RDS
│   ├── dags/                    # DAGs para orquestração dos pipelines
│   └── scripts/                 # Scripts de utilitários e deploy
│       ├── local_build.sh           # Script para construir imagem de desenvolvimento 
│       └── local_build_prod.sh      # Script para construir imagem de produção
│
└── processors/                  # Processadores para o datalake no ECS
    ├── Dockerfile               # Imagem Docker para processamento com DuckDB
    ├── src/
    │   ├── common/              # Componentes compartilhados
    │   ├── bronze_to_silver/    # Processadores para camada Silver
    │   ├── silver_to_gold/      # Processadores para camada Gold
    │   └── ...                  # Componentes de utilitários e modelos
    └── deployment/              # Scripts para deployment
        └── ecr_push.sh          # Script para enviar imagem para ECR
```

## Estrutura do Data Lake

```
s3://busco-data-lake/
  ├── bronze/
  │   ├── gsheets/
  │   ├── integracao/
  │   ├── postgres/
  │   │   ├── database1/
  │   │   │   ├── schema1/
  │   │   │   └── schema2/
  │   │   └── database2/
  │   └── redshift/
  ├── silver/
  │   ├── gsheets/
  │   ├── integracao/
  │   ├── postgres/
  │   └── redshift/
  └── gold/
      ├── analytics/
      ├── dashboards/
      └── reports/
```

## Pré-requisitos

* Docker e Docker Compose
* AWS CLI configurado
* Python 3.9+
* Acesso para recursos AWS (EC2, ECR, ECS, S3, Glue)
* Task definitions para ECS já criadas via Terraform

## Guias de Início Rápido

### Configuração Inicial do .env

Para iniciar, crie um arquivo `.env` com as variáveis necessárias:

```bash
# Na pasta airflow
cp .env.example .env
# Edite o arquivo .env conforme necessário
```

### Desenvolvimento com Airflow Local

```bash
# Navegar para a pasta do Airflow
cd airflow

# Build da imagem de desenvolvimento
./scripts/local_build.sh

# Iniciar o Airflow com volumes locais mapeados
docker-compose up -d

# Acessar a interface web
# http://localhost:8080 (usuário/senha: admin/admin)
```

### Build da Imagem de Produção

```bash
# Na pasta airflow
./scripts/local_build_prod.sh

# Testar localmente (opcional)
docker-compose -f docker-compose.prod.yml up -d
```

### Deploy para Produção

```bash
# Enviar imagem para ECR
cd airflow
./deployment/aws/ecr_push.sh prod  # Usar 'dev' para imagem de desenvolvimento

# Deploy na instância EC2
./scripts/ec2_deploy.sh <ec2-host> <key-path>
```

### Processadores DuckDB

```bash
# Build e envio da imagem para ECR
cd processors
docker build -t busco-datalake-processor .
./deployment/ecr_push.sh

# Os processadores serão executados pelo Airflow como tarefas ECS
```

## Estrutura de Desenvolvimento

### Diretórios Principais

* **dags/**: Adicione seus DAGs de Airflow aqui
* **plugins/**: Extensões para o Airflow
* **config/**: Arquivos de configuração
* **processors/src/**: Código fonte dos processadores de dados

### Fluxo de Trabalho

1. Desenvolva DAGs e plugins localmente com mapeamento de volumes
2. Teste localmente usando a imagem de desenvolvimento
3. Construa a imagem de produção para deploy
4. Envie para o repositório ECR
5. Implante na instância EC2

## Observações sobre Permissões

Quando trabalhar com volumes mapeados no Docker, use o ID do seu usuário local para evitar problemas de permissão:

```
# No arquivo .env
AIRFLOW_UID=$(id -u)  # Seu ID de usuário local
```

## Licença

Este projeto é propriedade da Busco.