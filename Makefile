all: check coverage lint

lint:
	@flake8 rpn

check:
	@flake8 --select=F rpn

test:
	@python setup.py test --addopts -vv

coverage:
	@coverage html

clean:
	@rm -rf .coverage htmlcov

.PHONY: all lint check test coverage clean
