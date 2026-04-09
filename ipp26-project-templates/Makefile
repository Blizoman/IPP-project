LOGIN = xblizna00
TESTS_DIR ?= $(CURDIR)/tests

.PHONY: setup c clean zip commit cf1 cf2 cf3 cf4

################################
############ SETUP ############

# Requires uv: curl -LsSf https://astral.sh/uv/install.sh | sh
setup:
	sudo apt-get install -y libxml2-dev libxslt-dev
	rm -rf tester/venv
	uv venv tester/venv --python 3.14
	uv pip install --python tester/venv/bin/python \
		-r tester/requirements.txt \
		-r tester/requirements-dev.txt \
		-r sol2xml/requirements.txt
	cd int && npm install

############ SETUP ############
################################
############ CLEAN #############

c: clean
clean:
	rm -f results.json
	rm -rf int/dist
	rm -rf .mypy_cache
	rm -rf tester/src/__pycache__
	rm -f $(LOGIN).zip
	rm -rf parses
	rm -rf sol2xml/out/
	clear

############ CLEAN #############
################################
############# SEND #############

zip: clean
	zip -r $(LOGIN).zip \
		int/ \
		tester/ \
		Dockerfile \
		ai_audit.md \
		-x "*/node_modules/*" \
		-x "*/dist/*" \
		-x "*/__pycache__/*" \
		-x "*/venv/*" \
		-x "*/.venv/*" \
		-x "*/.git/*" \
		-x "*/.*" \
		-x "*.DS_Store" \
		-x "*__MACOSX*"

############# SEND #############
################################
############ COMMIT ############

m ?= "Auto-commit"
commit:
	git add -A
	PATH="$$(pwd)/tester/venv/bin:$$PATH" git commit -m "$(m)"
fommit:
	git add -A
	PATH="$$(pwd)/tester/venv/bin:$$PATH" git commit -m "$(m)" --no-verify

############ COMMIT ############
################################
############ DOCKER ############
PWD := $(shell pwd)
cf1:
	pwd
	docker build --target check --tag ipp-check .
	docker run --rm -it -v $(PWD)/python/int:/src/int/ -v $(PWD)/typescript/tester/:/src/tester/ ipp-check

cf2:
	docker build --target build-test -t ipp-build -f Dockerfile .

cf3:
	docker build --target runtime -t ipp-runtime -f Dockerfile .

cf4:
	@docker build --target test -t ipp-test .
	@docker run --rm \
		-v $(TESTS_DIR):/opt/tests:ro \
		ipp-test /opt/tests -r > results.json
	@printf '%s\n' \
		'import json' \
		'from pathlib import Path' \
		'' \
		'results_path = Path("results.json")' \
		'if not results_path.exists():' \
		'    raise SystemExit("results.json was not generated")' \
		'' \
		'report = json.loads(results_path.read_text(encoding="utf-8"))' \
		'green = "\033[32m"' \
		'red = "\033[31m"' \
		'reset = "\033[0m"' \
		'passed = 0' \
		'failed = 0' \
		'results = report.get("results") or {}' \
		'for category in sorted(results):' \
		'    test_results = (results.get(category) or {}).get("test_results") or {}' \
		'    for test_name in sorted(test_results):' \
		'        test_result = (test_results.get(test_name) or {}).get("result")' \
		'        if test_result == "passed":' \
		'            passed += 1' \
		'            print(f"{green}PASS{reset} {test_name} ({category})")' \
		'        else:' \
		'            failed += 1' \
		'            print(f"{red}FAIL{reset} {test_name} ({category}) [{test_result}]")' \
		'unexecuted = report.get("unexecuted") or {}' \
		'for test_name in sorted(unexecuted):' \
		'    failed += 1' \
		'    reason = (unexecuted.get(test_name) or {}).get("message") or "UNEXECUTED"' \
		'    print(f"{red}FAIL{reset} {test_name} [UNEXECUTED: {reason}]")' \
		'print(f"Summary: {green}{passed}{reset} passed, {red}{failed}{reset} failed")' \
	| python3 -
	
# 	@$(MAKE) done

cf4-dry:
	@docker build --target test -t ipp-test .
	@docker run --rm \
		-v $(TESTS_DIR):/opt/tests:ro \
		ipp-test /opt/tests --recursive --dry-run

############ DOCKER ############
################################

circ_deps:
	npx madge --circular ./int/src/solint.ts

precommit:
	cd ./python/int && uv run pre-commit run --all-files

GREEN = \033[1;32m
NC = \033[0m # No Color
done:
	clear
	@printf "$(GREEN) ____   ___  _   _ _____ $(NC)\n"
	@printf "$(GREEN)|  _ \ / _ \| \ | | ____|$(NC)\n"
	@printf "$(GREEN)| | | | | | |  \| |  _|  $(NC)\n"
	@printf "$(GREEN)| |_| | |_| | |\  | |___ $(NC)\n"
	@printf "$(GREEN)|____/ \___/|_| \_|_____|$(NC)\n"
