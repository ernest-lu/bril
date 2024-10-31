
I implemented SSA in this assignment. I had some incorrect programs after ssa, and a lot of programs added a lot of instructions. In general, I will use SSA as the new baseline benchmark for programs going forward.

These are the aggregate statistics post SSA implementation:

```
    geomean(baseline) = 1.00
    min(baseline) = 1.00
    max(baseline) = 1.00
    geomean(ssa) = 2.71
    min(ssa) = 1.01
    max(ssa) = 6.22
```

I didn't run any dead code elimnation or liveness analysis on this SSA implementation. A lot of single assignment instructions are being added. 

My LICM implementation follows this logic:
1) Compute dominating relations
2) Loop through blocks to determine whether or not blocks can be hoisted out of
    - A block can be hoisted out of if it dominates all of its exits
3) Hoist items out of this block into the dominating block

Then, we get these statistics:
```
geomean(baseline) = 1.00
min(baseline) = 1.00
max(baseline) = 1.00
geomean(licm) = 2.51
min(licm) = 1.01
max(licm) = 6.22
```

Code for LICM:
``` 
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
```
