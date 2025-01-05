# Usar imagem base leve do Python
FROM python:3.10-slim

# Definir o diretório de trabalho no contêiner
WORKDIR /app

# Copiar o código para o contêiner
COPY locals_fast_api.py /app/locals_fast_api.py

# Instalar as dependências
RUN pip install --no-cache-dir fastapi uvicorn requests apscheduler

# Expor a porta 8000
EXPOSE 8000

# Comando para iniciar o servidor FastAPI
CMD ["uvicorn", "locals_fast_api:app", "--host", "0.0.0.0", "--port", "8000"]
