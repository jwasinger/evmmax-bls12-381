.PHONY: build

build:
	rm -rf build
	mkdir -p build/src
	mkdir -p build/artifacts
	mkdir -p build/src/g1mul
	mkdir -p build/artifacts/g1mul
	python3 gen_huff.py templates/g1mul/g1mul_dbl_and_add.huff.template build/src/g1mul/g1mul_dbl_and_add.huff
	bash -c "./huff-rs/target/release/huffc --artifacts --bytecode build/src/g1mul/g1mul_dbl_and_add.huff | python3 strip_to_return.py > build/artifacts/g1mul/g1mul_dbl_and_add.hex"
