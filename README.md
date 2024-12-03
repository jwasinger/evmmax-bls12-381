# evmmax-bls12381

This repository contains a python-based [Huff](https://github.com/huff-language/huff-rs) generation tool for creating crypto contracts that use EVMMAX ([EIP-6690](https://eips.ethereum.org/EIPS/eip-6690)).  It uses the Jinja2 templating framework.

**Note** the scope of this project at the time it was created was the implementation of bls12381 G1/G2 ecmul using the naive double-and-add algorithm as well as modular inversion via generated addchains.  Atm, it may be lacking flexibility/features necessary for more complicated crypto contracts.

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

## Template Format

Templates live under the `templates` folder.

Each template is self-contained and creates a single contract in the output directory (huff code in `build/src`, hex-encoded bytecode under `build/artifacts`). There is no code-sharing/module system yet.

Each template currently only supports one active field context (the EIP term for a modulus + allocated space of virtual registers).

Before any Huff functions/macros are defined, each template begins with a header which defines the layout of the virtual register space:  inputs, outputs and temporary values (required to be in that order exactly).  Value types are base field elements and field extension elements for G1 and G2 ecmul respectively.

As the header methods are executed, a symbol table is constructed.  It maps string names to one or more contiguous virtual registers in the field context allocation, or segments of the EVM memory space.

Upon invoking `emit_evmmax_store_inputs`, Inputs are taken in the order they were defined in the header, starting from offset 0 in memory, and placed into virtual registers with a single call to the `storex` opcode.

Arithmetic operations on base and extension field elements are performed with `emit_f_add`, `emit_f_sub`, `emit_f_mul`, and many others.  They take as parameters, string symbols corresponding to inputs/outputs.  Opcodes `addmodx`/`submodx`/`mulmodx` can be invoked directly with `emit_addmodx`, `emit_submodx`, `emit_mulmodx`.

Upon completing computation, `emit_evmmax_load_outputs` is invoked, symbols specified as outputs are loaded to memory with a call to the `loadx` opcode.  The destination range starts after the memory range occupied by inputs, and outputs are likewise ordered the same in memory that they were defined in the header.

## Features missing here that I think would be useful

These are some things I've considered implementing in `evmmax-bls12-381`.  Ordered by most to least important IMO:

1. a Module system to allow code-reuse.  The compilation process would take a dependency tree of templates, and create a symbol->register table that minimizes the overall number of values needed.
2. Support for multiple active moduli and their virtual register spaces (field contexts from the spec).
3. The ability to embed tables of precomputed constants in the code (in a data section with EOF).

## Known Bugs

* Do not invoke jumps or place jumpdests in the same macro/function as `ADDMODX`/`SUBMODX`/`MULMODX` opcodes, as this will corrupt Huff's calculation of jumpdest locations.
