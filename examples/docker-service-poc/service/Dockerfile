
FROM node:20-slim as node_base
FROM python:3.11-slim

# 1. Setup ambiente ibrido Node+Python
COPY --from=node_base /usr/local/bin/node /usr/local/bin/
COPY --from=node_base /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm

# 2. Installazione dipendenze di sistema
# git è necessario se pip installa da git, ma qui installeremo da locale
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# 3. Installazione Qwen CLI
RUN npm install -g @qwen-code/qwen-code

# 4. Setup Working Directory
WORKDIR /app

# 5. Copia e installazione della libreria corrente (credential-rotation)
# Nota: Il context di build sarà la root del progetto
COPY . .
RUN pip install . 
RUN pip install fastapi uvicorn requests

# 6. Copia dello script server
COPY examples/docker-service-poc/service/server.py .

# 7. Avvio
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
