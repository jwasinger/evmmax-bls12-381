.PHONY: build

build:
	rm -rf build
	mkdir -p build/src
	mkdir -p build/artifacts
	python3 gen_huff.py templates/g1mul.huff.template > build/src/g1mul.huff
	bash -c "./huff-rs/target/release/huffc --artifacts --bytecode build/src/modexp-exponent-hardcoded.huff | python3 strip_to_return.py > build/artifacts/g1mul.hex"
