lint:
	@flake8 src tests

check:
	@flake8 --select=F src tests

# TODO: Get rid of that annoying backslash in output.
bandit:
	@bandit -q -r -f custom \
	        --msg-template '{relpath}:{line}: {msg} \
	-- {range} {test_id} {confidence} {severity}' \
	        src
mypy:
	@mypy src tests

safety_check:
	@safety check --bare --full-report

pip_check:
	@pip check

trailing_whitespace:
	@! git grep --color=always -E '\s+$$'

git_check:
	@git diff --color=always @{upstream} --check
