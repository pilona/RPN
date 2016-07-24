#! /usr/bin/env python3

from sys import stdin, stderr
from decimal import Decimal
from datetime import datetime, time
from fractions import Fraction, gcd
from inspect import signature as getsignature, Parameter
from functools import reduce, wraps, partial
from collections import deque
from argparse import ArgumentParser, REMAINDER
from warnings import warn

import operator
import math
import cmath

import regex


def wrap_user_errors(fmt):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except UserWarning:
                raise
            except Exception as e:
                raise UserWarning(fmt.format(*args, **kwargs), e)
        return wrapper
    return decorator


class Machine:
    FMTS = {
        'i': int,
        'f': float,
        'D': Decimal,

        'd': datetime.fromtimestamp,
        't': time,

        # TODO: Are these two any use?
        'c': complex,
        'F': Fraction,
    }
    DEFAULT_IFMT = 'f'
    DEFAULT_OFMT = 'f'
    DEFAULT_PRECISION = None

    def _nullary(f):
        def wrapped():
            if callable(f):
                return f()
            else:
                return f
        return wrapped

    # FIXME: *really* dirty hack around getsignature not working on some
    # builtins.
    def _unary(f):
        # FIXME: @wraps(f) just exposes the original bug
        #@wraps(f)
        def wrapped(only):
            return f(only)
        return wrapped

    def _binary(f):
        #@wraps(f)
        def wrapped(left, right):
            return f(left, right)
        return wrapped

    BUILTINS = {
        # Arithmetic
        '+': _binary(operator.__add__),
        '-': _binary(operator.__sub__),
        # FIXME: Something better? Woulda been nice to keep this for floor
        '_': _unary(operator.__neg__),
        '*': _binary(operator.__mul__),
        '/': _binary(operator.__truediv__),
        '%': _binary(operator.__mod__),
        '^': _binary(operator.__pow__),

        # Logical
        '=': _binary(operator.__eq__),
        '!': _unary(operator.__not__),

        # Bitwise
        '«': _binary(operator.__lshift__),
        '»': _binary(operator.__rshift__),
        '~': _unary(operator.__invert__),
    }

    SYMBOLS = {
        # TODO: U+2200-U+222A, and more
        '\N{INFINITY}': math.inf,
        '\N{EMPTY SET}': set(),
        '\N{INTERSECTION}': set.intersection,
        '\N{UNION}': set.union,
        '\N{DEGREE SIGN}': math.degrees,
    }

    # FIXME: Workaround for getsignature not working on these:
    MATH = {
        'acos': _unary(math.acos),
        'acosh': _unary(math.acosh),
        'asin': _unary(math.asin),
        'asinh': _unary(math.asinh),
        'atan': _unary(math.atan),
        'atan2': _binary(math.atan2),
        'atanh': _unary(math.atanh),
        'ceil': _unary(math.ceil),
        'copysign': _binary(math.copysign),
        'cos': _unary(math.cos),
        'cosh': _unary(math.cosh),
        'degrees': _unary(math.degrees),
        'e': _nullary(math.e),
        'erf': _unary(math.erf),
        'erfc': _unary(math.erfc),
        'exp': _unary(math.exp),
        'expm1': _unary(math.expm1),
        'fabs': _unary(math.fabs),
        'factorial': _unary(math.factorial),
        'floor': _unary(math.floor),
        'fmod': _unary(math.fmod),
        'frexp': _unary(math.frexp),
        'fsum': _unary(math.fsum),
        'gamma': _unary(math.gamma),
        'gcd': _binary(math.gcd),
        'hypot': _binary(math.hypot),
        'inf': _nullary(math.inf),
        'isclose': _binary(math.isclose),
        'isfinite': _unary(math.isfinite),
        'isinf': _unary(math.isinf),
        'isnan': _unary(math.isnan),
        'ldexp': _binary(math.ldexp),
        'lgamma': _unary(math.lgamma),
        'log': _unary(math.log),
        'log10': _unary(math.log10),
        'log1p': _unary(math.log1p),
        'log2': _unary(math.log2),
        'modf': _unary(math.modf),
        'nan': _nullary(math.nan),
        'pi': _nullary(math.pi),
        'pow': _binary(math.pow),
        'radians': _unary(math.radians),
        'sin': _unary(math.sin),
        'sinh': _unary(math.sinh),
        'sqrt': _unary(math.sqrt),
        'tan': _unary(math.tan),
        'tanh': _unary(math.tanh),
        'trunc': _unary(math.trunc),
    }
    CMATH = {
        'acos': _unary(cmath.acos),
        'acosh': _unary(cmath.acosh),
        'asin': _unary(cmath.asin),
        'asinh': _unary(cmath.asinh),
        'atan': _unary(cmath.atan),
        'atanh': _unary(cmath.atanh),
        'cos': _unary(cmath.cos),
        'cosh': _unary(cmath.cosh),
        'e': _nullary(cmath.e),
        'exp': _unary(cmath.exp),
        'isclose': _binary(cmath.isclose),
        'isfinite': _unary(cmath.isfinite),
        'isinf': _unary(cmath.isinf),
        'isnan': _unary(cmath.isnan),
        'log': _unary(cmath.log),
        'log10': _unary(cmath.log10),
        'phase': _unary(cmath.phase),
        'pi': _nullary(cmath.pi),
        'polar': _unary(cmath.polar),
        'rect': _binary(cmath.rect),
        'sin': _unary(cmath.sin),
        'sinh': _unary(cmath.sinh),
        'sqrt': _unary(cmath.sqrt),
        'tan': _unary(cmath.tan),
        'tanh': _unary(cmath.tanh),
    }
    #MATH = {
    #    key: value
    #    for key, value
    #    in math.__dict__.items()
    #    if not key.startswith('_')
    #}
    #CMATH = {
    #    key: value
    #    for key, value
    #    in cmath.__dict__.items()
    #    if not key.startswith('_')
    #}

    def __init__(self, verbose=None):
        self.registers = dict()
        self.stack = deque()
        self.frames = deque([self.stack])
        self.ifmt = type(self).FMTS[type(self).DEFAULT_IFMT]
        self.ofmt = type(self).FMTS[type(self).DEFAULT_OFMT]
        self.precision = type(self).DEFAULT_PRECISION
        self.verbose = verbose
        # TODO: Endianness

    def feed(self, groups):
        parsed = next(self.parse(groups))
        if self.isstackable(groups):
            self._pshstack(parsed)
        else:
            self._apply(parsed)

    def parse(self, groups):
        if 'str' in groups:
            yield groups['__str__']
        elif 'number' in groups:
            yield self._iconvert(groups['number'])
        elif 'operator' in groups:
            operator = groups['operator']
            ref = type(self).OPERATORS[operator]
            if self.ofmt is complex:
                ref = type(self).CMATH.get(operator, ref)
            yield ref
        elif 'apply' in groups:
            yield self.apply

    def isstackable(self, groups):
        return bool(groups.keys() & {'str', 'number'})

    def _arity(self, f):
        if not callable(f):
            return None
        signature = getsignature(f)
        parameters = signature.parameters.values()
        positionals = [parameter
                       for parameter
                       in parameters
                       if parameter.kind == Parameter.POSITIONAL_OR_KEYWORD and
                          parameter.default == Parameter.empty]
        return len(positionals)

    def apply(self):
        f = self._popstack()[0]
        self._apply(type(self).NAMESPACE[f])

    def _apply(self, parsed):
        if parsed in type(self).FUNCTIONS.values():
            parsed = partial(parsed, self)
        # If you don't do this, you'll do 2**9 when you say 9 2 ^ instead of
        # 9**2.
        args = reversed(self._popstack(self._arity(parsed)))
        res = parsed(*args)
        if res is not None:
            self._pshstack(res)

    @wrap_user_errors('Cannot convert {1}')
    def _iconvert(self, number):
        return self.ifmt(number.replace('_', ''))

    @wrap_user_errors('Cannot convert {1}')
    def _oconvert(self, number):
        return self.ofmt(number)

    def _round(self, n):
        if self.precision is None:
            return n
        else:
            return round(n, self.precision)

    def print(self, *args, **kwargs):
        return print(*[self._round(self._oconvert(arg))
                       for arg
                       in args],
                     **kwargs)

    def clrstack(self):
        self.stack.clear()

    @wrap_user_errors('Empty stack')
    def printtop(self):
        self.print(self.stack[-1])

    def printcur(self):
        # TODO: Output endianness?
        self.print(*reversed(self.stack), sep='\n')

    def _pshstack(self, *new):
        self.stack.extend(new)

    pshstack = _pshstack

    def _popstack(self, n=1):
        if len(self.stack) < n:
            raise UserWarning('Less than {} elements on stack'.format(n))
        return [self.stack.pop() for _ in range(n)]

    @wrap_user_errors('Empty stack')
    def dupstack(self):
        top = self._popstack()[0]
        self._pshstack(top)
        self._pshstack(top)

    @wrap_user_errors('Empty stack')
    def popstack(self):
        self.print(self._popstack()[0])

    def revstack(self):
        self._pshstack(*self._popstack(n=2))

    def rotstack(self, n):
        self.stack.rotate(int(n))

    def printhelp(self):
        print('functions:', *sorted(type(self).NAMESPACE), file=stderr)
        print('operators:', *sorted(type(self).OPERATORS), file=stderr)
        print('formats:', *sorted(type(self).FMTS), file=stderr)

    @wrap_user_errors('No such register')
    def load(self, name):
        self._pshstack(self.registers[name])

    def store(self, name, value):
        self.registers[name] = value

    @wrap_user_errors('No such format')
    def storeifmt(self, ifmt):
        self.ifmt = type(self).FMTS[ifmt]

    @wrap_user_errors('No such format')
    def storeofmt(self, ofmt):
        self.ofmt = type(self).FMTS[ofmt]

    @wrap_user_errors('Bad precision')
    def storeprecision(self, precision):
        self.precision = int(precision)

    def loadifmt(self):
        self._pshstack(self.ifmt)

    def loadofmt(self):
        self._pshstack(self.ofmt)

    def loadprecision(self):
        self._pshstack(self.precision)

    # TODO: Create proper lexer class bound to a Machine
    FUNCTIONS = {
        # TODO: How to bind to machine?
        'p': printtop,
        'P': popstack,
        'f': printcur,
        'd': dupstack,
        'r': revstack,
        'R': rotstack,
        # TODO: Clear all the stacks
        'c': clrstack,
        'h': printhelp,
        's': store,
        'l': load,
        'i': storeifmt,
        'o': storeofmt,
        'k': storeprecision,
        'I': loadifmt,
        'O': loadofmt,
        'K': loadprecision,
    }

    SHORTHAND = {
        'v': _unary(math.sqrt),
        'j': lambda n: complex(0, n)
    }

    OPERATORS = dict()
    for namespace in SYMBOLS, FUNCTIONS, BUILTINS, SHORTHAND:
        OPERATORS.update(namespace)
    NAMESPACE = dict()
    for namespace in CMATH, MATH:
        NAMESPACE.update(namespace)
    NAMESPACE['gcd'] = gcd


class Lexer:
    # Support not just digits, but thousands separators
    DIGITS = r'(?:\d{1,3}(\d{3}|_)*)'
    # String formatting and regex is a tricky business, because of the braces.
    # It works here. Be careful in general!
    NUMBER = r'''
              (?:
                  {DIGITS}+
                  (?:
                  \.
                  {DIGITS}*
                  )?
              )|(?:
                  {DIGITS}*
                  \.
                  {DIGITS}+
              )
              '''.format(DIGITS=DIGITS)
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
    APPLY = r'\$'
    SPACE = r'\s+'

    IMMEDIATE = r'(?<operator>' + OPERATOR + r')|' \
                r'(?<apply>' + APPLY + r')|' \
                r'(?<space>' + SPACE + r')'
    LEXEME = r'(?<number>' + NUMBER + r')|' \
             r'(?<str>' + STR + r')|' \
             r'(?<immediate>' + IMMEDIATE + r')'
    FLAGS = reduce(operator.__or__,
                   {regex.POSIX,
                       regex.DOTALL,
                       regex.VERSION1,
                       regex.VERBOSE},
                   0)

    def __init__(self, machine):
        self.machine = machine

    def feed(line):
        raise NotImplementedError()

    def lex(self, line):
        while line:
            match = regex.match(type(self).LEXEME, line,
                                flags=type(self).FLAGS)
            if match is None:
                break
            yield match
            line = line[len(match.group(0)):]

    def isfeedable(self, match):
        return 'space' not in self.matchedgroups(match).keys()

    def isimmediate(self, match):
        return 'immediate' in match.groupdict()

    def matchedgroups(self, match):
        return {key: value
                for key, value
                in match.groupdict().items()
                if value and key != 'immediate'}


class CLI:
    def dumper(self):
        machine = Machine()
        lexer = Lexer()
        print('[groups]\t<repr(repr)>\t<arity>')
        for line in self.args.expressions:
            for match in lexer.lex(line):
                matched = match.group(0)
                groups = lexer.matchedgroups(match).keys()
                parsed = next(machine.parse(match), None)
                print(*groups,
                      repr(matched),
                      machine._arity(parsed),
                      sep='\t')

    def executor(self):
        machine = Machine(verbose=self.args.verbose)
        lexer = Lexer()
        for line in self.args.expressions:
            for match in lexer.lex(line):
                if lexer.isimmediate(match) and lexer.isfeedable(match):
                    try:
                        machine.feed(lexer.matchedgroups(match))
                    except UserWarning as e:
                        print(e.args[0])
                        if machine.verbose:
                            warn(e.args[1])

    def grammar(self):
        with open('grammar.pcre') as fp:
            print(fp.read().rstrip())

    def raw_grammar(self):
        lexer = Lexer()
        print(lexer.LEXEME)

    def __init__(self):
        self.argument_parser = ArgumentParser(description='RPN calculator')
        self.argument_parser.add_argument('-v', '--verbose',
                                          action='store_true')
        self.argument_parser.add_argument('-e', '--expression',
                                          nargs=REMAINDER,
                                          dest='expressions')
        for short_, long_, action in [('-g', '--grammar',
                                       self.grammar),
                                      ('-G', '--raw-grammar',
                                       self.raw_grammar),
                                      ('-D', '--dump', self.dumper)]:
            self.argument_parser.add_argument(short_, long_,
                                              action='store_const',
                                              const=action,
                                              dest='action')
        self.argument_parser.set_defaults(action=self.executor,
                                          expressions=stdin)

    def run(self):
        self.args = self.argument_parser.parse_args()
        self.args.action()


__all__ = 'Machine', 'Lexer', 'CLI'


if __name__ == '__main__':
    cli = CLI()
    cli.run()
