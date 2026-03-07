#!/bin/bash

ln -sf $(which ruff) /src/int/ruff
ln -sf $(which mypy) /src/int/mypy
ln -sf $(which eslint) /src/tester/eslint
ln -sf $(which prettier) /src/tester/prettier

exec "$@"
