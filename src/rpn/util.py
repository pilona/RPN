from functools import wraps
import subprocess


_SELECTIONS = {
    '+': 'clipboard',
    '*': 'primary',
}


def _store_selection(data, selection):
    with subprocess.Popen(['xclip',
                           '-selection', selection],
                          stdin=subprocess.PIPE) as xclip:
        xclip.stdin.write(str(data).encode())


def _load_selection(selection):
    with subprocess.Popen(['xclip',
                           '-selection', selection,
                           '-o'], stdout=subprocess.PIPE) as xclip:
        return xclip.stdout.read().decode()


class RPNError(Exception):
    pass


def wrap_user_errors(fmt):
    '''
    Ugly hack decorator that converts exceptions to warnings.

    Passes through RPNErrors.
    '''
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except RPNError:
                raise
            except Exception as e:
                raise RPNError(fmt.format(*args, **kwargs), e)
        return wrapper
    return decorator
