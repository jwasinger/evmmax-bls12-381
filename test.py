import os, subprocess

from bls12_381 import g1_gen, SUBGROUP_ORDER, fq_inv, fq_mul, fq_mod, to_norm, to_mont

def pad_input(val):
    if len(hex(val)) - 2 > 96:
        raise Exception('val too big')
    return "{0:0{1}x}".format(val,96)

def pad_scalar(val):
    if len(hex(val)) - 2 > 64:
        raise Exception('val too big')

    return "{0:0{1}x}".format(val,64)

def encode_input(scalar, point):
    return pad_scalar(scalar) + pad_input(point.x) + pad_input(point.y)

def bench_geth(inp: str, code_file: str):
    geth_path = os.path.join(os.getcwd(), "go-ethereum/build/bin/evm")

    geth_exec = os.path.join(geth_path)
    geth_cmd = "{} --codefile {} --input {} run".format(geth_exec, code_file, inp)
    print(geth_cmd)
    result = subprocess.run(geth_cmd.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise Exception("geth exec error: {}".format(result.stderr))

    output = result.stdout.decode('utf-8')[2:-1]
    import pdb; pdb.set_trace()
    proj_point = (int(output[0:96], 16), int(output[96:192], 16), int(output[192:], 16))
    z_inv = to_mont(fq_inv(to_norm(proj_point[2])))
    affine_point = (to_norm(fq_mul(proj_point[0], z_inv)), to_norm(fq_mul(proj_point[1], z_inv)))
    print("{}, {}".format(hex(affine_point[0]), hex(affine_point[1])))

def run_geth(inp):
    bench_geth(inp, "build/artifacts/g1mul/g1mul_dbl_and_add.hex")

def test1():
    point = g1_gen()
    scalar = 3
    inp = encode_input(scalar, point)

# test g1_gen * subgroup_order == inf_point
def test_subgroup_order():
    point = g1_gen()
    scalar = SUBGROUP_ORDER
    inp = encode_input(scalar, point)
    res = run_geth(inp)

    assert res == '000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'

def main():
    # res = g1_gen()
    # inp = encode_input(SUBGROUP_ORDER, g1_gen())

    # inp = encode_input(3, g1_gen())
    # bench_geth(inp, "build/artifacts/g1mul/g1mul_dbl_and_add.hex")
    test_subgroup_order()
    import pdb; pdb.set_trace()
    # TODO test g1mul(fq_order) == infinity point
    # TODO test g1mul(2) == g1add(g1_gen, g1_gen)

if __name__ == "__main__":
    main()
