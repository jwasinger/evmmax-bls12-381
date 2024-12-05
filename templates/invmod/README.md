# invmod

This contains implementation of bls12381 modular inverse via fermat.  It uses the `addchain` tool to generate an optimal addchain for the exponentiation, and generates a code template from that output.

## Usage

Set up `addchain` tool:
```
git submodule update --init
(cd addchain/cmd/addchain && go build
```

Generate invmod contract:

Run `make invmod` from the top-level directory of this repository.
