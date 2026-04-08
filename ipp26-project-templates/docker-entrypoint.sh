#!/bin/bash

chmod +x /src/int/ruff
chmod +x /src/int/mypy
chmod +x /src/tester/eslint
chmod +x /src/tester/prettier

exec "$@"