import os, subprocess

from bls12_381 import g1_gen, SUBGROUP_ORDER, fq_inv, fq_mul, fq_mod, to_norm, to_mont

def bench_geth(inp: str, code_file: str):
    geth_path = os.path.join(os.getcwd(), "go-ethereum/build/bin/evm")

    geth_exec = os.path.join(geth_path)
    geth_cmd = "{} --codefile {} --input {} run".format(geth_exec, code_file, inp)
    print(geth_cmd)
    result = subprocess.run(geth_cmd.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise Exception("geth exec error: {}".format(result.stderr))

    output = result.stdout.decode('utf-8')[2:-1]
    proj_point = (int(output[0:96], 16), int(output[96:192], 16), int(output[192:], 16))
    import pdb; pdb.set_trace()
    z_inv = to_mont(fq_inv(to_norm(proj_point[2])))
    affine_point = (to_norm(fq_mul(proj_point[0], z_inv)), to_norm(fq_mul(proj_point[1], z_inv)))
    print("{}, {}".format(hex(affine_point[0]), hex(affine_point[1])))

def main():
    res = g1_gen()

    inp = hex(SUBGROUP_ORDER)

    #inp = "0x0000000000000000000000000000000000000000000000000000000000000003"
    bench_geth(inp, "build/artifacts/g1mul/g1mul_dbl_and_add.hex")
    import pdb; pdb.set_trace()
    # TODO test g1mul(fq_order) == infinity point
    # TODO test g1mul(2) == g1add(g1_gen, g1_gen)

if __name__ == "__main__":
    main()
