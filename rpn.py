#! /usr/bin/env python3

from sys import stdin
from functools import reduce

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
OPERATORS = {
    # Arithmetic
    '+': operator.__add__,
    '-': operator.__sub__,
    # FIXME: Something better? Woulda been nice to keep this for floor
    '_': operator.__neg__,
    '*': operator.__mul__,
    '/': operator.__truediv__,
    '%': operator.__mod__,
    '^': operator.__pow__,

    # Logical
    '=': operator.__eq__,
    '!': operator.__not__,

    # Bitwise
    '«': operator.__lshift__,
    '»': operator.__rshift__,
    '~': operator.__invert__,
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


def dumper():
    for line in stdin:
        for match in lex(line):
            if isimmediate(match):
                print('immediate', end=' ')
            matched = match.group(0)
            groups = matchedgroups(match).keys()
            print(*groups,
                  repr(matched))


if __name__ == '__main__':
    dumper()
