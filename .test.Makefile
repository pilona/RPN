test: pytest

pytest:
	@pytest -vv --cov=src --cov=tests --cov-fail-under=95 --no-cov-on-fail

# We use pytest anyway.
#unittest:
#	@cd tests && python -m unittest test_*.py

coverage:
	@coverage html
