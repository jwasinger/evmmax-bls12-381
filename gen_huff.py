import sys
import os
import math
from jinja2.nativetypes import NativeEnvironment

def wrap_directive(template_state, fn):
        def wrapped(*args, **kwargs):
            try:
                fn(*args, **kwargs)
                return ''
            except Exception as e:
                import pdb; pdb.set_trace()
                foo = 'bar'
        return wrapped

def wrap_emit(template_state, fn):
    def wrapped(*args, **kwargs):
        return template_state.emit_text(fn(*args, **kwargs))
    return wrapped

class TemplateState:
    def __init__(self, g2=False, slot_offset=0, mem_offset=0):
        if g2:
            self.item_size = 2
        else:
            self.item_size = 1

        self.inputs_done = False
        self.outputs_done = False
        self.free_input_idx = 0
        self.inputs_count = 0
        self.inputs = {}
        self.output_val_count = 0

        self.outputs = {}

        self.free_slot = slot_offset
        self.evmmax_slot_size = 48 # hardcode to bls for now
        self.allocs = {}
        self.mem_allocs = mem_offset
        self.free_mem = 0
        self.indent_lvl = 0
        self.indent_size = 4

        self.compiled_text = None

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
            'emit_load_items': wrap_emit(self, self.emit_load_items),
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
            'emit_evmmax_load_val': wrap_emit(self, self.emit_evmmax_load_val),
            'emit_slots_used': wrap_emit(self, self.emit_slots_used),
            'emit_slot': wrap_emit(self, self.emit_slot)
        }

    def load_module(self, module_name, inputs, outputs):
        # TODO: assert -> modules must be loaded after current module's inputs/outputs are declared
        # TODO make sure that module alloc-space starts at an offset based on the last free slot
        # TODO: map submodule inputs/outputs to current module scope
        submodule = TemplateState(g2=self.g2, slot_offset=self.free_slot, mem_offset=self.free_mem)
        env = NativeEnvironment()

        template_content = ""
        with open(os.path.join(os.getcwd(), "templates/modules/{}/module.huff".format(module_name))) as f:
            template_content = f.read()

        t = env.from_string(template_content)
        t.globals.update(template_state.get_stdlib())
        result = t.render(EVMMAX_VAL_SIZE=hex(48), AFFINE_POINT_SIZE=hex(template_state.item_size * 48 * 2), PROJ_POINT_SIZE=hex(template_state.item_size * 48 * 3), exponent_bits=exponent_bits)

        # TODO: do something with result
        pass

    def get_outputs_start_idx(self):
        return min([idx for _, idx in self.outputs.items()])

    def alloc_range(self, symbol, count):
        if symbol in self.allocs:
            raise Exception("symobol already allocated {}".format(symbol))

        self.inputs_done = True
        self.outputs_done = True

        self.allocs[symbol] = self.free_slot
        self.free_slot += count * self.item_size

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

    def alloc_output_f(self, symbol):
        self.inputs_done = True

        if self.outputs_done:
            raise Exception("output values must be allocated before other memory values")

        self.outputs[symbol] = self.free_slot
        self.allocs[symbol] = self.free_slot
        self.mem_allocs[symbol] = self.free_mem

        self.output_val_count += self.item_size

        self.free_mem += self.item_size * 48
        self.free_slot += self.item_size

    def alloc_input_val(self, symbol):
        if self.inputs_done:
            raise Exception("input values must be allocated before other memory value")
        self.inputs[symbol] = self.free_slot
        self.inputs_count += 1

        self.mem_allocs[symbol] = self.free_mem
        self.allocs[symbol] = self.free_slot
        self.free_slot += 1
        self.free_mem += 48

    def alloc_input_f(self, symbol):
        if self.inputs_done:
            raise Exception("input values must be allocated before other memory value")

        self.inputs[symbol] = self.free_slot
        self.inputs_count += self.item_size

        self.mem_allocs[symbol] = self.free_mem
        self.allocs[symbol] = self.free_slot
        self.free_slot += self.item_size
        self.free_mem += self.item_size * 48

    def emit_evmmax_store_inputs(self):
        res = [
           hex(self.inputs_count),
           '0x0', # inputs always start at offset 0 in memory 
           '0x0', # inputs always start at value index 0
           '0x0',
           'storex'
        ]
        return res

    def emit_evmmax_load_outputs(self):
        res = [
           hex(self.output_val_count),
           hex(self.get_outputs_start_idx()),
           hex(self.get_outputs_start_idx() * 48),
           '0x0',
           'loadx'
        ]
        return res

    def emit_evmmax_load_val(self, output_symbol, symbol):
        output_offset = self.mem_allocs[output_symbol]
        val_idx = self.allocs[symbol]
        res = [
           hex(1),
           hex(val_idx),
           hex(output_offset),
           '0x0',
           'loadx'
        ]
        return res

    def alloc_mem(self, symbol, size):
        if symbol in self.mem_allocs:
            raise Exception("symbol already allocated in memory {}".format(symbol))

        self.inputs_done = True
        self.mem_allocs[symbol] = self.free_mem
        self.free_mem += size

    def __emit_mem_offset(self, symbol, offset=0):
        return hex(self.mem_allocs[symbol] + offset)

    def emit_mem_offset(self, symbol, offset=0):
        return [hex(self.mem_allocs[symbol] + offset)]

    def alloc_f(self, symbol):
        if symbol in self.allocs:
            raise Exception("symobol already allocated {}".format(symbol))

        if symbol in self.inputs:
            raise Exception("symobol already allocated as input {}".format(symbol))

        self.allocs[symbol] = self.free_slot
        self.free_slot += self.item_size

    def alloc_val(self, symbol):
        if symbol in self.allocs:
            raise Exception("symobol already allocated {}".format(symbol))

        if symbol in self.inputs:
            raise Exception("symobol already allocated as input {}".format(symbol))

        self.allocs[symbol] = self.free_slot
        self.free_slot += 1

    def emit_slot(self, symbol):
        return [hex(self.allocs[symbol])]
        
    def emit_slots_used(self):
        return [hex(self.free_slot)]

    def ref_item(self, new_name, existing_name):
        old_slot = self.allocs[existing_name]
        self.allocs[new_name] = old_slot

    def start_block(self):
        self.indent_lvl += 1

    def end_block(self):
        if self.indent_lvl == 0:
            raise Exception("bad")
        self.indent_lvl -= 1

    def emit_fp_set_one(self, out):
        out_slot = self.allocs[out]

        return [
            self.__emit_addmodx(out_slot, self.allocs['ONE_VAL'], self.allocs['ZERO_VAL'])
        ]

    def emit_fp2_set_one(self, out):
        out_slot = self.allocs[out]

        return [
            self.__emit_addmodx(out_slot, self.allocs['ONE_VAL'], self.allocs['ZERO_VAL']),
            self.__emit_addmodx(out_slot + 1, self.allocs['ZERO_VAL'], self.allocs['ZERO_VAL'])
        ]

    def emit_f_set_one(self, out):
        if self.item_size == 1:
            return self.emit_fp_set_one(out)
        else:
            return self.emit_fp2_set_one(out)

    def emit_fp_set_zero(self, out):
        out_slot = self.allocs[out]

        return [
            self.__emit_addmodx(out_slot, self.allocs['ZERO_VAL'], self.allocs['ZERO_VAL'])
        ]


    def emit_fp2_set_zero(self, out):
        out_slot = self.allocs[out]

        return [
            self.__emit_addmodx(out_slot, self.allocs['ZERO_VAL'], self.allocs['ZERO_VAL']),
            self.__emit_addmodx(out_slot + 1, self.allocs['ZERO_VAL'], self.allocs['ZERO_VAL'])
        ]

    def emit_f_set_zero(self, out):
        if self.item_size == 1:
            return self.emit_fp_set_zero(out)
        else:
            return self.emit_fp2_set_zero(out)

    def __emit_mulmontx(self, out_slot, x_slot, y_slot):
        return "__mulmontx(s{},s{},s{})".format(out_slot, x_slot, y_slot)

    def __emit_addmodx(self, out_slot, x_slot, y_slot):
        return "__addmodx(s{},s{},s{})".format(out_slot, x_slot, y_slot)

    def __emit_submodx(self, out_slot, x_slot, y_slot):
        return "__submodx(s{},s{},s{})".format(out_slot, x_slot, y_slot)

    def emit_mulmontx(self, out, x, y):
        out_slot = self.allocs[out]
        x_slot = self.allocs[x]
        y_slot = self.allocs[y]
        return [self.__emit_mulmontx(out_slot, x_slot, y_slot)]

    def emit_addmodx(self, out, x, y):
        out_slot = self.allocs[out]
        x_slot = self.allocs[x]
        y_slot = self.allocs[y]
        return [self.__emit_addmodx(out_slot, x_slot, y_slot)]

    def emit_submodx(self, out, x, y):
        out_slot = self.allocs[out]
        x_slot = self.allocs[x]
        y_slot = self.allocs[y]
        return [self.__emit_submodx(out_slot, x_slot, y_slot)]

    def emit_f_copy(self, output_item, input_item):
        output_item_slot = self.allocs[output_item]
        input_item_slot = self.allocs[input_item]
        res = []
        for i in range(self.item_size):
            res.append(self.__emit_addmodx(output_item_slot + i, input_item_slot + i, self.allocs['ZERO_VAL']))
        return res

    def emit_fp2_add(self, out, x, y):
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
        if self.item_size == 1:
            return self.emit_addmodx(out, x, y)
        else:
            return self.emit_fp2_add(out, x, y)

    def emit_f_sqr(self, out, x):
        if self.item_size == 1:
            return self.emit_mulmontx(out, x, x)
        else:
            return self.emit_fp2_sqr(out, x)

    def emit_f_mul(self, out, x, y):
        if self.item_size == 1:
            return self.emit_mulmontx(out, x, y)
        else:
            return self.emit_fp2_mul(out, x, y)

    def emit_f_sub(self, out, x, y):
        if self.item_size == 1:
            return self.emit_submodx(out, x, y)
        else:
            return self.emit_fp2_sub(out, x, y)

    def emit_text(self, items):
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

    def emit_check_val_nonzero(self, item):
        if self.item_size == 1:
            return self.__emit_check_fp_nonzero(item)
        else:
            return self.__emit_check_fp2_nonzero(item)

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

    def emit_load_items(self):
        return [] 

    def emit_set_val_12_fq(self, output):
        output_offset = self.allocs[output] * self.evmmax_slot_size
        res = []

        res.append('0xc')
        res.append(hex(output_offset + 16))
        res.append('mstore')

        return res

    def emit_set_val_12(self, output):
        if self.item_size == 1:
            return self.emit_set_val_12_fq(output)
        else:
            return self.emit_set_val_12_fq2(output)

    # TODO change name to store_constant_at_slot_offset or something similar
    def emit_store_constant_32byte_aligned(self, output, val):
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

    exponent = 1
    exponent_bits = [int(digit) for digit in bin(exponent)[2:]]
    t = env.from_string(template_content)
    t.globals.update(template_state.get_stdlib())
    result = t.render(EVMMAX_VAL_SIZE=hex(48), AFFINE_POINT_SIZE=hex(template_state.item_size * 48 * 2), PROJ_POINT_SIZE=hex(template_state.item_size * 48 * 3), exponent_bits=exponent_bits)

    with open(os.path.join(os.getcwd(), sys.argv[2]), 'w') as f:
        f.write(result)

if __name__ == "__main__":
    main()
