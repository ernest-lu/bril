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


# returns a dict of the form {block_name: {var_name: set(points_to)}}
def get_points_to(block_map):
    pred, succ = edges(block_map)

    # Initialize dominators to all blocks
    points_to = {name: dict() for name in block_map}

    def transition_fn(in_set, block_name):
        # x = alloc n: x points to this allocations
        # x = id y: x points to the same locations as y did
        # x = ptradd p offset: same as id (conservative)
        # x = load p: we aren't tracking anything about p, so x points to all memory locations
        # store p x: no change

        # counter to store ids of allocations
        nxt_alloc_id = 0

        out_set = in_set.copy()
        for instr in block_map[block_name]:
            if instr["op"] == "alloc":
                if instr["dest"] not in out_set:
                    out_set[instr["dest"]] = set()
                out_set[instr["dest"]].add(nxt_alloc_id)
                nxt_alloc_id += 1
            elif (
                instr["op"] == "id"
                and isinstance(instr["type"], dict)
                and "ptr" in instr["type"]
            ):
                if instr["dest"] not in out_set:
                    out_set[instr["dest"]] = set()
                out_set[instr["dest"]].update(in_set[instr["src"]])
            elif instr["op"] == "ptradd":
                if instr["dest"] not in out_set:
                    out_set[instr["dest"]] = set()
                out_set[instr["dest"]].update(in_set[instr["src"]])

        return out_set

    dij = queue.Queue()
    for name in block_map:
        dij.put(name)

    def union_dicts(dicts):
        union_dict = dict()
        for d in dicts:
            for k, v in d.items():
                if k not in union_dict:
                    union_dict[k] = set()
                union_dict[k].update(v)
        return union_dict

    while not dij.empty():
        # intersection of all predecessors
        block_name = dij.get()
        union_dict = union_dicts([points_to[p] for p in pred[block_name]])

        union_dict = transition_fn(union_dict, block_name)

        if union_dict != points_to[block_name]:
            points_to[block_name] = union_dict
            for s in succ[block_name]:
                dij.put(s)

    return points_to


def trivial_dead_store(points_to, block_map):
    for block_name, var_map in points_to.items():
        location_to_vars = dict()
        for var, locations in var_map.items():
            for location in locations:
                if location not in location_to_vars:
                    location_to_vars[location] = set()
                location_to_vars[location].add(var)

        new_instrs = []
        is_dead_instr = [False] * len(block_map[block_name])
        unused_vars = dict()

        for instr_id, instr in enumerate(block_map[block_name]):
            if instr["op"] == "store":
                src = instr["args"][0]
                if src in unused_vars:
                    loc = unused_vars[src]
                    is_dead_instr[loc] = True
                else:
                    unused_vars[src] = instr_id
            else:
                # very nested statement to just remove vars that are used in args
                if "args" in instr:
                    for arg in instr["args"]:
                        if arg in var_map:
                            for loc in var_map[arg]:
                                for var in location_to_vars[loc]:
                                    if var in unused_vars:
                                        unused_vars.pop(var)

        for var, loc in unused_vars.items():
            is_dead_instr[loc] = True

        for instr_id, instr in enumerate(block_map[block_name]):
            if not is_dead_instr[instr_id]:
                new_instrs.append(instr)

        block_map[block_name] = new_instrs


def no_ptr_args(fn):
    return "args" not in fn or not any(
        arg["type"] == {"ptr": "int"} for arg in fn["args"]
    )


if __name__ == "__main__":
    prog = json.load(sys.stdin)
    for fn in prog["functions"]:
        bm = get_block_map(fn["instrs"])
        if no_ptr_args(fn):
            # only do memory analysis for functions with no ptr arguments
            # this is conservative because we don't know where arguments can point
            # then we do dead code elimination on things that point to
            points_to = get_points_to(bm)
            # print(points_to)
            trivial_dead_store(points_to, bm)
            fn["instrs"] = reassemble(bm)
        # dominators, dominating = memory_analysis(block_map)
        # print(dominators)
        # print(dominating)

    json.dump(prog, sys.stdout, indent=2)
