"""
Module docstring
"""

from subprocess import run as shell

from . import helper

__exclude__ = list(globals())


def exec_shell(cmd):
    return shell(cmd, capture_output=True, shell=True).stdout.decode().strip()


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
