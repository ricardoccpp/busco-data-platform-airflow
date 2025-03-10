FROM python:3.8-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

RUN unlink /etc/localtime
RUN ln -s /usr/share/zoneinfo/America/Sao_Paulo /etc/localtime

COPY src/ /app/src/

# CMD ["python", "src/main.py", "--subject", "teste", "--source-prefix", "dev-ricardo/cliente-02/2025/03/05/", "--target-prefix", "dev-ricardo/cliente-02/2025/03/05/"]