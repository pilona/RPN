from os import isatty, path
from sys import stdin, stdout, stderr, exit
from functools import wraps
from argparse import ArgumentParser, REMAINDER, OPTIONAL

from prompt_toolkit import PromptSession

from .util import RPNError
from .machine import Machine
from .lexer import Lexer


class InteractiveInput:
    def __init__(self, prompt):
        self.prompt = prompt

    def __iter__(self):
        try:
            session = PromptSession(message=self.prompt,
                                    vi_mode=True,
                                    enable_suspend=True,
                                    enable_open_in_editor=True,
                                    # Persistent
                                    history=None,  # TODO
                                    # Stack size? Top of stack?
                                    rprompt=None,  # TODO
                                    # TODO:
                                    # - Stack size?
                                    # - Editing mode?
                                    # - I/O format, rounding?
                                    # - Hints? Help?
                                    # - Truncated stack?
                                    bottom_toolbar=None,  # TODO
                                    prompt_continuation=' ' * len(self.prompt),
                                    # Debatable. Interferes with X11 selection.
                                    mouse_support=True,
                                    # Certainly not! But be explicit.
                                    erase_when_done=False)
            # TODO: colour, lexing, completion
            while True:
                yield session.prompt()
        except EOFError:
            return


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
            try:
                for match in lexer.lex(line):
                    if lexer.isimmediate(match) and lexer.isfeedable(match):
                        machine.feed(lexer.matchedgroups(match))
            # Abort entire rest of line, makes sense anyway
            except RPNError as e:
                # FIXME: broken with prompt_toolkit. Moves cursor up two lines
                # instead.
                print(e.args[0], file=stderr)

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
            return InteractiveInput(prompt=self.args.prompt or
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
        for short_, long_, action in [('-G', '--raw-grammar',
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

    def run(self, *, args=None):
        '''
        Run CLI, given these args, or previously passed CLI args.
        '''
        self.args = self.argument_parser.parse_args(args)
        if self.args.expressions is stdin:
            self.args.expressions = self._prompting_input()
        try:
            self.args.action()
        except KeyboardInterrupt:
            exit(1)
