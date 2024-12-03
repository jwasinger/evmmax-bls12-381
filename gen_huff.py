import sys
import os
import math
from jinja2.nativetypes import NativeEnvironment

def wrap_directive(template_state, fn):
        def wrapped(*args, **kwargs):
            fn(*args, **kwargs)
            return ''
        return wrapped

def wrap_emit(template_state, fn):
    def wrapped(*args, **kwargs):
        return template_state.emit_text(fn(*args, **kwargs))
    return wrapped

# TemplateState represents the 
class TemplateState:
    def __init__(self, g2=False):
        if g2:
            self.field_elt_size = 2
        else:
            self.field_elt_size = 1

        # flags used during header parsing
        self.inputs_done = False
        self.outputs_done = False

        # the next free register not assigned to an input symbol
        self.free_input_idx = 0

        self.inputs_count = 0

        # map of symbol to the 1st virtual register in the range that it refers to
        self.inputs = {}

        self.output_val_count = 0

        # map of symbol to the 1st virtual register in the range that it refers to
        self.outputs = {}

        # the next free register not assigned to an input symbol
        self.free_slot = 0

        # virtual register size in bytes, hardcoded to bls12381 base field for now
        self.evmmax_slot_size = 48 # hardcode to bls for now

        # map of symbol to the 1st virtual register in the range that it refers to
        self.allocs = {}

        # map of symbol name (input or output) to a memory offset.
        # inputs are loaded from the specified offset.
        # outputs are stored to the specified offset.
        self.mem_allocs = {}
        self.free_mem = 0

        # these are for formatting the resulting Huff code for readability.
        self.indent_lvl = 0
        self.indent_size = 4

    # get_stdlib returns a map of functions available to templates
    def get_stdlib(self):
        return {
            'alloc_range': wrap_directive(self, self.alloc_range),
            'alloc_val': wrap_directive(self, self.alloc_val),
            'alloc_input_val': wrap_directive(self, self.alloc_input_val),
            'alloc_output_val': wrap_directive(self, self.alloc_output_val),
            'alloc_input_f': wrap_directive(self, self.alloc_input_f),
            'alloc_output_f': wrap_directive(self, self.alloc_output_f),
            'start_block': wrap_directive(self, self.start_block),
            'end_block': wrap_directive(self, self.end_block),
            'ref_item': wrap_directive(self, self.ref_item),
            'alloc_f': wrap_directive(self, self.alloc_f),
            'alloc_mem': wrap_directive(self, self.alloc_mem),
            'emit_f_copy': wrap_emit(self, self.emit_f_copy),
            'emit_mulmontx': wrap_emit(self, self.emit_mulmontx),
            'emit_f_mul': wrap_emit(self, self.emit_f_mul),
            'emit_f_sqr': wrap_emit(self, self.emit_f_sqr),
            'emit_f_add': wrap_emit(self, self.emit_f_add),
            'emit_f_sub': wrap_emit(self, self.emit_f_sub), 
            'emit_mem_offset': wrap_emit(self, self.emit_mem_offset),
            'emit_f_set_one': wrap_emit(self, self.emit_f_set_one),
            'emit_f_set_zero': wrap_emit(self, self.emit_f_set_zero),
            'emit_f_copy': wrap_emit(self, self.emit_f_copy),
            'emit_set_val_12': wrap_emit(self, self.emit_set_val_12),
            'emit_store_constant_32byte_aligned': wrap_emit(self, self.emit_store_constant_32byte_aligned),
            'emit_check_val_nonzero': wrap_emit(self, self.emit_check_val_nonzero),
            'emit_evmmax_store_inputs': wrap_emit(self, self.emit_evmmax_store_inputs),
            'emit_evmmax_load_outputs': wrap_emit(self, self.emit_evmmax_load_outputs),
            'emit_num_slots_used': wrap_emit(self, self.emit_num_slots_used),
            'emit_slot': wrap_emit(self, self.emit_slot)
        }

    def get_outputs_start_register(self):
        return min([idx for _, idx in self.outputs.items()])

    # alloc_range allocates a range of register for internal value 'symbol' to own.
    def alloc_range(self, symbol, count):
        if symbol in self.allocs:
            raise Exception("symobol already allocated {}".format(symbol))

        self.inputs_done = True
        self.outputs_done = True

        self.allocs[symbol] = self.free_slot
        self.free_slot += count * self.field_elt_size

    # alloc_output_val allocates a single register for 'symbol' to own.
    def alloc_output_val(self, symbol):
        self.inputs_done = True

        if self.outputs_done:
            raise Exception("output values must be allocated before other memory values")

        self.outputs[symbol] = self.free_slot
        self.allocs[symbol] = self.free_slot
        self.mem_allocs[symbol] = self.free_mem

        self.output_val_count += 1

        self.free_mem += 48
        self.free_slot += 1

    # allocate_output_f allocates one or more registers to hold an input field element.
    # the size depends on whether the field in question is the base field or 
    # an extension field (in the case of G2).
    def alloc_output_f(self, symbol):
        self.inputs_done = True

        if self.outputs_done:
            raise Exception("output values must be allocated before other memory values")

        self.outputs[symbol] = self.free_slot
        self.allocs[symbol] = self.free_slot
        self.mem_allocs[symbol] = self.free_mem

        self.output_val_count += self.field_elt_size

        self.free_mem += self.field_elt_size * 48
        self.free_slot += self.field_elt_size

    # alloc_input_val allocates a single virtual register associating it with 'symbol'
    # in the symbol table.
    def alloc_input_val(self, symbol):
        if self.inputs_done:
            raise Exception("input values must be allocated before other memory value")
        self.inputs[symbol] = self.free_slot
        self.inputs_count += 1

        self.mem_allocs[symbol] = self.free_mem
        self.allocs[symbol] = self.free_slot
        self.free_slot += 1
        self.free_mem += 48

    # allocate_input_f allocates one or more registers to hold an output field element.
    # the size depends on whether the field in question is the base field or 
    # an extension field (in the case of G2).
    def alloc_input_f(self, symbol):
        if self.inputs_done:
            raise Exception("input values must be allocated before other memory value")

        self.inputs[symbol] = self.free_slot
        self.inputs_count += self.field_elt_size

        self.mem_allocs[symbol] = self.free_mem
        self.allocs[symbol] = self.free_slot
        self.free_slot += self.field_elt_size
        self.free_mem += self.field_elt_size * 48

    # emit_evmmax_store_inputs returns lines of Huff code to store all inputs into
    # their assigned registers from EVM memory starting at offset 0.
    def emit_evmmax_store_inputs(self) -> [str]:
        res = [
           hex(self.inputs_count),
           '0x0', # inputs always start at offset 0 in memory 
           '0x0', # inputs always start at value index 0
           'storex'
        ]
        return res

    # emit_evmmax_load_outputs returns lines of Huff code to load all outputs from 
    # their assigned registers into EVM memory.
    def emit_evmmax_load_outputs(self) -> [str]:

        res = [
           hex(self.output_val_count),
           hex(self.get_outputs_start_register()),
           hex(self.get_outputs_start_register() * 48),
           'loadx'
        ]
        return res

    # alloc_mem assigns a contiguous range of memory of size 'size' bytes to the symbol name.
    def alloc_mem(self, symbol, size):
        if symbol in self.mem_allocs:
            raise Exception("symbol already allocated in memory {}".format(symbol))

        self.inputs_done = True
        self.mem_allocs[symbol] = self.free_mem
        self.free_mem += size

    def __emit_mem_offset(self, symbol, offset=0):
        return hex(self.mem_allocs[symbol] + offset)

    # emit_mem_offset returns the hex literal of the first byte in the memory
    # segment referenced by the symbol, with an optional offset to add to that
    # value
    def emit_mem_offset(self, symbol, offset=0) -> [str]:
        return [hex(self.mem_allocs[symbol] + offset)]

    # alloc_f maps a symbol to the next available slot(s) (depending on whether g1/g2 is
    # configured).  These will contain a field element.
    def alloc_f(self, symbol):
        if symbol in self.allocs:
            raise Exception("symobol already allocated {}".format(symbol))

        if symbol in self.inputs:
            raise Exception("symobol already allocated as input {}".format(symbol))

        self.allocs[symbol] = self.free_slot
        self.free_slot += self.field_elt_size

    # alloc_val maps a symbol to the next available free slot.
    def alloc_val(self, symbol):
        if symbol in self.allocs:
            raise Exception("symobol already allocated {}".format(symbol))

        if symbol in self.inputs:
            raise Exception("symobol already allocated as input {}".format(symbol))

        self.allocs[symbol] = self.free_slot
        self.free_slot += 1

    # emit_slot returns the first slot mapped to a symbol represented as
    # an array containing a single hex-literal 
    def emit_slot(self, symbol) -> [str]:
        return [hex(self.allocs[symbol])]
        
    # emit_num_slots_used returns the amount of allocated slots in the symbol table 
    # represented as an array containing a single string hex literal.
    def emit_num_slots_used(self) -> [str]:
        return [hex(self.free_slot)]

    # ref_item creates an alias to an existing symbol in the table, without
    # allocating any new slots.
    def ref_item(self, new_name: str, existing_name: str):
        old_slot = self.allocs[existing_name]
        self.allocs[new_name] = old_slot

    # start_block should be called on the beginning of every Huff code block
    # to ensure that template generation generates properly-indented code
    def start_block(self):
        self.indent_lvl += 1

    # end_block should be called at the end of every Huff code block to ensure
    # that template generation generations peroply-indented code.
    def end_block(self):
        if self.indent_lvl == 0:
            raise Exception("bad")
        self.indent_lvl -= 1

    # emit_fp_set_one returns Huff code for a single call to 'addmodx' which 
    # assigns the value 1 to the register corresponding to the symbol 'out'
    def emit_fp_set_one(self, out: str) -> [str]:
        out_slot = self.allocs[out]

        return [
            self.__emit_addmodx(out_slot, self.allocs['ONE_VAL'], self.allocs['ZERO_VAL'])
        ]

    # emit_fp2_set_one returns huff code  to set the field extension element referenced by 
    # symbol 'out' to one.
    def emit_fp2_set_one(self, out: str) -> str:
        out_slot = self.allocs[out]

        return [
            self.__emit_addmodx(out_slot, self.allocs['ONE_VAL'], self.allocs['ZERO_VAL']),
            self.__emit_addmodx(out_slot + 1, self.allocs['ZERO_VAL'], self.allocs['ZERO_VAL'])
        ]

    # emit_f_set_one returns Huff code to set a field element referenced by symbol 'out'
    # to the value 1.
    def emit_f_set_one(self, out: str) -> [str]:
        if self.field_elt_size == 1:
            return self.emit_fp_set_one(out)
        else:
            return self.emit_fp2_set_one(out)

    # emit_f_set_zero returns Huff code to set a field element referenced by symbol 'out'
    # to the value 1.
    def emit_fp_set_zero(self, out) -> [str]:
        out_slot = self.allocs[out]

        return [
            self.__emit_addmodx(out_slot, self.allocs['ZERO_VAL'], self.allocs['ZERO_VAL'])
        ]


    # emit_fp2_set_zero returns Huff code to set the field extension element referenced by 
    # symbol 'out' to 0.
    def emit_fp2_set_zero(self, out: str) -> [str]:
        out_slot = self.allocs[out]

        return [
            self.__emit_addmodx(out_slot, self.allocs['ZERO_VAL'], self.allocs['ZERO_VAL']),
            self.__emit_addmodx(out_slot + 1, self.allocs['ZERO_VAL'], self.allocs['ZERO_VAL'])
        ]

    # emit_f_set_one returns Huff code to set a field element referenced by symbol 'out'
    # to the value 0.
    def emit_f_set_zero(self, out: str) -> [str]:
        if self.field_elt_size == 1:
            return self.emit_fp_set_zero(out)
        else:
            return self.emit_fp2_set_zero(out)

    def __emit_mulmontx(self, out_slot, x_slot, y_slot):
        return "__mulmontx(s{},s1,s{},s1,s{},s1,s1)".format(out_slot, x_slot, y_slot)

    def __emit_addmodx(self, out_slot, x_slot, y_slot):
        return "__addmodx(s{},s1,s{},s1,s{},s1,s1)".format(out_slot, x_slot, y_slot)

    def __emit_submodx(self, out_slot, x_slot, y_slot):
        return "__submodx(s{},s1,s{},s1,s{},s1,s1)".format(out_slot, x_slot, y_slot)

    # emit_mulmontx returns Huff code for a single call to the MULMODX opcode
    # with inputs as virtual register indices.
    # 
    # stride and count inputs take the value 1.
    def emit_mulmontx(self, out: int, x: int, y: int) -> [str]:
        out_slot = self.allocs[out]
        x_slot = self.allocs[x]
        y_slot = self.allocs[y]
        return [self.__emit_mulmontx(out_slot, x_slot, y_slot)]

    # emit_mulmontx returns Huff code for a single call to the ADDMODX opcode
    # with inputs as virtual register indices.
    # 
    # stride and count inputs take the value 1.
    def emit_addmodx(self, out: int, x: int, y: int) -> [str]:
        out_slot = self.allocs[out]
        x_slot = self.allocs[x]
        y_slot = self.allocs[y]
        return [self.__emit_addmodx(out_slot, x_slot, y_slot)]

    # emit_mulmontx returns Huff code for a single call to the SUBMODX opcode
    # with inputs as virtual register indices.
    # 
    # stride and count inputs take the value 1.
    def emit_submodx(self, out: int, x: int, y: int) -> [str]:
        out_slot = self.allocs[out]
        x_slot = self.allocs[x]
        y_slot = self.allocs[y]
        return [self.__emit_submodx(out_slot, x_slot, y_slot)]

    # emit_f_copy returns the Huff code necessary to copy a field element
    # from from the register(s) referenced by input_item to those referenced
    # by output_item.  The inputs and outputs cannot overlap.
    def emit_f_copy(self, output_item: str, input_item: str):
        output_item_slot = self.allocs[output_item]
        input_item_slot = self.allocs[input_item]
        res = []
        for i in range(self.field_elt_size):
            res.append(self.__emit_addmodx(output_item_slot + i, input_item_slot + i, self.allocs['ZERO_VAL']))
        return res

    def emit_fp2_add(self, out: str, x: str, y: str) -> [str]:
        out_slot = self.allocs[out]
        x_slot = self.allocs[x]
        y_slot = self.allocs[y]

        res = [
            self.__emit_addmodx(out_slot, x_slot, y_slot),
            self.__emit_addmodx(out_slot + 1, x_slot + 1, y_slot + 1)
        ]
        return res

    def emit_fp2_sub(self, out, x, y):
        out_slot = self.allocs[out]
        x_slot = self.allocs[x]
        y_slot = self.allocs[y]

        res = [
            self.__emit_submodx(out_slot, x_slot, y_slot),
            self.__emit_submodx(out_slot + 1, x_slot + 1, y_slot + 1)
        ]
        return res

    def emit_fp2_sqr(self, out, x):
        out_slot_0 = self.allocs[out]
        out_slot_1 = out_slot_0 + 1
        x_slot_0 = self.allocs[x]
        x_slot_1 = x_slot_0 + 1

        if out_slot_0 == x_slot_0:
            # TODO support this
            raise Exception("untested input configuration")

        res = [
            # out[0] <- (x[0] + x[1]) * (x[0] - x[1])
            self.__emit_addmodx(out_slot_1, x_slot_0, x_slot_1),
            self.__emit_submodx(out_slot_0, x_slot_0, x_slot_1),
            self.__emit_mulmontx(out_slot_0, out_slot_0, out_slot_1),
            # out[1] <- 2 * x[0] * x[1]
            self.__emit_mulmontx(out_slot_1, x_slot_0, x_slot_1),
            self.__emit_addmodx(out_slot_1, out_slot_1, out_slot_1)
        ]
        return res

    def emit_fp2_mul(self, out, x, y):
        out_slot_0 = self.allocs[out]
        out_slot_1 = out_slot_0 + 1
        x_slot_0 = self.allocs[x]
        x_slot_1 = x_slot_0 + 1
        y_slot_0 = self.allocs[y]
        y_slot_1 = y_slot_0 + 1

        t0 = self.allocs['FP2_TEMP0']
        t1 = self.allocs['FP2_TEMP1']
        t2 = self.allocs['FP2_TEMP2']
        t3 = self.allocs['FP2_TEMP3']

        res = [
            # out[0] <- x[0] * y[0] - x[1] * y[1]
            # out[1] <- x[0] * y[1] + x[1] * y[0]

            self.__emit_mulmontx(t0, x_slot_0, y_slot_0),
            self.__emit_mulmontx(t1, x_slot_1, y_slot_1),
            self.__emit_mulmontx(t2, x_slot_0, y_slot_1),
            self.__emit_mulmontx(t3, x_slot_1, y_slot_0),
            self.__emit_submodx(out_slot_0, t0, t1),
            self.__emit_addmodx(out_slot_1, t2, t3)
        ]
        return res

    def emit_f_add(self, out, x, y):
        if self.field_elt_size == 1:
            return self.emit_addmodx(out, x, y)
        else:
            return self.emit_fp2_add(out, x, y)

    def emit_f_sqr(self, out, x):
        if self.field_elt_size == 1:
            return self.emit_mulmontx(out, x, x)
        else:
            return self.emit_fp2_sqr(out, x)

    def emit_f_mul(self, out, x, y):
        if self.field_elt_size == 1:
            return self.emit_mulmontx(out, x, y)
        else:
            return self.emit_fp2_mul(out, x, y)

    def emit_f_sub(self, out, x, y):
        if self.field_elt_size == 1:
            return self.emit_submodx(out, x, y)
        else:
            return self.emit_fp2_sub(out, x, y)

    # emit_text takes a set of lines of Huff code and outputs them as a single string.
    def emit_text(self, items: [str]) -> str:
        res = []
        for i, item in enumerate(items):
            if i == 0:
                res.append(item + '\n')
            else:
                res.append(self.indent_lvl * self.indent_size * ' ' + item + '\n')

        res += ' ' * self.indent_lvl * self.indent_size

        return ''.join(res)

    def __emit_check_fp2_nonzero(self, item):
        res = [
            self.__emit_mem_offset(item),
            'mload',
            self.__emit_mem_offset(item, offset=32),
            'mload',
            '0xffffffffffffffffffffffffffffffff00000000000000000000000000000000',
            'and',
            'or',
            self.__emit_mem_offset(item),
            'mload',
            self.__emit_mem_offset(item, offset=32),
            'mload',
            '0xffffffffffffffffffffffffffffffff00000000000000000000000000000000',
            'and',
            'or',
            'or'
            ]

        return res

    def __emit_check_fp_nonzero(self, item):
        res = [
            self.__emit_mem_offset(item),
            'mload',
            self.__emit_mem_offset(item, offset=32),
            'mload',
            '0xffffffffffffffffffffffffffffffff00000000000000000000000000000000',
            'and',
            'or'
            ]

        return res

    # emit_check_val returns huff code to check whether an field element
    # referenced by a symbol is nonzero
    def emit_check_val_nonzero(self, item: str) -> [str]:
        if self.field_elt_size == 1:
            return self.__emit_check_fp_nonzero(item)
        else:
            return self.__emit_check_fp2_nonzero(item)

    # emit_set_val_12_fq2 returns Huff code to set the extension field element
    # referenced by the symbol 'output' to 12.
    def emit_set_val_12_fq2(self, output):
        output_offset = self.allocs[output] * self.evmmax_slot_size
        res = []

        res.append('0xc')
        res.append(hex(output_offset + 16))
        res.append('mstore')
        res.append('0xc')
        res.append(hex(output_offset + 48 + 16))
        res.append('mstore')

        return res

    # emit_set_val_12_fq2 returns Huff code to set the non-extension field element
    # referenced by the symbol 'output' to 12.
    def emit_set_val_12_fq(self, output):
        output_offset = self.allocs[output] * self.evmmax_slot_size
        res = []

        res.append('0xc')
        res.append(hex(output_offset + 16))
        res.append('mstore')

        return res

    # emit_set_val_12_fq2 returns Huff code to set the field element
    # referenced by the symbol 'output' to 12.
    def emit_set_val_12(self, output):
        if self.field_elt_size == 1:
            return self.emit_set_val_12_fq(output)
        else:
            return self.emit_set_val_12_fq2(output)

    # emit_store_constant_32byte_aligned returns the huff code to store a literal unsigned integer
    # value starting at the memory offset referenced by symbol 'output',
    # padding the memory written to be 32byte-aligned:  padding the start of the output offset with
    # zeroes.
    def emit_store_constant_32byte_aligned(self, output: str, val: int) -> [str]:
        output_offset = self.mem_allocs[output]
        res = []
        val_hex = hex(val)[2:]

        if len(val_hex) <= 64:
            res.append("0x"+val_hex[:])
            res.append(hex(output_offset + 16))
            res.append("mstore")
            return res

        for i in range(0, math.ceil(len(val_hex) / 64)):
            if (i + 1) * 64 > len(val_hex):
                pad_len = (i + 1) * 64 - len(val_hex)
                res.append("0x"+val_hex[i*64:] + '0' * pad_len)
                res.append(hex(output_offset + i * 32))
                res.append("mstore")
            else:
                res.append("0x"+val_hex[i*64:(i+1)*64])
                res.append(hex(output_offset + i * 32))
                res.append("mstore")

        return res

def main():
    template_state = None
    if len(sys.argv) != 4:
        raise Exception("bad argument count")

    if sys.argv[3] == 'G1':
        template_state = TemplateState()
    else:
        template_state = TemplateState(g2=True)

    env = NativeEnvironment()

    template_content = ""
    with open(os.path.join(os.getcwd(),sys.argv[1])) as f:
        template_content = f.read()

    t = env.from_string(template_content)
    t.globals.update(template_state.get_stdlib())
    result = t.render(EVMMAX_VAL_SIZE=hex(48), AFFINE_POINT_SIZE=hex(template_state.field_elt_size * 48 * 2), PROJ_POINT_SIZE=hex(template_state.field_elt_size * 48 * 3))

    with open(os.path.join(os.getcwd(), sys.argv[2]), 'w') as f:
        f.write(result)

if __name__ == "__main__":
    main()
