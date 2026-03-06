# CHECK
FROM python:3.12-bookworm AS check
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y nodejs && \
    pip install uv

WORKDIR /src
ENTRYPOINT ["/bin/bash"]

# BUILD-TEST
FROM node:24-bookworm AS build-test
WORKDIR /app
COPY typescript/tester/package*.json ./
RUN npm install
COPY typescript/tester/ ./
RUN npm run build

# RUNTIME
FROM python:3.12-slim AS runtime
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y nodejs
WORKDIR /app

# lejtr copy interpretu will see
# COPY python/interpret/ .
# ENTRYPOINT ["python3", "main.py"]

# TEST
FROM runtime AS test
WORKDIR /app
COPY --from=build-test /app/dist ./dist
COPY --from=build-test /app/node_modules ./node_modules
ENTRYPOINT ["node", "dist/tester.js"]