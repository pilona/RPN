[![Coverity Scan Build Status](https://img.shields.io/coverity/scan/10257.svg)](https://scan.coverity.com/projects/pilona-rpn)
[![Travis](https://img.shields.io/travis/rust-lang/rust.svg)](https://travis-ci.org/pilona/RPN)

## Overview ##

Supports plain old arithmetic, bitwise, Python's mathematical functions, and
your usual stack operators. Not intended to be Turing-complete!

Originally intended to be a more powerful `dc`, which lacked many mathematical
functions. Is not a superset of `dc`'s featureset though. It notably lacks
macros.

## Why another RPN calculator? ##

- Wanted one in Python.
- [`rpn`](https://pypi.org/project/rpn/) has a limited feature set.
- Didn't know about [`lerpn`](https://pypi.org/project/lerpn/).
- [`pyrpn`](https://pypi.org/project/pyrpn/) is woefully incomplete.
- Disagreed with [`RPyN`](https://pypi.org/project/RPyN/) implementation;
  limited feature set.
- [`hcpy`](https://pypi.org/project/hcpy/) is missing a *few* things, and
  I don't agree with the grammar; shorthand should trump the convenience of the
  lesser used unquoted function names.
- [`pycalculator`](https://pypi.org/project/pycalculator/)'s a GUI. I don't
  intend on requiring people to have Qt installed, much less look nice, and
  there is no need for a GUI anyway, *at this time*.
- [`rpncalc`](https://pypi.org/project/rpncalc/) depends on an external
  numerical library, and one that you're not likely to already have.
- [`stacky`](https://pypi.org/project/stacky/) is a full blown language, and
  seems abandoned.
- [`pyrpncalc`](https://pypi.org/project/pyrpncalc/) has excessive printing,
  I don't agree with the code, and lacks a few features I want.

## Installation ##

Just `pip install --user https://github.com/pilona/rpn.git`.

## Usage ##

Example:

    $ rpn
    > 2 3 + 4 * p
    20.0
    > 5 f
    5.0
    20.0
    > / 3 % p
    1.0
    > c
    > f
    >

List available functions and operators:

    > h
    functions: abs acos acosh asin asinh atan atan2 atanh ceil copysign cos cosh degrees e erf erfc exp expm1 fabs factorial floor fmod frexp fsum gamma gcd hypot inf isclose isfinite isinf isnan ldexp lgamma log log10 log1p log2 modf nan phase pi polar pow radians rect sin sinh sqrt tan tanh trunc
    operators: ! % * + - / = A H I K O P R ^ _ a c d f h i j k l o p r s v x ~ « ° » ∞
    formats: D F b c d f i s t

Print pydoc of a particular operator:

    > \%H
    Help on function mod in module __main__:

    mod(left, right)
        mod(a, b) -- Same as a % b.

Push π, take the sine of it.

    > 'pi'$
    > 'sin'$
    > p
    1.2246467991473532e-16

Oops. It's floating point. Let's round to 10 decimal digits.

    > 10k
    > p
    0.0

Play with negative numbers. There is not syntactical support for prefix unary
minus. It's done using the unary minus (postfix) operator.

    > 1_ 1 +
