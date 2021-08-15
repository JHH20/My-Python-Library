"""
Module docstring
"""

from subprocess import run
from pathlib import Path
from pty import openpty
import os
import shlex

from . import helper

__exclude__ = list(globals())


def exec_shell(cmd):
    """
    Deprecated function to run shell commands

    Uses subprocess module's internal PIPE to capture outputs
    - Captured outputs may be out of order compared to executing in a tty
    """
    print("[Deprecated] ctftools: Switch from exec_shell() to exec()")
    return run(cmd, capture_output=True, shell=True).stdout.decode().strip()


def exec(cmd, *, binput=None):
    """
    Execute `cmd` in a shell using a pseudo tty
    Returns result as (console output, return code)

    - If supplied, binput is byte data passed to the stdin

    Reference
    - https://bugs.python.org/issue5380
    """
    if binput is not None and not isinstance(binput, (bytes, bytearray)):
        raise TypeError("Argument must be a byte-like object: {binput}")

    # Parse file descriptor redirection
    parsed_cmd = shlex.split(cmd)
    redirects = []
    for i, token in enumerate(parsed_cmd):
        if '<' in token and not token.startswith('<'):
            try:
                # Extract desired fd
                fd_r = int(token.split('<')[0])

                # Will not attempt to open using STD I/O file descriptors
                if fd_r < 3:
                    raise ValueError

                # Open file
                file = open(parsed_cmd[i + 1])

                # Change fd to desired value
                if fd_r != file.fileno():
                    os.dup2(file.fileno(), fd_r)
                    file.close()

                # Add fd to list
                redirects.append(fd_r)
            except ValueError:
                err_msg = "Will not explicitly redirect file to STD I/O"
                raise ValueError(err_msg) from None
            except Exception as err:
                err_msg = "Failed to handle file descriptor redirection"
                err_tokens = (token, parsed_cmd[i + 1])
                raise ValueError(f"{err_msg}: {err_tokens}") from err

    # Execute in a pseudo tty
    fd_p, fd_c = openpty()
    res = run(cmd, input=binput, shell=True, stdout=fd_c, stderr=fd_c, pass_fds=redirects)
    os.close(fd_c)

    # Close redirected file descriptors
    for fd_r in redirects:
        os.close(fd_r)

    # Collect shell output
    output = b''
    try:
        last_read = None
        while last_read is None or len(last_read) > 0:
            last_read = os.read(fd_p, 1024)
            output += last_read
    except OSError as err:
        # Reading from pty may throw OSError: [Errno 5] Input/output error
        # on excess reading instead of returning empty string after closing
        # its pair on some platforms (see reference link for more info)
        if err.strerror != "Input/output error":
            raise err from None
    finally:
        os.close(fd_p)

    return output.decode().strip(), res.returncode


def pwn_college():
    """
    Get path of pwn.college CTF executable file
    by finding first executable file in root that does not start with '.'
    """
    for file in Path('/').iterdir():
        if file.is_file() and not file.name.startswith('.') \
            and os.access(file, os.X_OK):
            return str(file)


def parse_objdump_line(line):
    # line format = <inst pos>:\t<jmp arrow> <machine code> \t<assembly> <comments>

    # Ensure param is an assembly line
    if ":\t" not in line:
        raise ValueError(f"Not an instruction line: {line}")

    line = line.strip()
    inst_pos = line[0:line.find(':')]

    # For skipping jump visuals if no machine code
    end_arrow = "\x1b[0m"
    after_arrow = line.rfind(end_arrow) + len(end_arrow)
    inst_start = max(line.rfind('\t'), after_arrow)

    inst_end = len(line)
    if '#' in line:
        inst_end = line.find('#', inst_start)
    if '<' in line:
        inst_end = min(inst_end, line.find('<', inst_start))

    inst = line[inst_start:inst_end].strip().split(maxsplit=1)
    params = inst[1].split(',') if len(inst) == 2 else []

    # For extracting machine code if exists
    machine_code = line[max(line.find('\t'), after_arrow):inst_start].strip() \
        if line.find('\t') < line.rfind('\t') else "<no OP code>"

    return [inst_pos, machine_code, inst[0]] + params


def get_objdump(exec_path):
    """
    Get and parse objdump of `exec_path` .text section in intel assembly

    Returns tuple(\n-separated raw dump, parsed )
    """
    dump = exec_shell(f"objdump -z -M intel -d -j .text {exec_path}")
    dump = helper.split(dump, '\n')
    parsed_asm = [parse_objdump_line(x) for x in dump if ":\t" in x]
    return (dump, parsed_asm)


__all__ = [x for x in globals() if x not in __exclude__ and not x.startswith('_')]
