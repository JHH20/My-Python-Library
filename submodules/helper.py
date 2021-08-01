"""
This module defines a collection of disparate functions
"""

import re
import inspect

__exclude__ = list(globals())


def seq_holdstype(obj, cls=None):
    """
    Check if `obj` is a list/tuple/set/frozenset that contains `cls` instances
    - If `cls` = None, skip type checking of elements
    """
    if cls is not None and not inspect.isclass(cls):
        raise TypeError(f"`cls` argument must be a class: {cls}")

    return isinstance(obj, (list, tuple, set, frozenset)) \
        and (cls is None or all(isinstance(x, cls) for x in obj))


def unsigned_to_signed(num, bits):
    """
    Convert unsigned number to `bits`-bit signed number in two's complement
    """
    max_val = 1 << bits
    if num < 0 or num >= max_val:
        raise ValueError(f"Unsigned number `{num}` does not fit in {bits} bits")

    if num & (max_val >> 1):
        num -= max_val

    return num


def signed_to_unsigned(num, bits):
    """
    Convert signed number in two's complement to `bits`-bit unsigned number
    """
    max_val = 1 << (bits - 1)
    if num < -max_val or num >= max_val:
        raise ValueError(f"Signed number`{num}` does not fit in {bits} bits")

    if num & max_val:
        num += (max_val << 1)


def wrap_overflow(num, bits, *, signed):
    """
    Wrap around number as `bits` bit integer if overflowed or underflowed
    """
    limit = 1 << bits
    max_val = (limit // 2 - 1) if signed else (limit - 1)
    min_val = -(max_val + 1) if signed else 0

    if num < min_val:
        offset = (min_val - num - 1) % limit
        return max_val - offset

    if num > max_val:
        offset = (num - max_val - 1) % limit
        return min_val + offset

    # min_val <= num <= max_val
    return num


def split(string, delim, *, maxsplit=0):
    """
    Split `string` on any occurrence of `delim`
    If maxsplit == 0, split on every occurrence of `delim` (default)
    """
    if not (isinstance(delim, str) or seq_holdstype(delim, str)):
        raise TypeError(f"Argument must be a sequence of str: {delim}")

    # delim is collection of delimiter characters
    pattern = f"[{re.escape(''.join(delim))}]+"
    return re.split(pattern, string, maxsplit)


def py_strace(count=1, *, warn=False):
    """
    Stacktrace function calls up to `count` frames back
    - Each frame is saved as tuple(function name, arguments, local variables)
    - Stacktrace stores frame info in reverse order of invocation

    - warn: boolean
        * If true, print an alert when terminating early

    ex) f1() -> f2() -> f3() -> f4() -> strace(3) = [f4, f3, f2]
    ex) f1() -> f2() -> strace(4) = [f2, f1] + optional warn
    """
    if count < 0:
        raise ValueError("`count` argument must be non-negative: {count}")

    callers = []
    frame = inspect.currentframe()
    for i in range(count):
        try:
            frame = frame.f_back

            func_name = inspect.getframeinfo(frame).function
            frame_info = inspect.getargvalues(frame)
            args = {k: frame_info.locals[k] for k in frame_info.args}
            locals = {k:v for k,v in frame_info.locals.items() if k not in args}

            callers.append( (func_name, args, locals) )
        except:
            if warn:
                print(f"Early termination after {i} frames")
            break
    return callers


__all__ = [x for x in globals() if x not in __exclude__ and not x.startswith('_')]
