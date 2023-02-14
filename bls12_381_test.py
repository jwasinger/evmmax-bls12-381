from bls12_381 import fq2_inv, fq2_mul, fq2_add, to_mont, fq_inv, fq_mul

fe1 = (to_mont(2), 0)

res = fq2_mul(fe1, fe1)
inv = fq2_inv(res) 

assert fq2_mul(res, inv) == (1, 0)
