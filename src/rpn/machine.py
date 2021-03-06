from sys import stderr
from decimal import Decimal
from datetime import datetime, time
from fractions import Fraction
from inspect import signature as getsignature, getdoc, Parameter
from functools import wraps, partial
from collections import deque

import operator
import math
import cmath

from .util import (RPNError, wrap_user_errors,
                   _SELECTIONS, _load_selection, _store_selection)


class Machine:
    '''
    Arithmetic stack machine (RPN calculator).

    Takes lexemes and runs them. Assumes to this particular RPN calculator
    language.
    '''

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
        '''
        Dirty hack to work around 0-arg builtins failing inspect.getsignature.
        '''
        def wrapped():
            if callable(f):
                return f()
            else:
                return f
        if callable(f):
            wrapped.__doc__ = f.__doc__
        else:
            wrapped.__doc__ = str(f)
        try:
            wrapped.__name__ = f.__name__
        except AttributeError:
            pass
        return wrapped

    # FIXME: *really* dirty hack around getsignature not working on some
    # builtins.
    def _unary(f):
        '''
        Dirty hack to work around 1-arg builtins failing inspect.getsignature.
        '''
        # FIXME: @wraps(f) just exposes the original bug
        #@wraps(f)
        def wrapped(only):
            return f(only)
        wrapped.__doc__ = f.__doc__
        try:
            wrapped.__name__ = f.__name__
        except AttributeError:
            pass
        return wrapped

    def _binary(f):
        '''
        Dirty hack to work around 2-arg builtins failing inspect.getsignature.
        '''
        #@wraps(f)
        def wrapped(left, right):
            return f(left, right)
        wrapped.__doc__ = f.__doc__
        try:
            wrapped.__name__ = f.__name__
        except AttributeError:
            pass
        return wrapped

    def _lambdoc(f, doc):
        '''
        Set anonymous function documentation.
        '''
        f.__doc__ = doc
        return f

    def _cdispatch(mathfunc, cmathfunc):
        '''
        Single dispatch to mathfunc or cmathfunc on unary argument type
        '''
        def wrapped(only):
            if isinstance(only, complex):
                return cmathfunc(only)
            else:
                return mathfunc(only)
        wrapped.__doc__ = mathfunc.__doc__
        return wrapped

    # Arithmetic operators on the items of a machine.
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

    # Unicode to function translation
    SYMBOLS = {
        # TODO: U+2200-U+222A, and more
        '\N{INFINITY}': _nullary(math.inf),
        '\N{DEGREE SIGN}': _unary(math.degrees),
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
        'abs': _unary(abs),
    }
    # FIXME: Workaround for getsignature not working on these:
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
        '''
        Create empty stack machine.

        :param verbose: Show stack traces on bad user commands.
        '''
        self.registers = dict()
        self.stack = deque()
        self.frames = deque([self.stack])
        self.ifmt = type(self).FMTS[type(self).DEFAULT_IFMT]
        self.ofmt = type(self).FMTS[type(self).DEFAULT_OFMT]
        self.precision = type(self).DEFAULT_PRECISION
        self.verbose = verbose
        # TODO: Endianness

    def feed(self, groups):
        '''
        Stack or run lexemes on machine.

        :param groups: re Match objects on lexemes.
        '''
        parsed = self.parse(groups)
        if self.isstackable(groups):
            self._pshstack(parsed)
        else:
            self._apply(parsed)

    def parse(self, groups):
        '''
        Parse lexeme match into objects for machine: numbers, callables, etc.

        :param groups: re Match objects on lexemes.
        '''
        if 'str' in groups:
            return groups['__str__']
        elif 'number' in groups:
            return self._iconvert(groups['number'])
        elif 'operator' in groups:
            operator = groups['operator']
            ref = type(self).OPERATORS[operator]
            if self.ofmt is complex:
                ref = type(self).CMATH.get(operator, ref)
            return ref
        elif 'apply' in groups:
            return self.apply

    def isstackable(self, groups):
        '''
        Return true if stackable lexeme (e.g., number), rather than runnable.
        '''
        return bool(groups.keys() & {'str', 'number'})

    def _arity(self, f):
        '''
        Return number of non-default position alrguments, if callable.
        '''
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
        '''
        Pop and run callable on top of stack, popping more arguments as needed.

        This is meant to be called externally (e.g., the apply operator), not
        internally.
        '''
        f = self._popstack()[0]
        self._apply(type(self).NAMESPACE[f])

    def _apply(self, parsed):
        '''
        Apply (callable) parsed lexeme to stack, popping arguments as needed.

        Does the real work.
        '''
        # Bind non-instance methods to self.
        # TODO: A better way of detecting this?
        if parsed in type(self).FUNCTIONS.values():
            parsed = partial(parsed, self)
        # If you don't reverse, you'll do 2**9 when you say 9 2 ^ instead of
        # 9**2.
        args = reversed(self._popstack(self._arity(parsed)))
        res = parsed(*args)
        if res is not None:
            self._pshstack(res)

    @wrap_user_errors('Cannot convert {1}')
    def _iconvert(self, number):
        '''
        Convert number to intended internal representation on input.
        '''
        # Handle the underscores in here. Ugly. FIXME?
        return self.ifmt(number.replace('_', ''))

    @wrap_user_errors('Cannot convert {1}')
    def _oconvert(self, number):
        '''
        Convert number to indended representation on output.
        '''
        return self.ofmt(number)

    def _round(self, n):
        '''
        Round number to precision (on output) if machine set to round.
        '''
        if self.precision is None:
            return n
        else:
            return round(n, self.precision)

    def print(self, *args, **kwargs):
        '''
        Round and convert/format args according to machine settings.
        '''
        return print(*[self._round(self._oconvert(arg))
                       for arg
                       in args],
                     **kwargs)

    def clrstack(self):
        '''
        Clear everything from the stack.
        '''
        self.stack.clear()

    @wrap_user_errors('Empty stack')
    def printtop(self):
        '''
        Print the element on the top of the stack.
        '''
        self.print(self.stack[-1])

    def printstack(self):
        '''
        Print all elements on the stack, top of the stack first.
        '''
        # TODO: Output endianness?
        self.print(*reversed(self.stack), sep='\n')

    def _pshstack(self, *new):
        '''
        Push all elements onto stack, leftmost at the bottom.
        '''
        self.stack.extend(new)

    pshstack = _pshstack

    def _popstack(self, n=1):
        '''
        Pop specified number of args from stack, topmost first.

        Warn if not enough args.
        '''
        if len(self.stack) < n:
            raise RPNError('Less than {} element(s) on stack'.format(n))
        return [self.stack.pop() for _ in range(n)]

    @wrap_user_errors('Empty stack')
    def dupstack(self):
        '''
        Duplicate element at top of stack.
        '''
        top = self._popstack()[0]
        self._pshstack(top)
        self._pshstack(top)

    @wrap_user_errors('Empty stack')
    def popstack(self):
        '''
        Pop and print element at top of stack.
        '''
        self.print(self._popstack()[0])

    def revstack(self):
        '''
        Swap two elements at top of stack.
        '''
        self._pshstack(*self._popstack(n=2))

    def rotstack(self, n):
        '''
        Rotate the entire stack by n.
        '''
        self.stack.rotate(int(n))

    def printhelp(self):
        '''
        Print all possible commands.
        '''
        print('functions:', *sorted(type(self).NAMESPACE), file=stderr)
        print('operators:', *sorted(type(self).OPERATORS), file=stderr)
        print('formats:', *sorted(type(self).FMTS), file=stderr)

    @staticmethod
    def _mathdoc(key, function):
        '''
        Abbreviate math.* and cmath.* documentation

        Those functions often start with their signature, which isn't exactly
        useful.
        '''
        doclines = [line.strip()
                    for line
                    in getdoc(function).splitlines()
                    if line]
        if doclines[0].startswith(key) and len(doclines) > 1:
            return doclines[1]
        else:
            return doclines[0]

    @staticmethod
    def _operatordoc(opfunc):
        '''
        Return cleaned up operator documentation
        '''
        if opfunc.__doc__:
            return getdoc(opfunc).splitlines()[0].strip()
        else:
            return opfunc.__name__

    def verbosehelp(self):
        '''
        Print table of possible commands and abbreviated help
        '''
        print('functions:', file=stderr)
        for key, mathfunc in sorted(type(self).NAMESPACE.items()):
            print(key, self._mathdoc(key, mathfunc),
                  sep=': ',
                  file=stderr)
        print('\noperators:', file=stderr)
        for key, opfunc in sorted(type(self).OPERATORS.items()):
            print(key, self._operatordoc(opfunc),
                  sep=': ',
                  file=stderr)
        print('\nformats:', file=stderr)
        for key, formatter in sorted(type(self).FMTS.items()):
            print(key, formatter.__name__,
                  sep=': ',
                  file=stderr)

    @wrap_user_errors('No such register')
    def load(self, name):
        '''
        Load variable value into stack.
        '''
        if name == '_':
            self._pshstack(None)
        elif name in _SELECTIONS:
            self._pshstack(_load_selection(_SELECTIONS[name]))
        elif not name.isupper() and name.capitalize() == name:
            self._pshstack(self.registers[name].pop())
        else:
            self._pshstack(self.registers[name])

    def store(self, value, name):
        '''
        Store value into variable.
        '''
        if not name:
            raise RPNError('Name invalid name {}'.format(repr(name)))
        elif name == '_':
            return
        elif name in _SELECTIONS:
            return _store_selection(value, _SELECTIONS[name])
        elif name.isupper():
            if name not in self.registers:
                self.registers[name] = value
            else:
                self._pshstack(value)
                raise RPNError("Attempting to assign {} to constant register {}".format(value, repr(name)))
        elif name.islower():
            self.registers[name] = value
        elif name.capitalize() == name:
            if name not in self.registers:
                self.registers[name] = []
            self.registers[name].append(value)

    @wrap_user_errors('No such format')
    def storeifmt(self, ifmt):
        '''
        Set default coercion on input.
        '''
        self.ifmt = type(self).FMTS[ifmt]

    @wrap_user_errors('No such format')
    def storeofmt(self, ofmt):
        '''
        Set default output format.
        '''
        self.ofmt = type(self).FMTS[ofmt]

    @wrap_user_errors('Bad precision')
    def storeprecision(self, precision):
        '''
        Set output rounding.
        '''
        if precision is None:
            self.precision = None
        else:
            self.precision = int(precision)

    def loadifmt(self):
        '''
        Push input coercion function to top of stack.
        '''
        self._pshstack(self.ifmt)

    def loadofmt(self):
        '''
        Push output format function to top of stack.
        '''
        self._pshstack(self.ofmt)

    def loadprecision(self):
        '''
        Push output rounding to top of stack.
        '''
        self._pshstack(self.precision)

    @wrap_user_errors('No such name')
    def help(self, name):
        '''
        Show help for operators or math function with name.
        '''
        ref = type(self).OPERATORS.get(name)
        if ref is None:
            ref = type(self).NAMESPACE.get(name)
        if ref is None:
            raise KeyError
        help(ref)

    # Language mapping to stack operations/callables.
    # TODO: Create proper lexer class bound to a Machine
    FUNCTIONS = {
        # TODO: How to bind to machine?
        'p': printtop,
        'P': popstack,
        'f': printstack,
        'd': dupstack,
        'r': revstack,
        'R': rotstack,
        # TODO: Clear all the stacks
        'c': clrstack,
        'h': printhelp,
        'V': verbosehelp,
        'H': help,
        's': store,
        'l': load,
        'i': storeifmt,
        'o': storeofmt,
        'k': storeprecision,
        'I': loadifmt,
        'O': loadofmt,
        'K': loadprecision,
    }

    # Aliases to oft used functions, so we don't need to type out their full
    # name, quoted, and apply each time.
    SHORTHAND = {
        # 'v', like in UNIX dc.
        'v': _cdispatch(math.sqrt, cmath.sqrt),
        # Unfortunately, that means you need to 3 4j + instead of 3j4, but hey,
        # it's consistent! Like _ (unary minus). No special casing. Wonder if I
        # should exceptionally make these prefix operators…
        'j': _lambdoc(lambda n: complex(0, n),
                      'complex(0, n) -- Same as 0+nj'),
    }

    # All operators, whether symbols, builtins, etc., all callable.
    # Not all functions are operators though.
    OPERATORS = dict()
    for namespace in SYMBOLS, FUNCTIONS, BUILTINS, SHORTHAND:
        OPERATORS.update(namespace)
    # The namespace of all visible callables.
    NAMESPACE = dict()
    for namespace in CMATH, MATH:
        NAMESPACE.update(namespace)
    NAMESPACE['gcd'] = math.gcd
