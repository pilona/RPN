from pytest import Item


def pytest_assertion_pass(item: Item,
                          lineno: int,
                          orig: str,
                          expl: str) -> None:
    '''
    Log every assertion, in case we later need to audit a run.

    Excessive in most cases.

    Use with pytest -rP.
    '''
    # Not bothering with make-style output that you can feed into a Vim
    # quickfix list and iterate over.
    print('given', item.name + ':' + str(lineno), str(orig))  # no repr()!)
    print('actual', item.name + ':' + str(lineno),
          # Get rid of full-diff, -vv for full diff, etc.
          # TODO: Make work when multiline output.
          '\n'.join(str(expl).splitlines()[:-2]))
