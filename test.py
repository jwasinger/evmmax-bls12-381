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
    geth_path = os.path.join(os.getcwd(), "go-ethereum-eip5843/build/bin/evm")

    geth_exec = os.path.join(geth_path)
    geth_cmd = "{} --codefile {} --input {} run".format(geth_exec, code_file, inp)
    result = subprocess.run(geth_cmd.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise Exception("geth exec error: {}".format(result.stderr))

    output = result.stdout.decode('utf-8')[2:-1]
    return output

def run_geth(inp):
    return bench_geth(inp, "build/artifacts/g1mul/g1mul_dbl_and_add.hex")

def test_subgroup_order():
    point = g1_gen()
    scalar = SUBGROUP_ORDER
    inp = encode_input(scalar, point)
    res = run_geth(inp)

    assert res == '000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'

def test3():
    point = g1_gen()
    scalar = 3
    inp = encode_input(scalar, point)
    res = run_geth(inp)

    assert res == '0a59e0a886919a3e3b746e549319d23dae362a728a29b6d804d02f86aeb43bd288207db6420a5d639d74409f5c53442d0eff673f0d01d28ace893c37229adaa3f139dcc81306308583c4fe2e7c5d70f9778e2d71e22804b2878f1b6d644f087b03adbc0d6fe485af1096a983741bf93f28cbbb920607abff8856ea833538197d094e67c9559d61baaaa51ff2f01bc682'

def test1():
    point = g1_gen()
    scalar = 1
    inp = encode_input(scalar, point)
    output = run_geth(inp)

    proj_point = (int(output[0:96], 16), int(output[96:192], 16), int(output[192:], 16))
    z_inv = to_mont(fq_inv(to_norm(proj_point[2])))
    affine_point = (to_norm(fq_mul(proj_point[0], z_inv)), to_norm(fq_mul(proj_point[1], z_inv)))

    assert affine_point[0] == point.x and affine_point[1] == point.y

def main():
    print("hardcoded test case 1")
    test1()
    print("hardcoded test case 2")
    test3()
    print("test g0_gen * subgroup_order == inf_point")
    test_subgroup_order()

if __name__ == "__main__":
    main()
