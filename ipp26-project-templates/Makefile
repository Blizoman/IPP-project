LOGIN = xpruzir00
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
	docker build --target build -t ipp-build -f Dockerfile .

cf3:
	docker build --target runtime -t ipp-runtime -f Dockerfile .

cf4:
	@docker build --target test -t ipp-test .
	@docker run --rm \
		-v $(TESTS_DIR):/opt/tests:ro \
		ipp-test /opt/tests -r > results.json
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
