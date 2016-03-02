#! /usr/bin/env python3

from sys import stdin
from inspect import signature as getsignature, Parameter
from functools import reduce, wraps

import inspect

import operator

import regex

NUMBER = r'''
          (?:
            \d+
            (?:
              \.
              \d*
            )?
          )|(?:
            \d*
            \.
            \d+
          )
          '''
STR = r'''
       (?:
         '
         (?P<__str__>
             [^'\\]
             |
             \\'
         )*
         '
       )|(?:
         \
         (?P<__str__>
           .
         )
       )
       '''


# FIXME: *really* dirty hack around inspect.signature not working on some
# builtins.
def unary(f):
    # FIXME: @wraps(f) just exposes the original bug
    #@wraps(f)
    def wrapped(only):
        return f(only)
    return wrapped


def binary(f):
    #@wraps(f)
    def wrapped(left, right):
        return f(left, right)
    return wrapped


OPERATORS = {
    # Arithmetic
    '+': binary(operator.__add__),
    '-': binary(operator.__sub__),
    # FIXME: Something better? Woulda been nice to keep this for floor
    '_': unary(operator.__neg__),
    '*': binary(operator.__mul__),
    '/': binary(operator.__truediv__),
    '%': binary(operator.__mod__),
    '^': binary(operator.__pow__),

    # Logical
    '=': binary(operator.__eq__),
    '!': unary(operator.__not__),

    # Bitwise
    '«': binary(operator.__lshift__),
    '»': binary(operator.__rshift__),
    '~': unary(operator.__invert__),
}
OPERATOR = r'(?:' + '|'.join(map(regex.escape, OPERATORS)) + r')'
APPLY = r'\$'
SPACE = r'\s+'
IMMEDIATE = r'(?P<str>' + STR + r')|' \
            r'(?P<operator>' + OPERATOR + r')|' \
            r'(?P<apply>' + APPLY + r')|' \
            r'(?P<space>' + SPACE + r')'
LEXEME = r'(?P<number>' + NUMBER + r')|' \
         r'(?P<immediate>' + IMMEDIATE + r')'
FLAGS = reduce(operator.__or__,
               {regex.POSIX,
                regex.DOTALL,
                regex.VERSION1,
                regex.VERBOSE},
               0)


def lex(line):
    while line:
        match = regex.match(LEXEME, line, flags=FLAGS)
        if match is None:
            break
        yield match
        line = line[len(match.group(0)):]


def isimmediate(match):
    return 'immediate' in match.groupdict()


def matchedgroups(match):
    return {key:value
            for key, value
            in match.groupdict().items()
            if value and key != 'immediate'}


def parse(match):
    groups = matchedgroups(match)
    if 'str' in groups:
        yield groups['__str__']
    elif 'number' in groups:
        yield groups['number']
    elif 'operator' in groups:
        yield OPERATORS[groups['operator']]


def arity(f):
    if not callable(f):
        return None
    signature = inspect.signature(f)
    parameters = signature.parameters.values()
    positionals = [parameter
                   for parameter
                   in parameters
                   if parameter.kind == Parameter.POSITIONAL_OR_KEYWORD and
                      parameter.default == Parameter.empty]
    return len(positionals)


def dumper():
    print('(<immediate?>) [groups] <repr> <arity>')
    for line in stdin:
        for match in lex(line):
            if isimmediate(match):
                print('immediate', end=' ')
            matched = match.group(0)
            groups = matchedgroups(match).keys()
            parsed = next(parse(match), None)
            print(*groups,
                  repr(matched),
                  arity(parsed))


if __name__ == '__main__':
    dumper()
