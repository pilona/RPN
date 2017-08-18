from os import isatty, path
from sys import stdin, stdout, stderr
from functools import wraps
from argparse import ArgumentParser, REMAINDER, OPTIONAL

import rlcompleter
import readline

from .util import RPNError
from .machine import Machine
from .lexer import Lexer


class InteractiveInput:
    def __init__(self, it, prompt):
        self.it = it
        self.prompt = prompt

    def __iter__(self):
        print(self.prompt, flush=True, end='')
        for i in self.it:
            yield i
            print(self.prompt, flush=True, end='')


class CLI:
    '''
    Command line interface to RPN system.
    '''

    DEFAULT_PROMPT = '> '
    HISTORY_FILE = '~/.rpn_history'

    def dumper(self):
        '''
        Dump all lexemes matches, parse, and arity.
        '''
        machine = Machine()
        lexer = Lexer()
        print('[groups]\t<repr(repr)>\t<arity>')
        for line in self.args.expressions:
            for match in lexer.lex(line):
                matched = match.group(0)  # the lexeme text itself
                groups = lexer.matchedgroups(match)
                parsed = machine.parse(groups)
                print(*groups.keys(),
                      repr(matched),
                      machine._arity(parsed),
                      sep='\t')

    def executor(self):
        '''
        Run machine (RPN calculator).
        '''
        machine = Machine(verbose=self.args.verbose)
        lexer = Lexer()
        for line in self.args.expressions:
            # TODO: Better check here
            if self._interactive():
                readline.add_history(line.strip())

            try:
                for match in lexer.lex(line):
                    if lexer.isimmediate(match) and lexer.isfeedable(match):
                        machine.feed(lexer.matchedgroups(match))
            # Abort entire rest of line, makes sense anyway
            except RPNError as e:
                print(e.args[0], file=stderr)

    def grammar(self):
        '''
        Print manual pretty-printed grammar.
        '''
        with open('grammar.pcre') as fp:
            print(fp.read().rstrip())

    def raw_grammar(self):
        '''
        Print current internally defined grammar.
        '''
        lexer = Lexer()
        print(lexer.LEXEME)

    def _prompting_input(self):
        '''
        Return prompting stdin.__iter__ decorator...

        If either:
        - prompt explicitly specified.
        - both stdin/out are a tty
        '''
        if self.args.prompt or \
           isatty(stdin.fileno()) and isatty(stdout.fileno()):
            return InteractiveInput(stdin,
                                    prompt=self.args.prompt or
                                           self.DEFAULT_PROMPT)
        else:
            return stdin

    def __init__(self):
        '''
        Create ready to run CLI.

        Does not run or parse command line arguments.
        '''
        self.argument_parser = ArgumentParser(description='RPN calculator')
        self.argument_parser.add_argument('-v', '--verbose',
                                          action='store_true')
        int_nonint_groups = self.argument_parser.add_mutually_exclusive_group()
        int_nonint_groups.add_argument('-e', '--expression',
                                       nargs=REMAINDER,
                                       dest='expressions')
        int_nonint_groups.add_argument('-p', '--prompt',
                                       nargs=OPTIONAL,
                                       const=self.DEFAULT_PROMPT)
        main_groups = self.argument_parser.add_mutually_exclusive_group()
        for short_, long_, action in [('-g', '--grammar',
                                       self.grammar),
                                      ('-G', '--raw-grammar',
                                       self.raw_grammar),
                                      ('-D', '--dump', self.dumper)]:
            main_groups.add_argument(short_, long_,
                                     action='store_const',
                                     const=action,
                                     dest='action')
        self.argument_parser.set_defaults(action=self.executor,
                                          expressions=stdin)

    def _interactive(self):
        return isinstance(self.args.expressions, InteractiveInput)

    def _historied(f):
        @wraps(f)
        def wrapped(self, *args, **kwargs):
            history_path = path.expanduser(type(self).HISTORY_FILE)
            try:
                readline.read_history_file(history_path)
            except FileNotFoundError:
                pass
            try:
                f(self, *args, **kwargs)
            finally:
                readline.write_history_file(history_path)
        return wrapped

    @_historied
    def run(self, *, args=None):
        '''
        Run CLI, given these args, or previously passed CLI args.
        '''
        self.args = self.argument_parser.parse_args(args)
        if self.args.expressions is stdin:
            self.args.expressions = self._prompting_input()
        self.args.action()
