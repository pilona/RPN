'''
RPN calculator.

Supports plain old arithmetic, bitwise, Python's mathematical functions, and
your usual stack operators. Not intended to be Turing-complete!

Originally intended to be a more powerful dc, which lacked many mathematical
functions. Is not a superset of dc's featureset though.

Why another RPN calculator?

- Wanted one in Python.
- rpn has a limited feature set.
- Didn't know about lerpn.
- pyrpn is woefully incomplete.
- Disagreed with RPyN implementation; limited feature set.
- hcpy is missing a *few* things, and I don't agree with the grammar; shorthand
  should trump the convenience of the lesser used unquoted function names.
- pycalculator's a GUI.
- rpncalc depends on an external numerical library, and one that you're not
  likely to already have.
- stacky is a full blown language, and seems abandoned.
- pyrpncalc has excessive printing, I don't agree with the code, and lacks a
  few features I want.
'''

# TODO: Thousands separator formatting.
# TODO: Stack center-align numbers, on the decimal point
# TODO: Hex, octal, binary; yes, as a programmer, I sometimes need these
# TODO: Macros
# TODO: complex <-> {polar, reim, cartesian}
# TODO: Should load{alignment,ifmt,ofmt,precision} reset them
#       to their default values? People can just dup and store, right?

from .cli import CLI
from .lexer import Lexer
from .machine import Machine


__all__ = 'Machine', 'Lexer', 'CLI'
