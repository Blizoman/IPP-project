IMG_CHECK = ipp-check
IMG_RUN = ipp-runtime
IMG_TEST = ipp-test

# (make run ARGS="--help")
ARGS ?=

.PHONY: all pre-commit build-check check build-run run build-test test clean

all: check test

# -----------------------------------------
# 1. PRE-COMMIT
# -----------------------------------------
pre-commit:
	pre-commit run --all-files

# -----------------------------------------
# 2. CHECK STAGE (linter + decorator)
# -----------------------------------------
build-check:
	docker build --target check -t $(IMG_CHECK) .

check: build-check
	docker run --rm -v $(PWD)/python/int:/src/int -v $(PWD)/typescript/tester:/src/tester -it $(IMG_CHECK)

# -----------------------------------------
# 3. RUNTIME STAGE (py interpret)
# -----------------------------------------
build-run:
	docker build --target runtime -t $(IMG_RUN) .

run: build-run
	docker run --rm $(IMG_RUN) $(ARGS)

# -----------------------------------------
# 4. TEST STAGE (Node.js testing))
# -----------------------------------------
build-test:
	docker build --target test -t $(IMG_TEST) .

test: build-test
	docker run --rm $(IMG_TEST) $(ARGS)

# -----------------------------------------
# 5. CLEANUP
# -----------------------------------------
clean:
	docker rmi $(IMG_CHECK) $(IMG_RUN) $(IMG_TEST) -f || true
