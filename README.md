# evmmax-bls12381

This repository contains an EVM implementation of BLS12381 G1 point multiplication using [EVMMAX](link) opcodes.

## Usage

Download the submodules and build them:
```
git submodule init
(cd huff-rs && cargo build --release)
(cd go-ethereum-eip5843 && make all)
(cd go-ethereum-asm384 && make all)
```

Compile the Huff template source code into executable EVM bytecode snippet:
```
make
```

Run tests:
```
python3 test.py
```

Run benchmarks:
```
python3 benchmark.py
```

Benchmark output is stored in `benchmarks/benchmarks.csv`.
