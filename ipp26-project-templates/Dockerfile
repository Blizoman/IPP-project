# CHECK
FROM python:3.14-bookworm AS check
WORKDIR /src

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

# BUILD
FROM python:3.14-slim AS build
WORKDIR /src
COPY python/int/src/ ./int/src/

# BUILD-TEST
FROM node:24-bookworm AS build-test
WORKDIR /src
COPY typescript/tester/package*.json ./
RUN npm install
COPY typescript/tester/ ./
RUN npm run build && \
    npm prune --omit=dev

# RUNTIME
# mensia size
FROM python:3.14-slim AS runtime
WORKDIR /src
RUN pip install --no-cache-dir pydantic pydantic-xml lxml
COPY --from=build /src/int /src/int

ENV PYTHONPATH="/src/int/src"
## basic cesta v ENTRYPOINTE nesla, chatar cez -m (modul)
ENTRYPOINT ["python3", "-m", "interpreter.interpreter"]

# TEST
FROM runtime AS test
RUN apt-get update && \
    apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_24.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY --from=build-test /src/dist /src/tester/dist
COPY --from=build-test /src/node_modules /src/tester/node_modules
COPY --from=build-test /src/package.json /src/tester/
ENTRYPOINT ["node", "/src/tester/dist/tester.js"]
