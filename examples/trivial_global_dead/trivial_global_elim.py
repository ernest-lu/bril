import json
import sys
from functools import reduce
from collections import OrderedDict
import itertools

from collections import namedtuple

# Instructions that terminate a basic block.
TERMINATORS = "br", "jmp", "ret"


Value = namedtuple("Value", ["op", "args"])

FOLDABLE_OPS = {
    "add": lambda a, b: a + b,
    "mul": lambda a, b: a * b,
    "sub": lambda a, b: a - b,
    "div": lambda a, b: a // b,
    "gt": lambda a, b: a > b,
    "lt": lambda a, b: a < b,
    "ge": lambda a, b: a >= b,
    "le": lambda a, b: a <= b,
    "ne": lambda a, b: a != b,
    "eq": lambda a, b: a == b,
    "or": lambda a, b: a or b,
    "and": lambda a, b: a and b,
    "not": lambda a: not a,
}


def _fold(num2const, value):
    if value.op in FOLDABLE_OPS:
        try:
            const_args = [num2const[n] for n in value.args]
            return FOLDABLE_OPS[value.op](*const_args)
        except KeyError:  # At least one argument is not a constant.
            if value.op in {"eq", "ne", "le", "ge"} and value.args[0] == value.args[1]:
                # Equivalent arguments may be evaluated for equality.
                # E.g. `eq x x`, where `x` is not a constant evaluates
                # to `true`.
                return value.op != "ne"

            if value.op in {"and", "or"} and any(v in num2const for v in value.args):
                # Short circuiting the logical operators `and` and `or`
                # for two cases: (1) `and x c0` -> false, where `c0` a
                # constant that evaluates to `false`. (2) `or x c1`  ->
                # true, where `c1` a constant that evaluates to `true`.
                const_val = num2const[
                    value.args[0] if value.args[0] in num2const else value.args[1]
                ]
                if (value.op == "and" and not const_val) or (
                    value.op == "or" and const_val
                ):
                    return const_val
            return None
        except ZeroDivisionError:  # If we hit a dynamic error, bail!
            return None
    else:
        return None


def fresh(seed, names):
    """Generate a new name that is not in `names` starting with `seed`."""
    i = 1
    while True:
        name = seed + str(i)
        if name not in names:
            return name
        i += 1


def flatten(ll):
    """Flatten an iterable of iterable to a single list."""
    return list(itertools.chain(*ll))


def form_blocks(instrs):
    """Given a list of Bril instructions, generate a sequence of
    instruction lists representing the basic blocks in the program.

    Every instruction in `instr` will show up in exactly one block. Jump
    and branch instructions may only appear at the end of a block, and
    control can transfer only to the top of a basic block---so labels
    can only appear at the *start* of a basic block. Basic blocks may
    not be empty.
    """

    # Start with an empty block.
    cur_block = []

    for instr in instrs:
        if "op" in instr:  # It's an instruction.
            # Add the instruction to the currently-being-formed block.
            cur_block.append(instr)

            # If this is a terminator (branching instruction), it's the
            # last instruction in the block. Finish this block and
            # start a new one.
            if instr["op"] in TERMINATORS:
                yield cur_block
                cur_block = []

        else:  # It's a label.
            # End the block here (if it contains anything).
            if cur_block:
                yield cur_block

            # Start a new block with the label.
            cur_block = [instr]

    # Produce the final block, if any.
    if cur_block:
        yield cur_block


def block_map(blocks):
    """Given a sequence of basic blocks, which are lists of instructions,
    produce a `OrderedDict` mapping names to blocks.

    The name of the block comes from the label it starts with, if any.
    Anonymous blocks, which don't start with a label, get an
    automatically generated name. Blocks in the mapping have their
    labels removed.
    """
    by_name = OrderedDict()

    for block in blocks:
        # Generate a name for the block.
        if "label" in block[0]:
            # The block has a label. Remove the label but use it for the
            # block's name.
            name = block[0]["label"]
            block = block[1:]
        else:
            # Make up a new name for this anonymous block.
            name = fresh("b", by_name)

        # Add the block to the mapping.
        by_name[name] = block

    return by_name


def successors(instr):
    """Get the list of jump target labels for an instruction.

    Raises a ValueError if the instruction is not a terminator (jump,
    branch, or return).
    """
    if instr["op"] in ("jmp", "br"):
        return instr["labels"]
    elif instr["op"] == "ret":
        return []  # No successors to an exit block.
    else:
        raise ValueError("{} is not a terminator".format(instr["op"]))


def add_terminators(blocks):
    """Given an ordered block map, modify the blocks to add terminators
    to all blocks (avoiding "fall-through" control flow transfers).
    """
    for i, block in enumerate(blocks.values()):
        if not block:
            if i == len(blocks) - 1:
                # In the last block, return.
                block.append({"op": "ret", "args": []})
            else:
                dest = list(blocks.keys())[i + 1]
                block.append({"op": "jmp", "labels": [dest]})
        elif block[-1]["op"] not in TERMINATORS:
            if i == len(blocks) - 1:
                block.append({"op": "ret", "args": []})
            else:
                # Otherwise, jump to the next block.
                dest = list(blocks.keys())[i + 1]
                block.append({"op": "jmp", "labels": [dest]})


def add_entry(blocks):
    """Ensure that a CFG has a unique entry block with no predecessors.

    If the first block already has no in-edges, do nothing. Otherwise,
    add a new block before it that has no in-edges but transfers control
    to the old first block.
    """
    first_lbl = next(iter(blocks.keys()))

    # Check for any references to the label.
    for instr in flatten(blocks.values()):
        if "labels" in instr and first_lbl in instr["labels"]:
            break
    else:
        return

    # References exist; insert a new block.
    new_lbl = fresh("entry", blocks)
    blocks[new_lbl] = []
    blocks.move_to_end(new_lbl, last=False)


def edges(blocks):
    """Given a block map containing blocks complete with terminators,
    generate two mappings: predecessors and successors. Both map block
    names to lists of block names.
    """
    preds = {name: [] for name in blocks}
    succs = {name: [] for name in blocks}
    for name, block in blocks.items():
        for succ in successors(block[-1]):
            succs[name].append(succ)
            preds[succ].append(name)
    return preds, succs


def perform_analysis(
    fn,
    transition_fn,
    must_analysis: bool = False,
    forward: bool = False,
    init_val: dict = dict(),
):
    succ = dict()
    pred = dict()

    blocks = form_blocks(fn["instrs"])
    bm = block_map(blocks)
    add_terminators(bm)
    pred, succ = edges(bm)

    visited_nodes = set()
    process_order = []

    def dfs(node):
        visited_nodes.add(node)
        for u in succ[node]:
            if u not in visited_nodes:
                dfs(u)
        process_order.append(node)

    for u in succ:
        if u not in visited_nodes:
            dfs(u)

    if forward:
        # Process nodes in topological order
        process_order.reverse()

    data_in = dict()
    data_out = dict()
    for node in process_order:
        data_in[node] = init_val
        data_out[node] = init_val

    def join_dicts(data_list: list[dict]):
        if len(data_list) == 0:
            return dict()
        elif len(data_list) == 1:
            return data_list[0].copy()

        if must_analysis:
            # intersection of dictionaries in the list
            intersection = reduce(
                lambda acc, d: acc & set(d.items()),
                data_list[1:],
                set(data_list[0].items()),
            )
            return dict(intersection)
        else:
            union = reduce(
                lambda acc, d: acc | set(d.items()),
                data_list[1:],
                set(data_list[0].items()),
            )
            return dict(union)

    for node in process_order:
        if forward:
            data_in[node] = join_dicts(
                [data_out[pred_node] for pred_node in pred[node]]
            )
            data_out[node] = transition_fn(bm[node], data_in[node])
        else:
            data_out[node] = join_dicts(
                [data_in[succ_node] for succ_node in succ[node]]
            )
            data_in[node] = transition_fn(bm[node], data_out[node])

    return data_in, data_out


if __name__ == "__main__":
    prog = json.load(sys.stdin)

    def transition_fn(node, data):
        new_data = data.copy()

        def fold_constant(value):
            if value.op in FOLDABLE_OPS:
                try:
                    const_args = [new_data[n] for n in value.args]
                    return FOLDABLE_OPS[value.op](*const_args)
                except KeyError:  # At least one argument is not a constant.
                    if (
                        value.op in {"eq", "ne", "le", "ge"}
                        and value.args[0] == value.args[1]
                    ):
                        # Equivalent arguments may be evaluated for equality.
                        # E.g. `eq x x`, where `x` is not a constant evaluates
                        # to `true`.
                        return value.op != "ne"

                    if value.op in {"and", "or"} and any(
                        v in new_data for v in value.args
                    ):
                        # Short circuiting the logical operators `and` and `or`
                        # for two cases: (1) `and x c0` -> false, where `c0` a
                        # constant that evaluates to `false`. (2) `or x c1`  ->
                        # true, where `c1` a constant that evaluates to `true`.
                        const_val = data[
                            (
                                value.args[0]
                                if value.args[0] in new_data
                                else value.args[1]
                            )
                        ]
                        if (value.op == "and" and not const_val) or (
                            value.op == "or" and const_val
                        ):
                            return const_val
                    return None
                except ZeroDivisionError:  # If we hit a dynamic error, bail!
                    return None
            else:
                return None

        for instr in node:
            if "dest" in instr:
                if "args" in instr:
                    ret = fold_constant(Value(instr["op"], instr["args"]))
                    if ret != None:
                        new_data[instr["dest"]] = ret
                        instr.update({"op": "const", "value": ret})
                elif instr["op"] == "const":
                    new_data[instr["dest"]] = instr["value"]

        return new_data

    def transition_fn_constant(node, data):
        new_data = data.copy()

        def fold_constant(value):
            if value.op in FOLDABLE_OPS:
                try:
                    const_args = [new_data[n] for n in value.args]
                    return FOLDABLE_OPS[value.op](*const_args)
                except KeyError:  # At least one argument is not a constant.
                    if (
                        value.op in {"eq", "ne", "le", "ge"}
                        and value.args[0] == value.args[1]
                    ):
                        # Equivalent arguments may be evaluated for equality.
                        # E.g. `eq x x`, where `x` is not a constant evaluates
                        # to `true`.
                        return value.op != "ne"

                    if value.op in {"and", "or"} and any(
                        v in new_data for v in value.args
                    ):
                        # Short circuiting the logical operators `and` and `or`
                        # for two cases: (1) `and x c0` -> false, where `c0` a
                        # constant that evaluates to `false`. (2) `or x c1`  ->
                        # true, where `c1` a constant that evaluates to `true`.
                        const_val = data[
                            (
                                value.args[0]
                                if value.args[0] in new_data
                                else value.args[1]
                            )
                        ]
                        if (value.op == "and" and not const_val) or (
                            value.op == "or" and const_val
                        ):
                            return const_val
                    return None
                except ZeroDivisionError:  # If we hit a dynamic error, bail!
                    return None
            else:
                return None

        for instr in node:
            if "dest" in instr:
                if "args" in instr:
                    ret = fold_constant(Value(instr["op"], instr["args"]))
                    if ret != None:
                        new_data[instr["dest"]] = ret
                        instr.update({"op": "const", "value": ret})
                elif instr["op"] == "const":
                    new_data[instr["dest"]] = instr["value"]

        return new_data

    for fn in prog["functions"]:
        data_in, _data_out = perform_analysis(
            fn, transition_fn=transition_fn, forward=True, must_analysis=True
        )

    # data_in, data_out = perform_analysis(prog, None)

    json.dump(prog, sys.stdout, indent=2)
