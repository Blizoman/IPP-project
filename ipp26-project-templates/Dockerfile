# CHECK
FROM python:3.14-bookworm AS check
WORKDIR /src

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN apt-get update && \
    apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y nodejs

RUN pip install ruff==0.14 mypy==1.19 && \
    npm install -g eslint@9.32 prettier@3.7 typescript typescript-eslint@8.52

RUN mkdir -p /src/int /src/tester

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["/bin/bash"]

# BUILD-TEST
FROM node:24-bookworm AS build-test
WORKDIR /src
COPY typescript/tester/package*.json ./
RUN npm install
COPY typescript/tester/ ./
RUN npm run build && \
    npm prune --omit=dev

# RUNTIME
FROM python:3.14-slim AS runtime
WORKDIR /src
RUN apt-get update && apt-get install -y libxml2-dev libxslt-dev gcc zlib1g-dev build-essential && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir pydantic pydantic-xml lxml lark==1.2.2
COPY python/int/src/ ./int/src/

ENV PYTHONPATH="/src/int/src"
ENTRYPOINT ["python3", "/src/int/src/solint.py"]

# TEST
FROM runtime AS test
RUN apt-get update && \
    apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY sol2xml/ /src/sol2xml/

COPY --from=build-test /src/dist /src/tester/dist
COPY --from=build-test /src/node_modules /src/tester/node_modules
COPY --from=build-test /src/package.json /src/tester/
ENTRYPOINT ["node", "/src/tester/dist/tester.js"]
