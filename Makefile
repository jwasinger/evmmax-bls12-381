.PHONY: build

all: init g2

init:
	rm -rf build
	mkdir -p build/src
	mkdir -p build/artifacts
	mkdir -p build/src/ecmul
	mkdir -p build/artifacts/ecmul

g1:
	python3 gen_huff.py templates/ecmul/ecmul_dbl_and_add.huff.template build/src/g1mul_dbl_and_add.huff G1
	bash -c "./huff-rs/target/release/huffc --artifacts --bytecode build/src/g1mul_dbl_and_add.huff > build/artifacts/ecmul/g1mul_dbl_and_add.hex"

g2:
	python3 gen_huff.py templates/ecmul/ecmul_dbl_and_add.huff.template build/src/g2mul_dbl_and_add.huff G2
	bash -c "./huff-rs/target/release/huffc --artifacts --bytecode build/src/g2mul_dbl_and_add.huff > build/artifacts/ecmul/g2mul_dbl_and_add.hex"
