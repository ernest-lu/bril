import json
import sys

from ssa import (
    ssa_add_phi,
    ssa_rename,
    remove_phi_instrs
)

from blocks import (
    form_blocks,
    block_map,
    edges,
    reassemble
)

from dom import (
    compute_dominator_tree,
    compute_dominators,
    compute_dominance_frontier
)

import logging

UNDEFINED = "__undefined"

def licm(fn_instrs):
    blocks = form_blocks(fn_instrs)
    blocks_map = block_map(blocks)

    dominators, dominating = compute_dominators(blocks_map)
    dominator_tree = compute_dominator_tree(dominators)
    dominance_frontier = compute_dominance_frontier(dominating, blocks_map)
    preds, succs = edges(blocks_map)


    new_blocks_map = {block_name: [] for block_name in blocks_map}

    for block_name in blocks_map:
        can_hoist_out = True
        for s in succs[block_name]:
            if s not in dominating[block_name]:
                can_hoist_out = False
                break

        if not can_hoist_out:
            new_blocks_map[block_name] = blocks_map[block_name]
        else:
            found_dominator = False
            for dom in dominators[block_name]:
                if dom in succs[block_name]:
                    # this dominator is the header to be hoisted too
                    for instr in blocks_map[block_name]:
                        new_blocks_map[dom].append(instr)

                    found_dominator = True
                    break

            if not found_dominator:
                new_blocks_map[block_name] = blocks_map[block_name]
    
    return reassemble(new_blocks_map)


if __name__ == "__main__":
    prog = json.load(sys.stdin)
    for fn in prog["functions"]:
        fn["instrs"] = ssa_add_phi(fn["instrs"])
        fn["instrs"] = ssa_rename(fn["instrs"])

        fn["instrs"] = licm(fn["instrs"])
        fn["instrs"] = remove_phi_instrs(fn["instrs"])
    json.dump(prog, sys.stdout, indent=2)
