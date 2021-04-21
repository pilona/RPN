include .test.Makefile
include .lint.Makefile

all: check coverage lint

venv:
	@python -m venv venv

install: venv
	@./venv/bin/pip install wheel
	@./venv/bin/pip install -r requirements.txt .

dev_install: install
	@./venv/bin/pip install -U -r requirements.dev.txt -e .

clean:
	@rm -rf .coverage htmlcov

.PHONY: all lint check test coverage clean
