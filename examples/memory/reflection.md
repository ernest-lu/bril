I implemented a simple dead store elimination pass.

First, we conduct points-to analysis to find all the locations that a variable points to. This was done as a standard dataflow analysis with the associated transfer function mentioned in the lesson. We only ran this on functions that had no pointer arguments, as conservatively, these parameters could point to any location. If there a pointers to any location, stores were not removed.

points-to analysis:
```python
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
```

Then, we conduct dead store elimination. We iterate over each block and each instruction in the block. If the instruction is a store, we check if the location it is storing to is dead. If it is, we remove the store. I think this could have been made better, but I did a very nested statement to just remove vars that are used in args.

```python
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
```

This was tested on a simple program that could optimize away dead stores. For example, this dead store:

```
@main() {
    size: int = const 3;
    v1: ptr<int> = alloc size;
    store v1 size;
    store v1 size;
    a_2: int = load v1;
}
```

was optimized to:

```
@main() {
    size: int = const 3;
    v1: ptr<int> = alloc size;
    store v1 size;
    a_2: int = load v1;
}
```

Then, we ran benchmarks to see the performance impact. In general, labels were added so the total instruction count was higher for some programs. Errors occurred in arrays that were allocated by a function call, don't know what points to is pointing to in this case.

These are the summary stats from running normalize.py on the memory benchmarks:

```
benchmark,run,result
quadratic,baseline,1.0
quadratic,memory,1.0585987261146497
primes-between,baseline,1.0
primes-between,memory,1.0037746037275737
birthday,baseline,1.0
birthday,memory,1.0041322314049588
orders,baseline,1.0
sum-check,baseline,1.0
sum-check,memory,1.0003985651654046
palindrome,baseline,1.0
palindrome,memory,1.0302013422818792
totient,baseline,1.0
totient,memory,1.023715415019763
relative-primes,baseline,1.0
relative-primes,memory,1.0884035361414457
hanoi,baseline,1.0
hanoi,memory,1.0808080808080809
is-decreasing,baseline,1.0
is-decreasing,memory,1.015748031496063
check-primes,baseline,1.0
check-primes,memory,1.052905054322154
sum-sq-diff,baseline,1.0
sum-sq-diff,memory,1.0009874917709018
fitsinside,baseline,1.0
fitsinside,memory,1.1
fact,baseline,1.0
fact,memory,1.0043668122270741
loopfact,baseline,1.0
loopfact,memory,1.0172413793103448
recfact,baseline,1.0
recfact,memory,1.0769230769230769
factors,baseline,1.0
factors,memory,1.0277777777777777
perfect,baseline,1.0
perfect,memory,1.0301724137931034
bitshift,baseline,1.0
bitshift,memory,1.0239520958083832
digital-root,baseline,1.0
digital-root,memory,1.0445344129554657
up-arrow,baseline,1.0
up-arrow,memory,1.0555555555555556
sum-divisors,baseline,1.0
sum-divisors,memory,1.0062893081761006
ackermann,baseline,1.0
ackermann,memory,1.0000006829523485
pythagorean_triple,baseline,1.0
pythagorean_triple,memory,1.0020969472349557
euclid,baseline,1.0
euclid,memory,1.0035523978685612
binary-fmt,baseline,1.0
binary-fmt,memory,1.18
lcm,baseline,1.0
lcm,memory,1.000859845227859
gcd,baseline,1.0
gcd,memory,1.0434782608695652
catalan,baseline,1.0
catalan,memory,1.0298523760271043
armstrong,baseline,1.0
armstrong,memory,1.037593984962406
pascals-row,baseline,1.0
pascals-row,memory,1.0205479452054795
collatz,baseline,1.0
collatz,memory,1.029585798816568
sum-bits,baseline,1.0
sum-bits,memory,1.0136986301369864
rectangles-area-difference,baseline,1.0
rectangles-area-difference,memory,1.1428571428571428
mod_inv,baseline,1.0
mod_inv,memory,1.0161290322580645
reverse,baseline,1.0
reverse,memory,1.0434782608695652
fizz-buzz,baseline,1.0
fizz-buzz,memory,1.0407995618838992
bitwise-ops,baseline,1.0
bitwise-ops,memory,1.0029585798816567
cholesky,baseline,1.0
mat-inv,baseline,1.0
mat-inv,memory,1.0009578544061302
dead-branch,baseline,1.0
dead-branch,memory,1.0016722408026757
ray-sphere-intersection,baseline,1.0
ray-sphere-intersection,memory,1.0070422535211268
conjugate-gradient,baseline,1.0
leibniz,baseline,1.0
leibniz,memory,1.0400001696000407
n_root,baseline,1.0
n_root,memory,1.030013642564802
newton,baseline,1.0
newton,memory,1.0092165898617511
euler,baseline,1.0
euler,memory,1.0723270440251573
riemann,baseline,1.0
riemann,memory,1.0134228187919463
mandelbrot,baseline,1.0
mandelbrot,memory,1.0014064956061253
norm,baseline,1.0
norm,memory,1.0435643564356436
cordic,baseline,1.0
cordic,memory,1.0657640232108316
pow,baseline,1.0
pow,memory,1.0833333333333333
sqrt,baseline,1.0
sqrt,memory,1.031055900621118
quickselect,baseline,1.0
quickselect,memory,1.003584229390681
sieve,baseline,1.0
sieve,memory,1.0008615738081563
bubblesort,baseline,1.0
bubblesort,memory,1.0790513833992095
primitive-root,baseline,1.0
primitive-root,memory,1.0434309547556442
adler32,baseline,1.0
adler32,memory,1.0032112100423296
adj2csr,baseline,1.0
adj2csr,memory,1.000035317593459
csrmv,baseline,1.0
csrmv,memory,1.0099090774079635
dot-product,baseline,1.0
dot-product,memory,1.0113636363636365
major-elm,baseline,1.0
max-subarray,baseline,1.0
mat-mul,baseline,1.0
mat-mul,memory,1.0
fib,baseline,1.0
vsmul,baseline,1.0
quicksort-hoare,baseline,1.0
quicksort,baseline,1.0
quicksort,memory,1.003787878787879
two-sum,baseline,1.0
two-sum,memory,1.010204081632653
eight-queens,baseline,1.0
eight-queens,memory,1.000000993587387
binary-search,baseline,1.0
binary-search,memory,1.0128205128205128
geomean(baseline) = 1.00
min(baseline) = 1.00
max(baseline) = 1.00
geomean(memory) = 1.03
min(memory) = 1.00
max(memory) = 1.18
```

This is compared to reassembled benchmarks as our baseline (where we added labels):
```
benchmark,run,result
quadratic,baseline,1.0
quadratic,reassemble,1.0585987261146497
primes-between,baseline,1.0
primes-between,reassemble,1.0037746037275737
birthday,baseline,1.0
birthday,reassemble,1.0041322314049588
orders,baseline,1.0
orders,reassemble,1.0179372197309418
sum-check,baseline,1.0
sum-check,reassemble,1.0003985651654046
palindrome,baseline,1.0
palindrome,reassemble,1.0302013422818792
totient,baseline,1.0
totient,reassemble,1.023715415019763
relative-primes,baseline,1.0
relative-primes,reassemble,1.0884035361414457
hanoi,baseline,1.0
hanoi,reassemble,1.0808080808080809
is-decreasing,baseline,1.0
is-decreasing,reassemble,1.015748031496063
check-primes,baseline,1.0
check-primes,reassemble,1.052905054322154
sum-sq-diff,baseline,1.0
sum-sq-diff,reassemble,1.0009874917709018
fitsinside,baseline,1.0
fitsinside,reassemble,1.1
fact,baseline,1.0
fact,reassemble,1.0043668122270741
loopfact,baseline,1.0
loopfact,reassemble,1.0172413793103448
recfact,baseline,1.0
recfact,reassemble,1.0769230769230769
factors,baseline,1.0
factors,reassemble,1.0277777777777777
perfect,baseline,1.0
perfect,reassemble,1.0301724137931034
bitshift,baseline,1.0
bitshift,reassemble,1.0239520958083832
digital-root,baseline,1.0
digital-root,reassemble,1.0445344129554657
up-arrow,baseline,1.0
up-arrow,reassemble,1.0555555555555556
sum-divisors,baseline,1.0
sum-divisors,reassemble,1.0062893081761006
ackermann,baseline,1.0
ackermann,reassemble,1.0000006829523485
pythagorean_triple,baseline,1.0
pythagorean_triple,reassemble,1.0020969472349557
euclid,baseline,1.0
euclid,reassemble,1.0035523978685612
binary-fmt,baseline,1.0
binary-fmt,reassemble,1.18
lcm,baseline,1.0
lcm,reassemble,1.000859845227859
gcd,baseline,1.0
gcd,reassemble,1.0434782608695652
catalan,baseline,1.0
catalan,reassemble,1.0298523760271043
armstrong,baseline,1.0
armstrong,reassemble,1.037593984962406
pascals-row,baseline,1.0
pascals-row,reassemble,1.0205479452054795
collatz,baseline,1.0
collatz,reassemble,1.029585798816568
sum-bits,baseline,1.0
sum-bits,reassemble,1.0136986301369864
rectangles-area-difference,baseline,1.0
rectangles-area-difference,reassemble,1.1428571428571428
mod_inv,baseline,1.0
mod_inv,reassemble,1.0161290322580645
reverse,baseline,1.0
reverse,reassemble,1.0434782608695652
fizz-buzz,baseline,1.0
fizz-buzz,reassemble,1.0407995618838992
bitwise-ops,baseline,1.0
bitwise-ops,reassemble,1.0029585798816567
cholesky,baseline,1.0
cholesky,reassemble,1.065939909598511
mat-inv,baseline,1.0
mat-inv,reassemble,1.0162835249042146
dead-branch,baseline,1.0
dead-branch,reassemble,1.0016722408026757
ray-sphere-intersection,baseline,1.0
ray-sphere-intersection,reassemble,1.0070422535211268
conjugate-gradient,baseline,1.0
conjugate-gradient,reassemble,1.0260130065032516
leibniz,baseline,1.0
leibniz,reassemble,1.0400001696000407
n_root,baseline,1.0
n_root,reassemble,1.030013642564802
newton,baseline,1.0
newton,reassemble,1.0092165898617511
euler,baseline,1.0
euler,reassemble,1.0723270440251573
riemann,baseline,1.0
riemann,reassemble,1.0134228187919463
mandelbrot,baseline,1.0
mandelbrot,reassemble,1.0014064956061253
norm,baseline,1.0
norm,reassemble,1.0554455445544555
cordic,baseline,1.0
cordic,reassemble,1.0657640232108316
pow,baseline,1.0
pow,reassemble,1.0833333333333333
sqrt,baseline,1.0
sqrt,reassemble,1.031055900621118
quickselect,baseline,1.0
quickselect,reassemble,1.0573476702508962
sieve,baseline,1.0
sieve,reassemble,1.022975301550833
bubblesort,baseline,1.0
bubblesort,reassemble,1.1225296442687747
primitive-root,baseline,1.0
primitive-root,reassemble,1.0456977060476924
adler32,baseline,1.0
adler32,reassemble,1.0036491023208292
adj2csr,baseline,1.0
adj2csr,reassemble,1.0871285030638012
csrmv,baseline,1.0
csrmv,reassemble,1.0142076863418095
dot-product,baseline,1.0
dot-product,reassemble,1.0227272727272727
major-elm,baseline,1.0
major-elm,reassemble,1.0425531914893618
max-subarray,baseline,1.0
max-subarray,reassemble,1.0103626943005182
mat-mul,baseline,1.0
mat-mul,reassemble,1.0729031801033657
fib,baseline,1.0
fib,reassemble,1.0082644628099173
vsmul,baseline,1.0
vsmul,reassemble,1.0476544702217676
quicksort-hoare,baseline,1.0
quicksort-hoare,reassemble,1.0717081915633118
quicksort,baseline,1.0
quicksort,reassemble,1.053030303030303
two-sum,baseline,1.0
two-sum,reassemble,1.030612244897959
eight-queens,baseline,1.0
eight-queens,reassemble,1.017663002978775
binary-search,baseline,1.0
binary-search,reassemble,1.0897435897435896
```

