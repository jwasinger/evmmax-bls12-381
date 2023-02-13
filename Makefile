.PHONY: build

all: init g1 g2 invmod

init:
	rm -rf build
	mkdir -p build/src
	mkdir -p build/artifacts
	mkdir -p build/src/ecmul
	mkdir -p build/artifacts/ecmul
	mkdir -p build/src/invmod
	mkdir -p build/artifacts/invmod

g1:
	#python3 gen_huff.py templates/ecmul/ecmul_dbl_and_add.huff.template build/src/g1mul_dbl_and_add.huff G1
	#bash -c "./huff-rs/target/release/huffc --artifacts --bytecode build/src/g1mul_dbl_and_add.huff > build/artifacts/ecmul/g1mul_dbl_and_add.hex"

g2:
	#python3 gen_huff.py templates/ecmul/ecmul_dbl_and_add.huff.template build/src/ecmul/g2mul_dbl_and_add.huff G2
	#bash -c "./huff-rs/target/release/huffc --artifacts --bytecode build/src/ecmul/g2mul_dbl_and_add.huff > build/artifacts/ecmul/g2mul_dbl_and_add.hex"
invmod:
	python3 gen_huff.py templates/invmod/invmod.huff.template build/src/invmod/invmod.huff G1
	bash -c "./huff-rs/target/release/huffc --artifacts --bytecode build/src/invmod/invmod.huff > build/artifacts/invmod/invmod.hex"
