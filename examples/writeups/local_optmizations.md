
We implemented trivial global dead code elimnation, local dead code elimination and, local value numbering.

In general, many of the benchmark codes were already locally optimized, with the brench benchmark outputting very similar benchmarks for those locally optimized, adn those non-locally optimized. Table for benchmark results are in the appendix of this writeup. However, we are able to produce programs where the local optimizations perform, and also programs where the local optimizations have less of an impact.

The following bril program is transformed into this json:
```bril
@tdce() {
  a: int = const 1;
  b: int = const 2;
  c: int = add a b;
  b: int = const 3;
  d: int = add a b;
  print d;
}


@main() {
  a: int = const 1;

  # local dead code elimnation
  a: int = const 3;
  b: int = const 2;

  # Common subexpression elimination
  c: int = add a b; 
  d: int = add a b;
  e: int = add a b;
}

```

```json
{
  "functions": [
    {
      "instrs": [
        {
          "label": "b1"
        },
        {
          "dest": "a",
          "op": "const",
          "type": "int",
          "value": 1
        },
        {
          "dest": "lvn.1",
          "op": "const",
          "type": "int",
          "value": 2
        },
        {
          "dest": "b",
          "op": "const",
          "type": "int",
          "value": 3
        },
        {
          "args": [
            "a",
            "b"
          ],
          "dest": "d",
          "op": "add",
          "type": "int"
        },
        {
          "args": [
            "d"
          ],
          "op": "print"
        }
      ],
      "name": "tdce"
    },
    {
      "instrs": [
        {
          "label": "b1"
        },
        {
          "dest": "a",
          "op": "const",
          "type": "int",
          "value": 3
        },
        {
          "dest": "b",
          "op": "const",
          "type": "int",
          "value": 2
        },
        {
          "args": [
            "a",
            "b"
          ],
          "dest": "c",
          "op": "add",
          "type": "int"
        }
      ],
      "name": "main"
    }
  ]
}
```

Whereas, most bril programs are written in a way that the local optimizations do not have a significant impact. The following bril program is transformed into this json:
```bril
@main() {
  a: int = const 1;
  b: int = const 2;
  d: int = add a b;
  e: int = const 4;
  f: int = e + d;
  g: int = f + e;
}
```

```json

{
  "functions": [
    {
      "instrs": [
        {
          "label": "b1"
        },
        {
          "dest": "a",
          "op": "const",
          "type": "int",
          "value": 1
        },
        {
          "dest": "b",
          "op": "const",
          "type": "int",
          "value": 2
        },
        {
          "args": [
            "a",
            "b"
          ],
          "dest": "d",
          "op": "add",
          "type": "int"
        },
        {
          "dest": "e",
          "op": "const",
          "type": "int",
          "value": 4
        },
        {
          "args": [
            "e",
            "d"
          ],
          "dest": "f",
          "op": "add",
          "type": "int"
        }
      ],
      "name": "main"
    }
  ]
}
```

```
benchmark,run,result
quadratic,baseline,785
quadratic,trivial_global_elim,783
primes-between,baseline,574100
primes-between,trivial_global_elim,574100
birthday,baseline,484
birthday,trivial_global_elim,483
orders,baseline,5352
orders,trivial_global_elim,5352
sum-check,baseline,5018
sum-check,trivial_global_elim,5018
palindrome,baseline,298
palindrome,trivial_global_elim,298
totient,baseline,253
totient,trivial_global_elim,253
relative-primes,baseline,1923
relative-primes,trivial_global_elim,1914
hanoi,baseline,99
hanoi,trivial_global_elim,99
is-decreasing,baseline,127
is-decreasing,trivial_global_elim,127
check-primes,baseline,8468
check-primes,trivial_global_elim,8419
sum-sq-diff,baseline,3038
sum-sq-diff,trivial_global_elim,3036
fitsinside,baseline,10
fitsinside,trivial_global_elim,10
fact,baseline,229
fact,trivial_global_elim,228
loopfact,baseline,116
loopfact,trivial_global_elim,115
recfact,baseline,104
recfact,trivial_global_elim,103
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
euclid,trivial_global_elim,562
binary-fmt,baseline,100
binary-fmt,trivial_global_elim,100
lcm,baseline,2326
lcm,trivial_global_elim,2326
gcd,baseline,46
gcd,trivial_global_elim,46
catalan,baseline,659378
catalan,trivial_global_elim,659378
armstrong,baseline,133
armstrong,trivial_global_elim,130
pascals-row,baseline,146
pascals-row,trivial_global_elim,139
collatz,baseline,169
collatz,trivial_global_elim,169
sum-bits,baseline,73
sum-bits,trivial_global_elim,73
rectangles-area-difference,baseline,14
rectangles-area-difference,trivial_global_elim,14
mod_inv,baseline,558
mod_inv,trivial_global_elim,556
reverse,baseline,46
reverse,trivial_global_elim,46
fizz-buzz,baseline,3652
fizz-buzz,trivial_global_elim,3552
bitwise-ops,baseline,1690
bitwise-ops,trivial_global_elim,1689
cholesky,baseline,3761
cholesky,trivial_global_elim,3750
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
euler,trivial_global_elim,1907
riemann,baseline,298
riemann,trivial_global_elim,298
mandelbrot,baseline,2720947
mandelbrot,trivial_global_elim,2720813
norm,baseline,505
norm,trivial_global_elim,505
cordic,baseline,517
cordic,trivial_global_elim,516
pow,baseline,36
pow,trivial_global_elim,34
sqrt,baseline,322
sqrt,trivial_global_elim,321
quickselect,baseline,279
quickselect,trivial_global_elim,279
sieve,baseline,3482
sieve,trivial_global_elim,3455
bubblesort,baseline,253
bubblesort,trivial_global_elim,253
primitive-root,baseline,11029
primitive-root,trivial_global_elim,11024
adler32,baseline,6851
adler32,trivial_global_elim,6851
adj2csr,baseline,56629
adj2csr,trivial_global_elim,56629
csrmv,baseline,121202
csrmv,trivial_global_elim,120652
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
two-sum,trivial_global_elim,88
eight-queens,baseline,1006454
eight-queens,trivial_global_elim,959702
binary-search,baseline,78
binary-search,trivial_global_elim,75
```

```
benchmark,run,result
quadratic,baseline,785
quadratic,local_dead_code_elim,785
primes-between,baseline,574100
primes-between,local_dead_code_elim,574100
birthday,baseline,484
birthday,local_dead_code_elim,484
orders,baseline,5352
orders,local_dead_code_elim,5352
sum-check,baseline,5018
sum-check,local_dead_code_elim,5018
palindrome,baseline,298
palindrome,local_dead_code_elim,298
totient,baseline,253
totient,local_dead_code_elim,253
relative-primes,baseline,1923
relative-primes,local_dead_code_elim,1923
hanoi,baseline,99
hanoi,local_dead_code_elim,99
is-decreasing,baseline,127
is-decreasing,local_dead_code_elim,127
check-primes,baseline,8468
check-primes,local_dead_code_elim,8468
sum-sq-diff,baseline,3038
sum-sq-diff,local_dead_code_elim,3038
fitsinside,baseline,10
fitsinside,local_dead_code_elim,10
fact,baseline,229
fact,local_dead_code_elim,229
loopfact,baseline,116
loopfact,local_dead_code_elim,116
recfact,baseline,104
recfact,local_dead_code_elim,104
factors,baseline,72
factors,local_dead_code_elim,72
perfect,baseline,232
perfect,local_dead_code_elim,232
bitshift,baseline,167
bitshift,local_dead_code_elim,167
digital-root,baseline,247
digital-root,local_dead_code_elim,247
up-arrow,baseline,252
up-arrow,local_dead_code_elim,252
sum-divisors,baseline,159
sum-divisors,local_dead_code_elim,159
ackermann,baseline,1464231
ackermann,local_dead_code_elim,1464231
pythagorean_triple,baseline,61518
pythagorean_triple,local_dead_code_elim,61518
euclid,baseline,563
euclid,local_dead_code_elim,563
binary-fmt,baseline,100
binary-fmt,local_dead_code_elim,100
lcm,baseline,2326
lcm,local_dead_code_elim,2326
gcd,baseline,46
gcd,local_dead_code_elim,46
catalan,baseline,659378
catalan,local_dead_code_elim,659378
armstrong,baseline,133
armstrong,local_dead_code_elim,133
pascals-row,baseline,146
pascals-row,local_dead_code_elim,146
collatz,baseline,169
collatz,local_dead_code_elim,169
sum-bits,baseline,73
sum-bits,local_dead_code_elim,73
rectangles-area-difference,baseline,14
rectangles-area-difference,local_dead_code_elim,14
mod_inv,baseline,558
mod_inv,local_dead_code_elim,558
reverse,baseline,46
reverse,local_dead_code_elim,46
fizz-buzz,baseline,3652
fizz-buzz,local_dead_code_elim,3652
bitwise-ops,baseline,1690
bitwise-ops,local_dead_code_elim,1690
cholesky,baseline,3761
cholesky,local_dead_code_elim,3761
mat-inv,baseline,1044
mat-inv,local_dead_code_elim,1044
dead-branch,baseline,1196
dead-branch,local_dead_code_elim,1196
function_call,baseline,timeout
function_call,local_dead_code_elim,timeout
ray-sphere-intersection,baseline,142
ray-sphere-intersection,local_dead_code_elim,142
conjugate-gradient,baseline,1999
conjugate-gradient,local_dead_code_elim,1999
leibniz,baseline,12499997
leibniz,local_dead_code_elim,12499997
n_root,baseline,733
n_root,local_dead_code_elim,733
newton,baseline,217
newton,local_dead_code_elim,217
euler,baseline,1908
euler,local_dead_code_elim,1908
riemann,baseline,298
riemann,local_dead_code_elim,298
mandelbrot,baseline,2720947
mandelbrot,local_dead_code_elim,2720947
norm,baseline,505
norm,local_dead_code_elim,505
cordic,baseline,517
cordic,local_dead_code_elim,517
pow,baseline,36
pow,local_dead_code_elim,36
sqrt,baseline,322
sqrt,local_dead_code_elim,322
quickselect,baseline,279
quickselect,local_dead_code_elim,279
sieve,baseline,3482
sieve,local_dead_code_elim,3482
bubblesort,baseline,253
bubblesort,local_dead_code_elim,253
primitive-root,baseline,11029
primitive-root,local_dead_code_elim,11029
adler32,baseline,6851
adler32,local_dead_code_elim,6851
adj2csr,baseline,56629
adj2csr,local_dead_code_elim,56629
csrmv,baseline,121202
csrmv,local_dead_code_elim,121202
dot-product,baseline,88
dot-product,local_dead_code_elim,88
major-elm,baseline,47
major-elm,local_dead_code_elim,47
max-subarray,baseline,193
max-subarray,local_dead_code_elim,193
mat-mul,baseline,1990407
mat-mul,local_dead_code_elim,1990407
fib,baseline,121
fib,local_dead_code_elim,121
vsmul,baseline,86036
vsmul,local_dead_code_elim,86036
quicksort-hoare,baseline,27333
quicksort-hoare,local_dead_code_elim,27333
quicksort,baseline,264
quicksort,local_dead_code_elim,264
two-sum,baseline,98
two-sum,local_dead_code_elim,98
eight-queens,baseline,1006454
eight-queens,local_dead_code_elim,1006454
binary-search,baseline,78
binary-search,local_dead_code_elim,78
```

```
benchmark,run,result
quadratic,baseline,785
quadratic,local_dead_code_elim,785
primes-between,baseline,574100
primes-between,local_dead_code_elim,574100
birthday,baseline,484
birthday,local_dead_code_elim,484
orders,baseline,5352
orders,local_dead_code_elim,5352
sum-check,baseline,5018
sum-check,local_dead_code_elim,5018
palindrome,baseline,298
palindrome,local_dead_code_elim,298
totient,baseline,253
totient,local_dead_code_elim,253
relative-primes,baseline,1923
relative-primes,local_dead_code_elim,1923
hanoi,baseline,99
hanoi,local_dead_code_elim,99
is-decreasing,baseline,127
is-decreasing,local_dead_code_elim,127
check-primes,baseline,8468
check-primes,local_dead_code_elim,8468
sum-sq-diff,baseline,3038
sum-sq-diff,local_dead_code_elim,3038
fitsinside,baseline,10
fitsinside,local_dead_code_elim,10
fact,baseline,229
fact,local_dead_code_elim,229
loopfact,baseline,116
loopfact,local_dead_code_elim,116
recfact,baseline,104
recfact,local_dead_code_elim,104
factors,baseline,72
factors,local_dead_code_elim,72
perfect,baseline,232
perfect,local_dead_code_elim,232
bitshift,baseline,167
bitshift,local_dead_code_elim,167
digital-root,baseline,247
digital-root,local_dead_code_elim,247
up-arrow,baseline,252
up-arrow,local_dead_code_elim,252
sum-divisors,baseline,159
sum-divisors,local_dead_code_elim,159
ackermann,baseline,1464231
ackermann,local_dead_code_elim,1464231
pythagorean_triple,baseline,61518
pythagorean_triple,local_dead_code_elim,61518
euclid,baseline,563
euclid,local_dead_code_elim,563
binary-fmt,baseline,100
binary-fmt,local_dead_code_elim,100
lcm,baseline,2326
lcm,local_dead_code_elim,2326
gcd,baseline,46
gcd,local_dead_code_elim,46
catalan,baseline,659378
catalan,local_dead_code_elim,659378
armstrong,baseline,133
armstrong,local_dead_code_elim,133
pascals-row,baseline,146
pascals-row,local_dead_code_elim,146
collatz,baseline,169
collatz,local_dead_code_elim,169
sum-bits,baseline,73
sum-bits,local_dead_code_elim,73
rectangles-area-difference,baseline,14
rectangles-area-difference,local_dead_code_elim,14
mod_inv,baseline,558
mod_inv,local_dead_code_elim,558
reverse,baseline,46
reverse,local_dead_code_elim,46
fizz-buzz,baseline,3652
fizz-buzz,local_dead_code_elim,3652
bitwise-ops,baseline,1690
bitwise-ops,local_dead_code_elim,1690
cholesky,baseline,3761
cholesky,local_dead_code_elim,3761
mat-inv,baseline,1044
mat-inv,local_dead_code_elim,1044
dead-branch,baseline,1196
dead-branch,local_dead_code_elim,1196
function_call,baseline,timeout
function_call,local_dead_code_elim,timeout
ray-sphere-intersection,baseline,142
ray-sphere-intersection,local_dead_code_elim,142
conjugate-gradient,baseline,1999
conjugate-gradient,local_dead_code_elim,1999
leibniz,baseline,12499997
leibniz,local_dead_code_elim,12499997
n_root,baseline,733
n_root,local_dead_code_elim,733
newton,baseline,217
newton,local_dead_code_elim,217
euler,baseline,1908
euler,local_dead_code_elim,1908
riemann,baseline,298
riemann,local_dead_code_elim,298
mandelbrot,baseline,2720947
mandelbrot,local_dead_code_elim,2720947
norm,baseline,505
norm,local_dead_code_elim,505
cordic,baseline,517
cordic,local_dead_code_elim,517
pow,baseline,36
pow,local_dead_code_elim,36
sqrt,baseline,322
sqrt,local_dead_code_elim,322
quickselect,baseline,279
quickselect,local_dead_code_elim,279
sieve,baseline,3482
sieve,local_dead_code_elim,3482
bubblesort,baseline,253
bubblesort,local_dead_code_elim,253
primitive-root,baseline,11029
primitive-root,local_dead_code_elim,11029
adler32,baseline,6851
adler32,local_dead_code_elim,6851
adj2csr,baseline,56629
adj2csr,local_dead_code_elim,56629
csrmv,baseline,121202
csrmv,local_dead_code_elim,121202
dot-product,baseline,88
dot-product,local_dead_code_elim,88
major-elm,baseline,47
major-elm,local_dead_code_elim,47
max-subarray,baseline,193
max-subarray,local_dead_code_elim,193
mat-mul,baseline,1990407
mat-mul,local_dead_code_elim,1990407
fib,baseline,121
fib,local_dead_code_elim,121
vsmul,baseline,86036
vsmul,local_dead_code_elim,86036
quicksort-hoare,baseline,27333
quicksort-hoare,local_dead_code_elim,27333
quicksort,baseline,264
quicksort,local_dead_code_elim,264
two-sum,baseline,98
two-sum,local_dead_code_elim,98
eight-queens,baseline,1006454
eight-queens,local_dead_code_elim,1006454
binary-search,baseline,78
binary-search,local_dead_code_elim,78
```
