'''
RPN lexer tests
'''

import regex

from rpn.util import RPNError
from rpn.lexer import Lexer

from pytest import raises


def test_even_backslashes():
    l = Lexer()
    matches = l.lex(r"'\\\\foo'")
    assert [m.group('__str__') for m in matches] == [r'\\\\foo']


def test_unknown_backslash():
    l = Lexer()
    with raises(RPNError, match=regex.escape(r"Couldn't lex '\f'")):
        list(l.lex(r"'\f'"))


def test_incomplete_backslash():
    l = Lexer()
    with raises(RPNError, match=regex.escape(r"Couldn't lex '\'")):
        list(l.lex(r"'\'"))


def test_odd_backslashes():
    l = Lexer()
    matches = l.lex(r"'\''")
    # We don't reduce backslashes yet. That's the parser's job.
    assert [m.group('__str__') for m in matches] == [r"\'"]

    matches = l.lex(r"'\\\''")
    assert [m.group('__str__') for m in matches] == [r"\\\'"]
