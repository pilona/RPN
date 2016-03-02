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
QUOTED = r'''
          '
          (?:
            [^'\\]
            |
            \\'
          )*
          '
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
IMMEDIATE = r'(?P<quoted>' + QUOTED + r')|' \
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

for line in stdin:
    start = 0
    while start < len(line):
        line = line[start:]
        match = regex.match(LEXEME, line, flags=FLAGS)
        if match is None:
            break
        matched = match.group(0)
        groups = match.groupdict()
        if groups.pop('immediate', None) is not None:
            print('immediate', end=' ')
        print(*[key
                for key, value
                in groups.items()
                if value],
              repr(matched))
        start = len(matched)
