from functools import reduce
import operator

import regex

from .util import RPNError
from .machine import Machine


class Lexer:
    '''
    Lexer for the RPN *regular* grammar.

    For consistency, for now, needs to be instantiated, despite holding no
    internal state.
    '''
    # Integral part of a number
    INTEGRAL = r'''
                # DO NOT REPEAT ME! I REPEAT MYSELF INTERNALLY!
                (?:
                    # 1, 12, or the 1 in 1_200.
                    \d{1,3}
                    (?:
                        # The 4, 45, etc. in 1234, 12345, etc.
                        \d
                        |
                        # Support not just digits, but thousands separators
                        (?:
                            _\d{3}
                        )
                    )*
                )
                '''
    # Fractional part of a number
    FRACTIONAL = r'''
                  # DO NOT REPEAT ME! I REPEAT MYSELF INTERNALLY!
                  (?:
                      # 1, 12, or the 1 in 1_200.
                      # TODO: Handle when number of digits % 3 ≠ 0.
                      \d+
                      |
                      (?:
                          \d{3}
                          (?:
                              _\d{3}
                          )*
                          (?:
                              _\d{1,2}
                          )?
                      )*
                  )
                  '''
    # Number, of any kind supported by grammar.
    # String formatting and regex is a tricky business, because of the braces.
    # It works here. Be careful in general!
    NUMBER = r'''
              (?:
                  # 1, 12, 1_200, 1_200. (notice trailing dot), 1.3
                  {INTEGRAL}
                  (?:
                      \.
                      {FRACTIONAL}?
                  )?
              )|(?:
                  # .2, 0.2, 0.200_200 but not 0.2_200
                  {INTEGRAL}?
                  \.
                  {FRACTIONAL}
              )
              '''.format(INTEGRAL=INTEGRAL, FRACTIONAL=FRACTIONAL)
    # String
    STR = r'''
           (?:
               '
               (?<__str__>
                   (?:
                       [^'\\]
                       |
                       \\'
                   )*
               )
               '
           )|(?:
               \\
               (?<__str__>
                   .
               )
           )
           '''

    assert not [operator
                for operator
                in Machine.OPERATORS
                if len(operator) != 1]
    OPERATOR = r'(?:' + r'|'.join(map(regex.escape, Machine.OPERATORS)) + r')'
    # TODO: a and A instead? Would make this no longer a special case, which is
    # kinda nice.
    # $ like in Haskell apply, but of course, eagerly evaluated, not curriable.
    APPLY = r'\$'
    SPACE = r'\s+'

    # Immediate, as in immediately complete lexeme
    IMMEDIATE = r'(?<operator>' + OPERATOR + r')|' \
                r'(?<apply>' + APPLY + r')|' \
                r'(?<space>' + SPACE + r')'
    # All possible lexemes.
    LEXEME = r'(?<number>' + NUMBER + r')|' \
             r'(?<str>' + STR + r')|' \
             r'(?<immediate>' + IMMEDIATE + r')'
    # Default regex flags for matching lexemes
    FLAGS = reduce(operator.__or__,
                   {regex.POSIX,
                    regex.DOTALL,
                    regex.VERSION1,
                    regex.VERBOSE},
                   0)

    def lex(self, line):
        '''
        Take a line and return all lexemes.

        Doesn't yield incomplete or incorrect lexemes, stopping on first bad.
        '''
        while line:
            match = regex.match(type(self).LEXEME, line,
                                flags=type(self).FLAGS)
            if match is None:
                break
            yield match
            line = line[len(match.group(0)):]
        if line:
            raise RPNError("Couldn\'t lex {0}".format(line.strip()))

    def isfeedable(self, match):
        '''
        Return True if lexeme can be fed to machine.
        '''
        return 'space' not in self.matchedgroups(match).keys()

    def isimmediate(self, match):
        '''
        Return true if lexeme is unambiguously complete.
        '''
        return 'immediate' in match.groupdict()

    def matchedgroups(self, match):
        '''
        Yield lexeme matches.
        '''
        return {key: value
                for key, value
                in match.groupdict().items()
                if value and key != 'immediate'}
