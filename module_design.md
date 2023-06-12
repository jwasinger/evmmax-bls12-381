# Definitions

* modulus_id: lexographic identifier for a given modulus
* evmmax symbol: a lexographic identifier corresponding to `(modulus_id, slot_offset, slots_used)`
* memory symbol: a lexographic identifier corresponding to `(memory_offset, mem_size)`

# Conventions

## Reserved Slots

0 - always set to zero
1 - always set to 1

## Modules

# Module Structure

* Modules specify a list of exported functions accessible to the parent scope.
* Module exports specify inputs (symbols) which are imported from the parent context and outputs which are exported to the parent context.

## Module Function Invocation

* copy inputs from invoker slots to module slots, perform computation, copy outputs to invoker output slots

## Module Structure overview

1) import dependency modules
2) declare export symbols
3) declare export functions
4) declare internal symbols
5) function definitions
6) (TODO) ability to embed constants directly into bytecode

### Random module notes

* functions (exported/private) which expect internal values to be zero should explitly zero them: slots may have garbage values from previous operations

# Open Questions

* what happens when I import a module twice with different moduli: `ecmul(BLS12_381)` and `ecmul(XYZ)` in the same contract?
	* the `ecmul` contract should exist twice in the produced bytecode
