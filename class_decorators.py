"""
This module defines decorators to be used on classes.
The decorator will crawl through its attributes to wrap methods.
"""

import functools
import copy
import inspect

from .submodules import helper
from .function_decorators import decorator_varargs

__exclude__ = list(globals())


def _get_methods(cls):
    # Equivalent to (dir filtered by callable) - '__class__'
    return [x[0] for x in inspect.getmembers(cls, predicate=inspect.isroutine)]


def _is_instance_method(cls, func_name):
    """
    If __self__ is None: @staticmethod
    If __self__ is class: @classmethod
    If __self__ is instance: instance method
    """
    dummy = cls()
    func = getattr(dummy, func_name) if hasattr(dummy, func_name) else None

    return hasattr(func, '__self__') and func.__self__ is dummy

def _is_inherited(cls, attr):
    """
    Reference
    - https://stackoverflow.com/a/30391309
    """
    if hasattr(cls, attr) and hasattr(super(cls, cls), attr):
        parent_attr = getattr(super(cls, cls), attr)
        child_attr = getattr(cls, attr)
        # Check after stripping any decoration in the child class
        # to allow for nested decoration
        return inspect.unwrap(child_attr) == parent_attr
    else:
        return False


_object_methods = tuple(_get_methods(object))

default_ignores = ('__delitem__', '__getitem__', '__setitem__',
                    '__del__', '__new__', '__init__'
                    '__len__', '__alloc__', '__contains__',
                    '__repr__', '__str__', '__iter__')


@decorator_varargs
def inherit_methods(cls, *, ignore=default_ignores, ignore_obj=True):
    """
    Class decorator that re-defines instance methods inherited from
    parent class so that it returns the instance of the child class
    by wrapping with a down-casting attempt if applicable

    Optional decorator arguments (keyword only)
    - ignore: tuple or list containing function names as string
        * These functions will not be wrapped and therefore ignored
        * @staticmethod and @classmethod are always ignored
        * Default = default_ignore_methods
    - ignore_obj: boolean
        * If true, also ignore all callable properties of class `object`
        * Default = True

    Reference
    - https://stackoverflow.com/a/53135377
    - https://stackoverflow.com/a/9112590
    """
    if not inspect.isclass(cls):
        raise TypeError(f"Must be used on a class, not: {type(cls)}")
    if not helper.seq_holdstype(ignore, str):
        raise TypeError(f"Argument must be a sequence of str: {ignore}")

    def apply_wrapper(cls, func_name):
        super_method = getattr(super(cls, cls), func_name)

        def issuperclass(obj, cls):
            return issubclass(cls, type(obj))

        @functools.wraps(super_method)
        def wrapped_func(self, *args, **kwargs):
            result = super_method(self, *args, **kwargs)
            # Convert to child class if applicable, otherwise return as is
            if issuperclass(result, cls):
                # Result is instance of parent class
                return cls(result)
            elif helper.seq_holdstype(result):
                gen = (cls(x) if issuperclass(x, cls) else x for x in result)
                return type(result) (gen)
            else:
                # Default
                return result

        # Update __qualname__ to reflect current class name
        wrapped_func.__qualname__ = f"{cls.__name__}.{func_name}"

        setattr(cls, func_name, wrapped_func)

    # Exclude `object` class methods if specified
    if ignore_obj:
        ignore = _object_methods + tuple(ignore)

    # Wrap inherited instance methods with appropriate down-casting
    for func_name in [x for x in _get_methods(cls) if _is_inherited(cls, x)]:
        if func_name not in ignore and _is_instance_method(cls, func_name):
            apply_wrapper(cls, func_name)

    return cls


@decorator_varargs
def immutify_methods(cls, methods):
    """
    Class decorator that re-defines instance methods to execute on a
    new deepcopy and return the copy object

    Will emit warning if method produces a return value

    Decorator argument
    - methods: sequence containing function names as string
        * sequence type = list, tuple, set, frozenset
        * These functions are candidate for wrapping
        * @staticmethod and @classmethod are always ignored
    """
    if not inspect.isclass(cls):
        raise TypeError(f"Must be used on a class, not: {type(cls)}")
    if not helper.seq_holdstype(methods, str):
        raise TypeError(f"Argument must be a sequence of str: {methods}")

    def apply_wrapper(cls, func_name):
        func = getattr(cls, func_name)

        @functools.wraps(func)
        def wrapped_func(self, *args, **kwargs):
            copy_obj = copy.deepcopy(self)
            res = func(copy_obj, *args, **kwargs)
            if res is not None:
                # Replace this with warning
                # https://docs.python.org/3.8/library/exceptions.html#warnings
                raise RuntimeError(f"Immutified method returned a value: {res}")
            return copy_obj

        setattr(cls, func_name, wrapped_func)

    for func_name in methods:
        if _is_instance_method(cls, func_name):
            apply_wrapper(cls, func_name)

    return cls


__all__ = [x for x in globals() if x not in __exclude__ and not x.startswith('_')]
