import os, subprocess

from bls12_381 import g1_gen, SUBGROUP_ORDER

def bench_geth(inp: str, code_file: str):
    geth_path = os.path.join(os.getcwd(), "go-ethereum/build/bin/evm")

    geth_exec = os.path.join(geth_path)
    geth_cmd = "{} --codefile {} --input {} --json run".format(geth_exec, code_file, inp)
    print(geth_cmd)
    result = subprocess.run(geth_cmd.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise Exception("geth exec error: {}".format(result.stderr))

def main():
    res = g1_gen()

    inp = hex(SUBGROUP_ORDER)[2:]
    bench_geth(inp, "build/artifacts/g1mul/g1mul_dbl_and_add.hex")
    # TODO test g1mul(fq_order) == infinity point
    # TODO test g1mul(2) == g1add(g1_gen, g1_gen)

if __name__ == "__main__":
    main()
