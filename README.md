# Cost Estimates for BLS12-381 G1/G2 Add/Mul implemented with EVMMAX Opcodes

In this doc, I give an estimate of gas cost of BLS12-381 G1/G2 scalar multiplication and addition implemented in EVM using EVMMAX opcodes.  Because GLV method appears to require modular inverse (which I haven't implemented in Huff yet) I do full double-and-add.  I use benchmarks of several native implementations scaled to `30ns/gas` to provide a basis for comparison.

of generic double-and-add scalar multiplication implemented using EVMMAX opcodes.
input is the curve subgroup order (`0x73eda753299d7d483339d80809a1d80553bda402fffe5bfeffffffff00000001`). Binary representation has `x` 1s and `y` 0s.

^ TODO check that "curve subgroup order is the correct term"



```
cost_point_add    = ...
cost_point_double = ...
cost_scalar_mul   = (cost_point_add + cost_point)double) * num_ones + cost_point_double * num_zeros
```

```
# TODO this is python scratch code: clean it up

input: 134 x (double, add) and 122 x double

point double: mul (or square)=6,  add/sub=13
point add:    mul (or square)=16, add/sub=13
```

from Geth (TODO: why are these different?  why does Geth code have conditionals?):

### Method

Chose the curve sub-group order (`0x73eda753299d7d483339d80809a1d80553bda402fffe5bfeffffffff00000001`).  Binary representatino has 134 1s and 122 zeros (TODO double-check this).  This translates to `134 x (point_double + point_add) +  122 x point_double`.

#### Counts from zk-crypto/bls12-381

| Operation | multiplication | square | addition/subtraction | double |
| ---- | ---- | ---- | ---- | ---- |
| fp2 multiplication | 3 | 0 | 5 | 0 |
| fp2 square | 2 | 0 | 2 | 1 |
| fp2 add/sub | 0 | 0 | 2 | 0 |
| fp2 double | 0 | 0 | 0 | 2 |

new from https://eprint.iacr.org/2015/1060.pdf (used in https://github.com/zkcrypto/bls12_381):
note: ~~in evm, implement `mul_by_3b` addition with multiplication because it is cheaper~~ TODO recount and compute mul_by_3b like the rust code (with addition)

| Operation | multiplication | square | addition | subtraction | double |
| ---- | ---- | ---- | ---- | ---- | ---- |
| point double | 7 | 0 | 8 |  1  | 0
| point add | 12 | 0 | 9 | 5 | 0 |

TODO:
* https://github.com/zkcrypto/bls12_381 g1 point add formula is 12 mul instead of 11 (disregarding muls by 3b) in https://eprint.iacr.org/2015/1060.pdf . what gives?

#### Counts of fp/fp2 operations in g1/g2 point addition and doubling:
| Operation | multiplication | square | addition | subtraction | double | 
| ----          | ---- | ---- | ---- | ---- | ---- |
| point double | 2   | 5    | 2 | 5 | 7 |
| point add    | 8 | 5 | 1 | 7 | 4 |

#### Fp2 Fp Op Counts

| Operation | multiplication | square | addition/subtraction | double |
| ---- | ---- | ---- | ---- | ---- |
| fp2 multiplication | 3 | 0 | 5 | 0 |
| fp2 square | 2 | 0 | 2 | 1 |
| fp2 add/sub | 0 | 0 | 2 | 0 |
| fp2 double | 0 | 0 | 0 | 2 |

### Best Cost Estimates

#### G1Add Cost

| Cost Model | 4/1 | 3/1 | 2/1 |
| ---------- | --- | -- | -- |

| Algorithm | Arithmetic Cost | Other EVM Overhead |
| ---- | ---- | ---- |
| Geth/Kilic |  | |
| Complete | | |

#### G1Mul Cost

| Algorithm | Arithmetic Cost | Other EVM Overhead |
| ---- | ---- | ---- |
| Geth/Kilic |  | |
| Complete | | |

#### G2Add Cost

| Algorithm | Arithmetic Cost | Other EVM Overhead |
| ---- | ---- | ---- |
| Geth/Kilic |  | |
| Geth/Kilic (keccak256) | |
| Complete | | |

#### G2Mul Cost

| Algorithm | Arithmetic Cost | Other EVM Overhead |
| ---- | ---- | ---- |
| Geth/Kilic |  | |
| Geth/Kilic (keccak256) | | |
| Complete | | |

Scalar multiplication cost

---
#### Sketch of Huff Code for 
#### Sketch of Huff Code for Geth/Kilic G1Mul

```
#define constant INPUT_SLOT = ...
#define constant OUTPUT_SLOT = INPUT_SLOT + 3
#define constant SCRATCH_SLOT = OUTPUT_SLOT + 3
#define constant ZERO_SLOT = SCRATCH_SLOT + 3

#define constant DOUBLE_INPUT_SLOT = ...
#define constant DOUBLE_OUTPUT_SLOT = DOUBLE_INPUT_SLOT + 3
#define constant DOUBLE_SCRATCH_SLOT = DOUBLE_OUTPUT_SLOT + 3

#define constant ADD_INPUT_SLOT1 = OUTPUT_SLOT
#define constant ADD_INPUT_SLOT2 = SCRATCH_SLOT
#define constant ADD_OUTPUT_SLOT = ...

// define some scratch space
#define constant T0_SLOT = ...
#define constant T1_SLOT = T0_SLOT + 1
#define constant T2_SLOT = T1_SLOT + 1
#define constant T3_SLOT = T2_SLOT + 1
#define constant T4_SLOT = T3_SLOT + 1
#define constant T5_SLOT = T4_SLOT + 1
#define constant T6_SLOT = T5_SLOT + 1
#define constant T7_SLOT = T6_SLOT + 1
#define cconstant T8_SLOT + T7_SLOT + 1

// est (TODO scratch): 80 gas / G1Add of non-arithmetic overhead
#define macro G1Add() = takes(0) returns(0) {
    ...
    // if INPUT1.z == 0:
 
    $INPUT1_Z_OFFSET_LO
    mload
    $INPUT1_Z_OFFSET_HI
    mload
    128
    shr
    0x0
    eq
    not
    check_input2 jumpi

   //     return INPUT2 
    __addmodx(OUTPUT_SLOT_0, INPUT_SLOT_0, ZERO_SLOT)
    __addmodx(OUTPUT_SLOT_1, INPUT_SLOT_1, ZERO_SLOT)
    __addmodx(OUTPUT_SLOT_2, INPUT_SLOT_2, ZERO_SLOT)
    end jumpi

check_input2:   
    // if INPUT2.z == 0:
    
    $INPUT2_Z_OFFSET_LO
    mload
    $INPUT2_Z_OFFSET_HI
    mload
    128
    shr
    0x0
    eq
    not
    end_check_input jumpi

    // sha3 version
    $INPUT2_Z_OFFSET_LO
    48
    sha3
    $known_hash_of_0x00....0
    eq
    not
    end_check_input jumpi
    
    //     return INPUT1
    __addmodx(OUTPUT_SLOT_0, INPUT_SLOT_0, ZERO_SLOT)
    __addmodx(OUTPUT_SLOT_1, INPUT_SLOT_1, ZERO_SLOT)
    __addmodx(OUTPUT_SLOT_2, INPUT_SLOT_2, ZERO_SLOT)
    end jumpi
    
end_check_input
    __mulmontx(TEMP_SLOT+7, ADD_INPUT_1 + 2, ADD_INPUT_1 + 2)
    __mulmontx(TEMP_SLOT + 1, ADD_INPUT_2, TEMP_SLOT + 7)
    __mulmontx(TEMP_SLOT + 2, ADD_INPUT_1 + 2, TEMP_SLOT + 7)
    __mulmontx(TEMP_SLOT, ADD_INPUT_2 + 1, TEMP_SLOT + 2)
    __mulmontx(TEMP_SLOT + 8, ADD_INPUT_2 + 2, ADD_INPUT_2 + 2)
    __mulmontx(TEMP_SLOT + 3, ADD_INPUT_1, TEMP_SLOT + 8)
    __mulmontx(TEMP_SLOT + 4, ADD_INPUT_1 + 2, TEMP_SLOT + 8)
    __mulmontx(TEMP_SLOT + 2, ADD_INPUT_1 + 1, TEMP_SLOT + 4)

    // if temp_slot_1 == temp_slot_3 {
    //  
    __submodx(TEMP_SLOT_1, TEMP_SLOT_1, TEMP_SLOT_3)
    $TEMP_SLOT_1_OFFSET
    mload
    $TEMP_SLOT_1_OFFSET_PLUS_32
    mload
    0x80 // 124
    shr
    eq
    not
    
    //    if t[0] == t[2] {
    //        return PointDouble()
    //    }
    

    
ret_zero_point:
    //    return 0 point
    
    // }

    /*
    if t[1].equal(t[3]) {
        if t[0].equal(t[2]) {
            return g.Double(r, p1) 
        }
        return r.Zero()
    }
    */
    
end_0:
    __submodx( TEMP_SLOT_1, TEMP_SLOT_1, TEMP_SLOT_3)
    __addmodx( TEMP_SLOT_4, TEMP_SLOT_1, TEMP_SLOT_1)
    __mulmontx(TEMP_SLOT_4, TEMP_SLOT_4, TEMP_SLOT_4)
    __mulmontx(TEMP_SLOT_5, TEMP_SLOT_1, TEMP_SLOT_4)
    __submodx( TEMP_SLOT_0, TEMP_SLOT_0, TEMP_SLOT_2)
    __addmodx( TEMP_SLOT_0, TEMP_SLOT_0, TEMP_SLOT_0)
    __mulmontx(TEMP_SLOT_6, TEMP_SLOT_0, TEMP_SLOT_0)
    __submodx( TEMP_SLOT_6, TEMP_SLOT_6, TEMP_SLOT_5)
    __mulmontx(TEMP_SLOT_3, TEMP_SLOT_3, TEMP_SLOT_4)
    __addmodx( TEMP_SLOT_4, TEMP_SLOT_3, TEMP_SLOT_3)
    __submodx( OUTPUT_SLOT_0, TEMP_SLOT_6, TEMP_SLOT_4)
    __submodx( TEMP_SLOT_4, TEMP_SLOT_3, OUTPUT_SLOT_0)
    __mulmontx(TEMP_SLOT_6, TEMP_SLOT_2, TEMP_SLOT_5)
    __addmodx(TEMP_SLOT_6, TEMP_SLOT_6, TEMP_SLOT_6)
    __mulmontx(TEMP_SLOT_0, TEMP_SLOT_0, TEMP_SLOT_4)
    __submodx(OUTPUT_SLOT_1, TEMP_SLOT_0, TEMP_SLOT_6)
    __addmodx(TEMP_SLOT_0, INPUT_1_2, INPUT_2_2)
    __mulmontx(TEMP_SLOT_0, TEMP_SLOT_0, TEMP_SLOT_0)
    __submodx(TEMP_SLOT_0, TEMP_SLOT_0, TEMP_SLOT_7)
    __submodx(TEMP_SLOT_0, TEMP_SLOT_0, TEMP_SLOT_8)
    __mulmontx(OUTPUT_SLOT_2, TEMP_SLOT_0, TEMP_SLOT_1)
end_1:
}

#define macro G1Double() = takes(0) returns(0) {
    // if DOUBLE_INPUT.z == 0:
    //    return DOUBLE_INPUT
    

    /*
    t := g.t
    square(t[0], &p[0])
    square(t[1], &p[1])
    square(t[2], t[1])
    add(t[1], &p[0], t[1])
    square(t[1], t[1])
    sub(t[1], t[1], t[0])
    sub(t[1], t[1], t[2])
    double(t[1], t[1])
    double(t[3], t[0])
    add(t[0], t[3], t[0])
    square(t[4], t[0])
    double(t[3], t[1])
    sub(&r[0], t[4], t[3])
    sub(t[1], t[1], &r[0])
    double(t[2], t[2])
    double(t[2], t[2])
    double(t[2], t[2])
    mul(t[0], t[0], t[1])
    sub(t[1], t[0], t[2])
    mul(t[0], &p[1], &p[2])
    r[1].set(t[1])
    double(&r[2], t[0])
    return r
    */
}

#define macro G1Mul() = takes(1) returns(0) {
    // copy INPUT_SLOT to OUTPUT_SLOT
    __addmodx(OUTPUT_SLOT, INPUT_SLOT, ZERO_SLOT)
    __addmodx(OUTPUT_SLOT + 1, INPUT_SLOT + 1, ZERO_SLOT)
    __addmodx(OUTPUT_SLOT + 2, INPUT_SLOT + 2, ZERO_SLOT)
    // scratch point slot initially set to 0x000...00

    // while scalar != 0 {
    
    start:
    dup1
    0x0
    eq
    end jumpi
    
    //     if scalar & 1 != 0 {
    //        OUTPUT_SLOT <- point_add(OUTPUT_SLOT, SCRATCH_SLOT)

    dup1
    0x01
    and
    not
    double_step jumpi
    
    G1Add()
    
    double_step:
    //     SCRATCH_SLOT <- point_double(SCRATCH_SLOT, SCRATCH_SLOT)
    
    // copy SCRATCH_SLOT to POINT_DOUBLE_INPUT_SLOT
    __addmodx(POINT_DOUBLE_INPUT_SLOT, SCRATCH_SLOT, ZERO_SLOT)
    __addmodx(POINT_DOUBLE_INPUT_SLOT + 1, SCRATCH_SLOT + 1, ZERO_SLOT)
    __addmodx(POINT_DOUBLE_INPUT_SLOT + 2, SCRATCH_SLOT + 2, ZERO_SLOT)
    
    G1Double()

    // copy output to SCRATCH_SLOT
    __addmodx(SCRATCH_SLOT, POINT_DOUBLE_OUTPUT_SLOT, ZERO_SLOT)
    __addmodx(SCRATCH_SLOT + 1, POINT_DOUBLE_OUTPUT_SLOT + 1, ZERO_SLOT)
    __addmodx(SCRATCH_SLOT + 2, POINT_DOUBLE_OUTPUT_SLOT + 2, ZERO_SLOT)

    // scalar = scalar >> 1
    0x01
    shr

    start
    jumpi
    end:
}
```



#### G1

Geth [G1Add](https://github.com/ethereum/go-ethereum/blob/master/crypto/bls12381/g1.go#L248-L294) and [G1Double](https://github.com/ethereum/go-ethereum/blob/master/crypto/bls12381/g1.go#L296-L326)

```
cost_g1_point_add = 6 * cost_g1_mul + 13 * cost_g1_add_sub
cost_g1_point_double = 16 * cost_g1_mul + 13 * cost_g1_add_sub
```

#### G2

```
cost_g2_point_add = 6 * cost_g2_mul + 13 * cost_g1_addsub
```

Compared against other implementations of the double-and-add algorithm:

##### bls12381 impl in geth
```
> go test -bench=G1Mul
BenchmarkG1Mul-4            4102            279140 ns/op
```

##### kilic/bls12-381
```
> go test -bench=G1Mul
BenchmarkG1MulWNAF/Naive-4                  5377            203893 ns/op
```
---
#### G2
Thing
