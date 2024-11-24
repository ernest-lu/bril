import queue
from blocks import (
    edges,
    successors,
    form_blocks,
    block_map,
    add_terminators,
    add_entry,
    reassemble,
)
import json, sys


def get_block_map(fn_instrs):
    blocks = form_blocks(fn_instrs)
    blocks_map = block_map(blocks)
    add_terminators(blocks_map)
    add_entry(blocks_map)
    return blocks_map


if __name__ == "__main__":
    prog = json.load(sys.stdin)
    for fn in prog["functions"]:
        bm = get_block_map(fn["instrs"])
        fn["instrs"] = reassemble(bm)

    json.dump(prog, sys.stdout, indent=2)
