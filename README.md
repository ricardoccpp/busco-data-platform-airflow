# Busco Data Platform Pipeline

Plataforma completa de processamento de dados baseada em Apache Airflow (2.10.5) para orquestração de pipelines com ECS para processamento de dados no datalake da Busco, implementando um padrão moderno de arquitetura em três camadas.

## Arquitetura

```
┌─────────────────┐                ┌───────────────────┐
│    Airflow      │                │  ECS Tasks        │
│   (Orquestrador)│◄──Invoca────►  │   (DuckDB)        │
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

### Camadas do Data Lake

- **Bronze**: Dados brutos ingeridos dos sistemas de origem
- **Silver**: Dados limpos, normalizados e validados 
- **Gold**: Dados agregados e modelados para consumo por aplicações de BI e analytics

## Componentes Principais

### Apache Airflow (2.10.5)

**Função**: Orquestrador de pipelines de dados responsável por agendar, monitorar e gerenciar fluxos de trabalho.

**Configurações**:
- **Desenvolvimento**: Contêineres Docker com PostgreSQL 16.3-alpine local
- **Produção**: Contêineres Docker em EC2 com RDS PostgreSQL

### ECS Tasks com DuckDB

**Função**: Processamento eficiente de dados entre as camadas do datalake.

**Infraestrutura**: Tarefas ECS executadas sob demanda, invocadas pelo Airflow usando o operador `EcsRunTaskOperator`.

**Processamento**:
- Transformações de bronze para silver
- Transformações de silver para gold
- Processamento baseado em eventos S3

## Estrutura do Projeto

```
busco-data-platform-pipeline/
├── Dockerfile                   # Imagem base do Airflow (dev/prod)
├── .env.example                 # Modelo para configurações de ambiente
├── .gitignore                   # Arquivos ignorados pelo Git
├── README.md                    # Documentação do projeto
├── config/                      # Configurações do Airflow
│   ├── airflow.cfg             # Configuração principal
│   └── webserver_config.py     # Configuração da interface web
├── dags/                        # DAGs para orquestração
│   ├── teste.py                # DAG de exemplo
│   └── teste2.py               # DAG com ECS task
├── deployment/                  # Scripts de deployment
│   └── aws/                     # Scripts específicos da AWS
│       ├── check_ssl.sh        # Verificação de certificados SSL
│       └── systemd/            # Configurações do serviço systemd
├── docker-compose.yml           # Configuração Docker para desenvolvimento
├── docker-compose.prod.yml      # Configuração Docker para produção
├── docker-compose.prod.letsencrypt.yml # Configuração para certificados SSL
└── scripts/                     # Scripts utilitários
    ├── ec2_deploy.sh           # Deploy para instância EC2
    ├── ecr_push.sh             # Envio de imagem para ECR
    ├── entrypoint.sh           # Ponto de entrada dos contêineres
    ├── local_build.sh          # Build da imagem local
    ├── set_local_dir_permission.sh # Ajuste de permissões
    ├── setup_connections.py    # Configuração de conexões do Airflow
    ├── setup_systemd.sh        # Configuração do serviço systemd
    └── wait-for-it.sh          # Utilitário para verificar disponibilidade de serviços
```

## Estrutura do Data Lake

```
s3://busco-data-lake/
  ├── bronze/      # Dados brutos ingeridos
  ├── silver/      # Dados limpos e validados
  └── gold/        # Dados modelados para consumo
```

## Guias Rápidos

### Pré-requisitos

- Docker e Docker Compose
- AWS CLI configurado
- Python 3.9+
- Acesso aos recursos AWS (EC2, ECR, ECS, S3, Glue)
- Task definitions para ECS já criadas via Terraform

### Configuração Inicial

1. Clone o repositório e configure o arquivo `.env`:

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/busco-data-platform-pipeline.git
cd busco-data-platform-pipeline

# Configure o ambiente
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

### Ambiente de Desenvolvimento Local

```bash
# Construir a imagem de desenvolvimento
./scripts/local_build.sh

# Iniciar o Airflow localmente
docker-compose up -d

# Acessar a interface do Airflow
# http://localhost:8080 (usuário/senha: admin/admin)
```

### Deploy para Produção

1. Build e envio da imagem para ECR:

```bash
# Construir imagem de produção
./scripts/local_build.sh

# Enviar para o ECR
./scripts/ecr_push.sh prod
```

2. Deploy para a instância EC2:

```bash
# Realizar deploy no EC2
./scripts/ec2_deploy.sh <ec2-host> <path-to-ssh-key.pem>
```

3. O script irá configurar:
   - Docker e Docker Compose na instância EC2
   - Certificado SSL via Let's Encrypt
   - Serviço Systemd para inicialização automática
   - Crontab para renovação do certificado SSL

## Fluxo de Trabalho de Desenvolvimento

1. **Desenvolvimento Local**:
   - Desenvolva DAGs e plugins no ambiente local
   - Teste usando a imagem de desenvolvimento
   - Verifique logs e resultados via interface web

2. **Testes Integrados**:
   - Valide a execução de tarefas ECS com dados de teste
   - Verifique transformações entre camadas do datalake

3. **Deploy para Produção**:
   - Construa a imagem de produção
   - Envie para o repositório ECR
   - Realize deploy na instância EC2

## Workflow de Ingestão/Processamento

1. **Ingestão para Bronze**: Dados brutos são armazenados na camada Bronze
2. **Evento S3**: Um evento de criação/modificação de arquivo no S3 dispara uma DAG
3. **Processamento Bronze para Silver**: DAG aciona tarefa ECS que processa os dados
4. **Processamento Silver para Gold**: Dados processados são transformados para consumo
5. **Disponibilização**: Dados ficam disponíveis para consulta via Athena/Glue ou ferramentas de BI

## Segurança e Configurações

### Segredos e Variáveis de Ambiente

Os seguintes parâmetros devem ser configurados no arquivo `.env`:

- Credenciais PostgreSQL
- Chave Fernet para criptografia do Airflow
- Credenciais AWS (Access Key, Secret Key)
- Detalhes do ECS (clusters, task definitions)
- URIs de repositórios ECR

### Permissões de Arquivos

Para evitar problemas de permissão ao trabalhar com volumes Docker mapeados:

```bash
# Configurar o ID de usuário no arquivo .env
AIRFLOW_UID=$(id -u)  # Seu ID de usuário local

# Ajustar permissões em diretórios locais
./scripts/set_local_dir_permission.sh
```

## Infraestrutura AWS

- **ECR**: Repositório para imagens Docker do Airflow
- **EC2**: Instância para execução do Airflow
- **ECS**: Execução de tarefas de processamento de dados
- **S3**: Armazenamento dos dados nas camadas do datalake
- **RDS** (Produção): Banco de dados PostgreSQL para o Airflow
- **Glue/Athena**: Descoberta e consulta de dados

## Monitoramento

- **Airflow UI**: Monitoramento de DAGs e tarefas (http://localhost:8080)
- **Flower**: Dashboard para monitoramento de workers Celery (http://localhost:5555)
- **CloudWatch**: Logs e métricas de recursos AWS
- **ECS Task Logs**: Logs das tarefas de processamento

## Serviços Docker Compose

### Desenvolvimento (docker-compose.yml)
- **postgres**: Banco de dados PostgreSQL
- **redis**: Backend para Celery
- **airflow-webserver**: Interface web
- **airflow-scheduler**: Scheduler do Airflow
- **airflow-worker**: Worker Celery
- **airflow-triggerer**: Triggerer para deferrable operators
- **airflow-init**: Inicialização do banco e usuários
- **flower**: Dashboard de monitoramento Celery

### Produção (docker-compose.prod.yml)
Inclui todos os serviços acima, mais:
- **nginx-proxy**: Proxy reverso com suporte a HTTPS
- **letsencrypt**: Serviço para obtenção/renovação de certificados SSL