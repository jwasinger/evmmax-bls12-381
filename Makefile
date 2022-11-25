.PHONY: build

build:
	rm -rf build
	mkdir -p build/src
	mkdir -p build/artifacts
	python3 gen_huff.py templates/g1mul.huff.template > build/src/g1mul.huff
	bash -c "./huff-rs/target/release/huffc --artifacts --bytecode build/src/modexp-exponent-hardcoded.huff | python3 strip_to_return.py > build/artifacts/modexp-exponent-hardcoded.hex"
	bash -c "./huff-rs/target/release/huffc --artifacts --bytecode build/src/modexp_1024.huff | python3 strip_to_return.py > build/artifacts/modexp_1024.hex"
	bash -c "./huff-rs/target/release/huffc --artifacts --bytecode build/src/modexp_2048.huff | python3 strip_to_return.py > build/artifacts/modexp_2048.hex"
	bash -c "./huff-rs/target/release/huffc --artifacts --bytecode build/src/modexp_4096.huff | python3 strip_to_return.py > build/artifacts/modexp_4096.hex"
