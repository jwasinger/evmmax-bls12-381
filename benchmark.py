import os, subprocess, re, sys

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

geth_cmd = "go test -run=^$ -bench=G1MulAvgCase"
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
print("avg case (eip5843)")
print(geth_cmd)
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

print("avg case (asm)")
print(geth_cmd)

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

# --- worst-case --------------------------------------------------------------------------------------------------------------------------------------------------------
# TODO pass cargo-path to this script
cmd ="/home/jared/.cargo/bin/cargo bench -- G1Proj"
result = subprocess.run(cmd.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=os.path.join(os.getcwd(), "bls12_381-g1mul-constant-time"))
if result.returncode != 0:
    raise Exception("geth exec error: {}".format(result.stderr))
res = re.search(r'^.*time:.*\[(.*)\]\\n', str(result.stdout)).groups()[0]
res = res.split(' ')[0:2]
if res[1] != '\\xc2\\xb5s':
    raise Exception("unit should be microseconds")

worst_case_rust_exec_time = round(float(res[0])) * 1000

geth_cmd = "go test -run=^$ -bench=G1MulWorstCase"
result = subprocess.run(geth_cmd.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=os.path.join(os.getcwd(), 'go-ethereum-eip5843/crypto/bls12381'))
if result.returncode != 0:
    raise Exception("geth exec error: {}".format(result.stderr))

result_stdout = str(result.stdout).replace('\\t', '')
worst_case_geth_exec_time = int(re.search(r'\\n.*BenchmarkG1Mul.* (.*) ns/op.*\\n', result_stdout).groups()[0])

# ---
worst_case_input = 115792089237316195423570985008687907853269984665640564039457584007913129639935
code_file = "build/artifacts/g1mul/g1mul_dbl_and_add.hex"
inp = hex(worst_case_input)
geth_path = os.path.join(os.getcwd(), "go-ethereum-eip5843/build/bin/evm")

geth_exec = os.path.join(geth_path)
geth_cmd = "{} --codefile {} --input {} --bench --statdump run".format(geth_exec, code_file, inp)
result = subprocess.run(geth_cmd.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
if result.returncode != 0:
    raise Exception("geth exec error: {}".format(result.stderr))

print("worst case (eip5843)")
print(geth_cmd)

res = str(result.stderr)
worst_case_evmmax_exec_time = res.split('\\n')[1][17:]
worst_case_evmmax_gas_used = re.search(r'EVM gas used: *([0-9]*)\\n', res)

if worst_case_evmmax_exec_time.endswith('ms'):
    # convert from ms to ns
    worst_case_evmmax_exec_time = float(worst_case_evmmax_exec_time[:-2])
    worst_case_evmmax_exec_time = round(worst_case_evmmax_exec_time * 1000000)
elif worst_case_evmmax_exec_time.endswith('\\xc2\\xb5s'):
    # microseconds
    worst_case_evmmax_exec_time = round(float(worst_case_evmmax_exec_time.strip('\\xc2\\xb5s'))) * 1000
else:
    raise Exception("script hardcoded to handle go-ethereum evm tool benchmark time output denoted in ms/microseconds.  got {}".format(evmmax_exec_time[-2:]))

# ---
code_file = "build/artifacts/g1mul/g1mul_dbl_and_add.hex"
inp = hex(worst_case_input)
geth_path = os.path.join(os.getcwd(), "go-ethereum-asm384/build/bin/evm")

geth_exec = os.path.join(geth_path)
geth_cmd = "{} --codefile {} --input {} --bench --statdump run".format(geth_exec, code_file, inp)
result = subprocess.run(geth_cmd.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
if result.returncode != 0:
    raise Exception("geth exec error: {}".format(result.stderr))

print("worst case (asm)")
print(geth_cmd)

res = str(result.stderr)
worst_case_evmmax_asm384_exec_time = res.split('\\n')[1][17:]
worst_case_evmmax_asm384_gas_used = re.search(r'EVM gas used: *([0-9]*)\\n', res)

if worst_case_evmmax_asm384_exec_time.endswith('ms'):
    # convert from ms to ns
    worst_case_evmmax_asm384_exec_time = float(worst_case_evmmax_exec_time[:-2])
    worst_case_evmmax_asm384_exec_time = round(worst_case_evmmax_exec_time * 1000000)
elif worst_case_evmmax_asm384_exec_time.endswith('\\xc2\\xb5s'):
    # microseconds
    worst_case_evmmax_asm384_exec_time = round(float(worst_case_evmmax_asm384_exec_time.strip('\\xc2\\xb5s'))) * 1000
else:
    raise Exception("script hardcoded to handle go-ethereum evm tool benchmark time output denoted in ms/microseconds.  got {}".format(worst_case_evmmax_asm384_exec_time[-2:]))

with open('benchmarks/benchmarks.csv', 'w') as f:
    f.write('avg-case-eip,{}\n'.format(evmmax_exec_time))
    f.write('avg-case-asm,{}\n'.format(evmmax_asm384_exec_time))
    f.write('avg-case-rust,{}\n'.format(rust_exec_time))
    f.write('avg-case-geth,{}\n'.format(geth_exec_time))
    f.write('worst-case-eip,{}\n'.format(worst_case_evmmax_exec_time))
    f.write('worst-case-asm,{}\n'.format(worst_case_evmmax_asm384_exec_time))
    f.write('worst-case-rust,{}\n'.format(worst_case_rust_exec_time))
    f.write('worst-case-geth,{}\n'.format(worst_case_geth_exec_time))
