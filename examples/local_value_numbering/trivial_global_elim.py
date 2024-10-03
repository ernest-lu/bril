import json
import sys


def process_block(instr_block):
    used = set()
    ret_block = []
    for instr in instr_block:
        if "args" in instr:
            for arg in instr["args"]:
                used.add(arg)

    for instr in instr_block:
        if "dest" in instr and instr["dest"] not in used:
            continue

        ret_block.append(instr)

    return ret_block


if __name__ == "__main__":
    prog = json.load(sys.stdin)
    for fn in prog["functions"]:
        fn["instrs"] = process_block(fn["instrs"])
    json.dump(prog, sys.stdout, indent=2)
