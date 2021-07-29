"""
This module defines decorators to be used on functions.
The decorator will simply wrap the callable object without
crawling through its attributes.
"""

import functools

__exclude__ = list(globals())


def decorator_varargs(decorator):
    """
    Decorator that makes decorator arguments optional
    for decorators applied to callable objects

    Restriction
    - Decorator can safely require only 1 positional argument (decorator target)
        * All additional arguments should be optional via defaults or varargs
        * Otherwise, the client is responsible for its proper invocation
    - Decorator target must be callable
    - If passing callable decorator argument, adhere to at least 1 of:
        * Pass as keyword argument
        * Pass at least 2 arguments
    """
    if not callable(decorator):
        raise TypeError(f"Must be used on a decorator: {decorator}")

    @functools.wraps(decorator)
    def wrapped_decorator(*args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
            # Decorator was not invoked and only target was passed as argument
            return decorator(args[0])
        else:
            # Decorator was invoked
            return lambda target: decorator(target, *args, **kwargs)
    return wrapped_decorator


def log_calls(func):
    """
    Function decorator that prints the call and result of function

    Reference
    - https://stackoverflow.com/a/9112590
    """
    if not callable(func):
        raise TypeError(f"Must be used on a callable object: {func}")

    @functools.wraps(func)
    def wrapped_func(*args, **kwargs):
        func_res = func(*args, **kwargs)

        kwargs_str = tuple(f"{k}={v}" for k, v in kwargs.items())
        param_str = ", ".join(map(str, args + kwargs_str))
        print(f"[Log] <{func.__name__}>({param_str}) = {func_res}")

        return func_res
    return wrapped_func


__all__ = [x for x in globals() if x not in __exclude__ and not x.startswith('_')]
