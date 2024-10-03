
I coded up a generalized framework for running dataflow analysis on Bril programs. I pass in the transition function as a callback function, along with whether or not the analysis is may or must and forward or backward as boolean flags. I implemented this by first running a DFS to get the topological ordering of the blocks. With this, I then process the nodes in the relevant order, and I merge the dictionaries of data together according to the flags. There is a decent amount of repeated logic in these merges across different branches, which I think can be simplified. 

In writing constant propagation's transition function, I chose to create a dictionary of foldable operations, and I looped through the instructions individually with their arguments, attempting to aggregate each one. Then, I add this to the map. This doesn't cache the var/val values of the arguments like what was done in local value numbering, but it is simpler for me to understand.

Our transition function for constant propagation in pseudocode looks like: 
```python

def transition_fn(node, data):
  new_data = data.copy()

  for instr in node:
      if "dest" in instr:
          if "args" in instr:
              data[instr["dest"]] = fold_constant(
                  Value(instr["op"], instr["args"])
              )
          elif instr["op"] == "const":
              data[instr["dest"]] = instr["value"]

  return new_data
```

