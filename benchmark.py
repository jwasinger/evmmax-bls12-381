import os, subprocess, re

# TODO pass cargo-path to this script
cmd ="/home/jared/.cargo/bin/cargo bench -- G1Proj"
result = subprocess.run(cmd.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=os.path.join(os.getcwd(), "bls12_381"))
if result.returncode != 0:
    raise Exception("geth exec error: {}".format(result.stderr))
res = re.search(r'^.*time:.*\[(.*)\]\\n', str(result.stdout)).groups()[0]
res = res.split(' ')[0:2]
if res[1] != '\\xc2\\xb5s':
    import pdb; pdb.set_trace()
    raise Exception("unit should be microseconds")

rust_exec_time = float(res[0])
import pdb; pdb.set_trace()
