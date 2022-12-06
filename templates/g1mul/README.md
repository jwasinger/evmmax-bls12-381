# G1Mul

Point addition consists of successive adding and doubling the generator point by a scalar.

### Full double-and-add point multiplication algorithm:
```
def ecmul_double_and_add(point, scalar):
    for bit in scalar:
        if bit == 1:
            double()
            if inf:
                return inf
        add()
        if inf:
            return inf
```

some observations about an efficient EVM implementation:
* we can unroll the double-and-add loop (255 max iterations) to save on EVM conditional flow overhead.
* the infinity checks can be delayed until the final iteration of the loop: G1 * scalar can only be infinity point if the scalar is gte the group order (255-bit number).

### Improvement: windowed method

We can simultaneously reduce the number of additions by 75% and EVM conditional flow overhead by `x%` by using a windowed method:

```
def ecmul_windowed():
    for scalar_piece in decomposed_scalar:
        for i in range(window_size):
            # in the EVM impl, this loop can be unrolled and we can
            # have a double_{{window_size}}_times macro which reduces
            # overhead vs having to call double separately each time
            # in the naive double-and-add algorithm
            double()
        add()
```

The speedup here comes from reducing the number of additions by 75% compared to the naive algorithm.  In addition, knowing that doublings always happen 4 consecutive times on the same value allow us to reduce EVM conditional flow overhead compared to the naive algorithm.

### Other Improvements to Try

There seem to be a host of other optimizations that could be used here.  Some include:
* expressing the scalar in NAF to reduce the number of doublings
* using the GLV method to reduce the number of doublings further
