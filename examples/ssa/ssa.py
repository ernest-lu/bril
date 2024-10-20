import json
import sys

from dom import compute_dominators, compute_dominance_frontier, compute_dominator_tree
from blocks import (
    form_blocks,
    block_map,
    add_terminators,
    add_entry,
    reassemble,
    edges,
    fresh,
)

import logging

UNDEFINED = "__undefined"

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="ssa.log",  # Log to this file
    filemode="w",  # "w" for overwrite, "a" for append
)


def process_block(block_instrs):
    instr_ret = []
    unused_defs = {}

    num_instrs = len(block_instrs)
    use_instr = [True] * num_instrs

    instr_id = 0
    for instr in block_instrs:
        if "args" in instr:
            for arg in instr["args"]:
                if arg in unused_defs:
                    unused_defs.pop(arg)

        if "dest" in instr:
            var_name = instr["dest"]
            if var_name in unused_defs:
                use_instr[unused_defs[var_name]] = False
            unused_defs[var_name] = instr_id

        instr_id += 1

    instr_id = 0
    for instr in block_instrs:
        if use_instr[instr_id]:
            instr_ret.append(instr)
        instr_id += 1

    return instr_ret


def ssa_add_phi(fn_instrs):
    blocks = form_blocks(fn_instrs)
    blocks_map = block_map(blocks)

    add_terminators(blocks_map)
    add_entry(blocks_map)

    dominators, dominating = compute_dominators(blocks_map)
    dominator_tree = compute_dominator_tree(dominators)
    dominance_frontier = compute_dominance_frontier(dominating, blocks_map)
    preds, succs = edges(blocks_map)

    variable_blocks = {}
    for block_name, block_instrs in blocks_map.items():
        for instr in process_block(block_instrs):
            if "dest" in instr:
                var = instr["dest"]
                if var not in variable_blocks:
                    variable_blocks[var] = set()
                variable_blocks[var].add(block_name)

    for var, blocks in variable_blocks.items():
        preexisting_defs = [b for b in blocks]
        for block_name in preexisting_defs:
            for df_block in dominance_frontier[block_name]:
                blocks_map[df_block] = [
                    {
                        "op": "phi",
                        "dest": var,
                        "args": [var for _ in preds[df_block]],
                        "labels": list(preds[df_block]),
                    }
                ] + blocks_map[df_block]
                variable_blocks[var].add(df_block)

    return reassemble(blocks_map)


def ssa_rename(fn_instrs):
    blocks = form_blocks(fn_instrs)
    blocks_map = block_map(blocks)

    dominators, dominating = compute_dominators(blocks_map)
    dominator_tree = compute_dominator_tree(dominators)
    dominance_frontier = compute_dominance_frontier(dominating, blocks_map)
    logging.debug(dominator_tree)
    preds, succs = edges(blocks_map)
    # renaming variables phase
    variable_stack = {}
    used_variable_names = set()

    logging.debug(dominator_tree)

    def rename_dfs(block_name):
        def rename_arg(arg, instr):
            if arg not in variable_stack:
                return arg
            return variable_stack[arg][-1]

        added_to_stack = []
        for instr in blocks_map[block_name]:
            if "args" in instr and instr["op"] != "phi":
                for i in range(len(instr["args"])):
                    instr["args"][i] = rename_arg(instr["args"][i], instr)

            if "dest" in instr:
                if instr["dest"] not in variable_stack:
                    variable_stack[instr["dest"]] = []
                fresh_name = fresh(instr["dest"], used_variable_names)
                used_variable_names.add(fresh_name)
                variable_stack[instr["dest"]].append(fresh_name)
                added_to_stack.append(instr["dest"])
                instr["new_dest"] = fresh_name

        for succ in succs[block_name]:
            for instr in blocks_map[succ]:
                if "op" in instr and instr["op"] == "phi":
                    v = instr["dest"]
                    assert len(instr["args"]) == len(instr["labels"])
                    for i in range(len(instr["args"])):
                        if instr["labels"][i] == block_name:
                            instr["args"][i] = rename_arg(v, instr)

        if block_name in dominator_tree:
            for succ in dominator_tree[block_name]:
                rename_dfs(succ)

        for dest in added_to_stack:
            variable_stack[dest].pop()
            if len(variable_stack[dest]) == 0:
                variable_stack.pop(dest)

    root = None
    for block_name in blocks_map:
        if len(preds[block_name]) == 0:
            root = block_name
            break
    assert root is not None
    rename_dfs(root)

    for block_name, block_instrs in blocks_map.items():
        instr_list = []
        for instr in block_instrs:
            instr_list.append(instr)
            if "new_dest" in instr and "dest" in instr:
                instr["dest"] = instr["new_dest"]
                instr.pop("new_dest")
        blocks_map[block_name] = instr_list

    return reassemble(blocks_map)


def remove_phi_instrs(fn_instr):
    blocks_map = block_map(form_blocks(fn_instr))
    preds, succs = edges(blocks_map)

    def add_copy_instr_to_end(instr, block_name):
        blocks_map[block_name] = (
            blocks_map[block_name][:-1] + [instr] + [blocks_map[block_name][-1]]
        )

    for block_name, block_instrs in blocks_map.items():
        for instr in block_instrs:
            if "op" in instr and instr["op"] == "phi":
                num_labels = len(instr["labels"])
                var_name = instr["dest"]
                assert len(instr["args"]) == num_labels
                for i in range(num_labels):
                    label = instr["labels"][i]
                    arg = instr["args"][i]
                    if arg != UNDEFINED:
                        add_copy_instr_to_end(
                            {"dest": var_name, "op": "id", "args": [arg]},
                            label,
                        )

    for block_name, block_instrs in blocks_map.items():
        new_block = []
        for instr in block_instrs:
            if "op" in instr and instr["op"] == "phi":
                continue
            new_block.append(instr)
        blocks_map[block_name] = new_block

    return reassemble(blocks_map)


if __name__ == "__main__":
    prog = json.load(sys.stdin)
    for fn in prog["functions"]:
        fn["instrs"] = ssa_add_phi(fn["instrs"])
        # json.dump(prog, sys.stdout, indent=2)
        fn["instrs"] = ssa_rename(fn["instrs"])
        # json.dump(prog, sys.stdout, indent=2)
        fn["instrs"] = remove_phi_instrs(fn["instrs"])
    json.dump(prog, sys.stdout, indent=2)
