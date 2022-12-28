import os, subprocess, re

from bls12_381 import g1_gen, SUBGROUP_ORDER, fq_inv, fq_mul, fq_mod, to_norm, to_mont

# TODO pass cargo-path to this script
cmd ="/home/jared/.cargo/bin/cargo bench -- G1Proj"
result = subprocess.run(cmd.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=os.path.join(os.getcwd(), "bls12_381"))
if result.returncode != 0:
    raise Exception("geth exec error: {}".format(result.stderr))
res = re.search(r'^.*time:.*\[(.*)\]\\n', str(result.stdout)).groups()[0]
res = res.split(' ')[0:2]
if res[1] != '\\xc2\\xb5s':
    raise Exception("unit should be microseconds")

rust_exec_time = round(float(res[0])) * 1000

geth_cmd = "go test -run=^$ -bench=G1Mul"
result = subprocess.run(geth_cmd.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=os.path.join(os.getcwd(), 'go-ethereum-eip5843/crypto/bls12381'))
if result.returncode != 0:
    raise Exception("geth exec error: {}".format(result.stderr))

result_stdout = str(result.stdout).replace('\\t', '')
geth_exec_time = int(re.search(r'\\n.*BenchmarkG1Mul.* (.*) ns/op.*\\n', result_stdout).groups()[0])

# ---
code_file = "build/artifacts/g1mul/g1mul_dbl_and_add.hex"
inp = hex(SUBGROUP_ORDER)
geth_path = os.path.join(os.getcwd(), "go-ethereum-eip5843/build/bin/evm")

geth_exec = os.path.join(geth_path)
geth_cmd = "{} --codefile {} --input {} --bench --statdump run".format(geth_exec, code_file, inp)
result = subprocess.run(geth_cmd.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
if result.returncode != 0:
    raise Exception("geth exec error: {}".format(result.stderr))

res = str(result.stderr)
evmmax_exec_time = res.split('\\n')[1][17:]
evmmax_gas_used = re.search(r'EVM gas used: *([0-9]*)\\n', res)

if evmmax_exec_time.endswith('ms'):
    # convert from ms to ns
    evmmax_exec_time = float(evmmax_exec_time[:-2])
    evmmax_exec_time = round(evmmax_exec_time * 1000000)
elif evmmax_exec_time.endswith('\\xc2\\xb5s'):
    # microseconds
    evmmax_exec_time = round(float(evmmax_exec_time.strip('\\xc2\\xb5s'))) * 1000
else:
    raise Exception("script hardcoded to handle go-ethereum evm tool benchmark time output denoted in ms/microseconds.  got {}".format(evmmax_exec_time[-2:]))

# ---
code_file = "build/artifacts/g1mul/g1mul_dbl_and_add.hex"
inp = hex(SUBGROUP_ORDER)
geth_path = os.path.join(os.getcwd(), "go-ethereum-asm384/build/bin/evm")

geth_exec = os.path.join(geth_path)
geth_cmd = "{} --codefile {} --input {} --bench --statdump run".format(geth_exec, code_file, inp)
result = subprocess.run(geth_cmd.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
if result.returncode != 0:
    raise Exception("geth exec error: {}".format(result.stderr))

res = str(result.stderr)
evmmax_asm384_exec_time = res.split('\\n')[1][17:]
evmmax_asm384_gas_used = re.search(r'EVM gas used: *([0-9]*)\\n', res)

if evmmax_asm384_exec_time.endswith('ms'):
    # convert from ms to ns
    evmmax_asm384_exec_time = float(evmmax_exec_time[:-2])
    evmmax_asm384_exec_time = round(evmmax_exec_time * 1000000)
elif evmmax_asm384_exec_time.endswith('\\xc2\\xb5s'):
    # microseconds
    evmmax_asm384_exec_time = round(float(evmmax_asm384_exec_time.strip('\\xc2\\xb5s'))) * 1000
else:
    raise Exception("script hardcoded to handle go-ethereum evm tool benchmark time output denoted in ms/microseconds.  got {}".format(evmmax_asm384_exec_time[-2:]))

with open('benchmarks/benchmarks.csv', 'w') as f:
    f.write('evmmax-eip,{}\n'.format(evmmax_exec_time))
    f.write('evmmax-asm,{}\n'.format(evmmax_asm384_exec_time))
    f.write('rust,{}\n'.format(rust_exec_time))
    f.write('geth,{}\n'.format(geth_exec_time))
