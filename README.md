# evmmax-bls12381

This repository contains EVM implementations of BLS12831 G1/G2 point multiplication using [EIP-5843](https://github.com/ethereum/EIPs/pull/5843).

## Usage

Download the submodules:
```
git submodule update --init
```

Build Geth:
```
(cd go-ethereum && make all)
```

Build Huff compiler:
```
(cd huff-rs && cargo build --release)
```

Build the contracts:
```
make
```

Run contract tests:
```
python3 test.py
```
