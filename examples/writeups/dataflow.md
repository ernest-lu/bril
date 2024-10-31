
I coded up a generalized framework for running dataflow analysis on Bril programs. I pass in the transition function as a callback function, along with whether or not the analysis is may or must and forward or backward as boolean flags. I implemented this by first running a DFS to get the topological ordering of the blocks. With this, I then process the nodes in the relevant order, and I merge the dictionaries of data together according to the flags. There is a decent amount of repeated logic in these merges across different branches, which I think can be simplified. 

In writing constant propagation's transition function, I chose to create a dictionary of foldable operations, and I looped through the instructions individually with their arguments, attempting to aggregate each one. Then, I add this to the map. This doesn't cache the var/val values of the arguments like what was done in local value numbering, but it is simpler for me to understand.

code for general analysis:
```python
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
```

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

As a quick sanity check, our constant propogation outputs


```
@main {
  a: int = const 0;
  b: int = const 1;
  c: int = const 1;
}
```

for
```
@main() {
    a: int = const 0;
    b: int = const 1;
    c: int = add a b;
}
```

Constant propogation did not elimnate any instruction counts. But we do see optimizations in the instructinos being outputted.

We followed a similar pattern for liveness analysis, with transition pseudocode looking like:


Liveness analysis got rid of some code segments, resulting in the following output: (I couldn't find a plotting tool in this repo):

```
benchmark,run,result
quadratic,baseline,785
quadratic,trivial_global_elim,785
primes-between,baseline,574100
primes-between,trivial_global_elim,574100
birthday,baseline,484
birthday,trivial_global_elim,484
orders,baseline,5352
orders,trivial_global_elim,5352
sum-check,baseline,5018
sum-check,trivial_global_elim,5018
palindrome,baseline,298
palindrome,trivial_global_elim,298
totient,baseline,253
totient,trivial_global_elim,253
relative-primes,baseline,1923
relative-primes,trivial_global_elim,1923
hanoi,baseline,99
hanoi,trivial_global_elim,99
is-decreasing,baseline,127
is-decreasing,trivial_global_elim,127
check-primes,baseline,8468
check-primes,trivial_global_elim,8468
sum-sq-diff,baseline,3038
sum-sq-diff,trivial_global_elim,3038
fitsinside,baseline,10
fitsinside,trivial_global_elim,10
fact,baseline,229
fact,trivial_global_elim,229
loopfact,baseline,116
loopfact,trivial_global_elim,116
recfact,baseline,104
recfact,trivial_global_elim,104
factors,baseline,72
factors,trivial_global_elim,72
perfect,baseline,232
perfect,trivial_global_elim,232
bitshift,baseline,167
bitshift,trivial_global_elim,167
digital-root,baseline,247
digital-root,trivial_global_elim,247
up-arrow,baseline,252
up-arrow,trivial_global_elim,252
sum-divisors,baseline,159
sum-divisors,trivial_global_elim,159
ackermann,baseline,1464231
ackermann,trivial_global_elim,1464231
pythagorean_triple,baseline,61518
pythagorean_triple,trivial_global_elim,61518
euclid,baseline,563
euclid,trivial_global_elim,563
binary-fmt,baseline,100
binary-fmt,trivial_global_elim,100
lcm,baseline,2326
lcm,trivial_global_elim,2326
gcd,baseline,46
gcd,trivial_global_elim,46
catalan,baseline,659378
catalan,trivial_global_elim,659378
armstrong,baseline,133
armstrong,trivial_global_elim,133
pascals-row,baseline,146
pascals-row,trivial_global_elim,146
collatz,baseline,169
collatz,trivial_global_elim,169
sum-bits,baseline,73
sum-bits,trivial_global_elim,73
rectangles-area-difference,baseline,14
rectangles-area-difference,trivial_global_elim,14
mod_inv,baseline,558
mod_inv,trivial_global_elim,558
reverse,baseline,46
reverse,trivial_global_elim,46
fizz-buzz,baseline,3652
fizz-buzz,trivial_global_elim,3652
bitwise-ops,baseline,1690
bitwise-ops,trivial_global_elim,1690
cholesky,baseline,3761
cholesky,trivial_global_elim,3761
mat-inv,baseline,1044
mat-inv,trivial_global_elim,1044
dead-branch,baseline,1196
dead-branch,trivial_global_elim,1196
function_call,baseline,timeout
function_call,trivial_global_elim,timeout
ray-sphere-intersection,baseline,142
ray-sphere-intersection,trivial_global_elim,142
conjugate-gradient,baseline,1999
conjugate-gradient,trivial_global_elim,1999
leibniz,baseline,12499997
leibniz,trivial_global_elim,12499997
n_root,baseline,733
n_root,trivial_global_elim,733
newton,baseline,217
newton,trivial_global_elim,217
euler,baseline,1908
euler,trivial_global_elim,1908
riemann,baseline,298
riemann,trivial_global_elim,298
mandelbrot,baseline,2720947
mandelbrot,trivial_global_elim,2720947
norm,baseline,505
norm,trivial_global_elim,505
cordic,baseline,517
cordic,trivial_global_elim,517
pow,baseline,36
pow,trivial_global_elim,36
sqrt,baseline,322
sqrt,trivial_global_elim,322
quickselect,baseline,279
quickselect,trivial_global_elim,279
sieve,baseline,3482
sieve,trivial_global_elim,3482
bubblesort,baseline,253
bubblesort,trivial_global_elim,253
primitive-root,baseline,11029
primitive-root,trivial_global_elim,11029
adler32,baseline,6851
adler32,trivial_global_elim,6851
adj2csr,baseline,56629
adj2csr,trivial_global_elim,56629
csrmv,baseline,121202
csrmv,trivial_global_elim,121202
dot-product,baseline,88
dot-product,trivial_global_elim,88
major-elm,baseline,47
major-elm,trivial_global_elim,47
max-subarray,baseline,193
max-subarray,trivial_global_elim,193
mat-mul,baseline,1990407
mat-mul,trivial_global_elim,1990407
fib,baseline,121
fib,trivial_global_elim,121
vsmul,baseline,86036
vsmul,trivial_global_elim,86036
quicksort-hoare,baseline,27333
quicksort-hoare,trivial_global_elim,27333
quicksort,baseline,264
quicksort,trivial_global_elim,264
two-sum,baseline,98
two-sum,trivial_global_elim,98
eight-queens,baseline,1006454
eight-queens,trivial_global_elim,1006454
binary-search,baseline,78
binary-search,trivial_global_elim,78
```