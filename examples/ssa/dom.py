import queue
from blocks import edges, successors


def compute_dominators(block_map):
    pred, succ = edges(block_map)

    # Initialize dominators to all blocks
    dominators = {name: set({name for name in block_map}) for name in block_map}

    dij = queue.Queue()
    for name in block_map:
        dij.put(name)
    while not dij.empty():
        # intersection of all predecessors
        block_name = dij.get()
        int_set = (
            set()
            if len(pred[block_name]) == 0
            else set.intersection(
                # Union the predecessor as part of the transition from in -> out
                *[dominators[p].union(frozenset([p])) for p in pred[block_name]]
            )
        )

        if int_set != dominators[block_name]:
            dominators[block_name] = int_set
            for s in succ[block_name]:
                dij.put(s)

    for d in dominators:
        dominators[d].add(d)

    dominating = {name: set() for name in block_map}
    for name, doms in dominators.items():
        for dom in doms:
            dominating[dom].add(name)

    return dominators, dominating


def compute_dominator_tree(dominators):
    dominator_tree = {}
    for name, doms in dominators.items():
        dom_parent = None
        for dom_1 in doms:
            if dom_1 == name:
                continue
            is_parent = True
            for dom_2 in doms:
                if dom_2 == name:
                    continue
                if dom_1 != dom_2 and dom_1 in dominators[dom_2]:
                    is_parent = False
                    break

            if is_parent:
                dom_parent = dom_1
                break

        if dom_parent is not None:
            if dom_parent not in dominator_tree:
                dominator_tree[dom_parent] = []
            if name != dom_parent:
                dominator_tree[dom_parent].append(name)

    return dominator_tree


def compute_dominance_frontier(dominating, block_map):
    dominance_frontier = {name: set() for name in block_map}
    _pred, succ = edges(block_map)
    for node, children in dominating.items():
        potential_frontier = set()
        for c in children:
            for s in succ[c]:
                potential_frontier.add(s)

        for p in potential_frontier:
            if node not in dominating[p]:
                dominance_frontier[node].add(p)

    return dominance_frontier
