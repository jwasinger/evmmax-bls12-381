import sys
import os
import math
from jinja2.nativetypes import NativeEnvironment

class TemplateState:
    def __init__(self, g2=False):
        if g2:
            self.item_size = 2
        else:
            self.item_size = 1

        self.alloc_inputs_done = False
        self.free_input_idx = 0
        self.num_inputs = 0
        self.free_slot = 0
        self.evmmax_slot_size = 48 # hardcode to bls for now
        self.allocs = {}
        self.indent_lvl = 0
        self.indent_size = 4

    def alloc_range(self, symbol, count):
        if symbol in self.allocs:
            raise Exception("symobol already allocated {}".format(symbol))

        #import pdb; pdb.set_trace()
        self.allocs[symbol] = self.free_slot
        self.free_slot += count * self.item_size

    def alloc_input(self, symbol):
        self.inputs[symbol] = self.free_input_free_input_idx
        self.free_input_idx += self.item_size

    def emit_evmmax_store_inputs(self):
        res = [
           '0x0',
           '0x0', 
           '0x0',
           hex(self.free_input_idx),
           'storex'
        ]
        return res

    def alloc_val(self, symbol):
        if symbol in self.allocs:
            raise Exception("symobol already allocated {}".format(symbol))

        self.allocs[symbol] = self.free_slot
        self.free_slot += 1

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
        return self.__emit_mulmontx(out_slot, x_slot, y_slot)

    def emit_addmodx(self, out, x, y):
        out_slot = self.allocs[out]
        x_slot = self.allocs[x]
        y_slot = self.allocs[y]
        return self.__emit_addmodx(out_slot, x_slot, y_slot)

    def emit_submodx(self, out, x, y):
        out_slot = self.allocs[out]
        x_slot = self.allocs[x]
        y_slot = self.allocs[y]
        return self.__emit_submodx(out_slot, x_slot, y_slot)

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
            return [self.emit_addmodx(out, x, y)]
        else:
            return self.emit_fp2_add(out, x, y)

    def emit_f_sqr(self, out, x):
        if self.item_size == 1:
            return [self.emit_mulmontx(out, x, x)]
        else:
            return self.emit_fp2_sqr(out, x)

    def emit_f_mul(self, out, x, y):
        if self.item_size == 1:
            return [self.emit_mulmontx(out, x, y)]
        else:
            return self.emit_fp2_mul(out, x, y)

    def emit_f_sub(self, out, x, y):
        if self.item_size == 1:
            return [self.emit_submodx(out, x, y)]
        else:
            return self.emit_fp2_sub(out, x, y)

    def emit_slot_mem_offset(self, slot, offset=0, newline=True):
        return hex(self.evmmax_mem_start + self.evmmax_slot_size * slot + offset)

    def emit_text(self, items):
        res = []
        for i, item in enumerate(items):
            if i == 0:
                res.append(item + '\n')
            else:
                res.append(self.indent_lvl * self.indent_size * ' ' + item + '\n')

        res += ' ' * self.indent_lvl * self.indent_size

        return ''.join(res)

    def emit_mem_offset(self, slot, offset=0):
        return hex(self.evmmax_mem_start + self.allocs[slot] * self.evmmax_slot_size  + offset)

    def emit_load_input_vals(self):
        res = []

        for i in range(0, self.item_size):
            res.append(hex(self.evmmax_mem_start + self.allocs[item] * self.evmmax_slot_size + i * self.evmmax_slot_size))
            res.append('dup1')
            res.append('tomontx')

        return res
    
    def __emit_check_fp2_nonzero(self, item):
        res = [
            self.emit_mem_offset(item),
            'mload',
            self.emit_mem_offset(item, offset=32),
            'mload',
            '0xffffffffffffffffffffffffffffffff00000000000000000000000000000000',
            'and',
            'or',
            self.emit_mem_offset(item),
            'mload',
            self.emit_mem_offset(item, offset=32),
            'mload',
            '0xffffffffffffffffffffffffffffffff00000000000000000000000000000000',
            'and',
            'or',
            'or'
            ]

        return res

    def __emit_check_fp_nonzero(self, item):
        res = [
            self.emit_mem_offset(item),
            'mload',
            self.emit_mem_offset(item, offset=32),
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
        output_offset = self.evmmax_mem_start + self.allocs[output] * self.evmmax_slot_size
        res = []

        res.append('0xc')
        res.append(hex(output_offset + 16))
        res.append('mstore')
        res.append('0xc')
        res.append(hex(output_offset + 48 + 16))
        res.append('mstore')

        return res

    def emit_set_val_12_fq(self, output):
        output_offset = self.evmmax_mem_start + self.allocs[output] * self.evmmax_slot_size
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
        output_offset = self.evmmax_mem_start + self.allocs[output] * self.evmmax_slot_size
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

template_state = None

def start_block():
    global template_state
    template_state.start_block()
    return ''

def emit_load_items(item):
    global template_state
    return template_state.emit_text(template_state.emit_load_items(item))

def emit_slots_used():
    global template_state
    return template_state.emit_text(template_state.emit_slots_used())

def end_block():
    global template_state
    template_state.end_block()
    return ''

def emit_mem_offset(item, offset=0):
    global template_state
    return template_state.emit_text([template_state.emit_mem_offset(item, offset=offset)])

def emit_store_constant_32byte_aligned(offset, val):
    global template_state
    return template_state.emit_text(template_state.emit_store_constant_32byte_aligned(offset, val))

def emit_mulmontx(output, inp1, inp2) -> str:
    global template_state
    return template_state.emit_text(template_state.emit_mulmontx(output, inp1, inp2))

def emit_f_copy(out, inp) -> str:
    global template_state
    return template_state.emit_text(template_state.emit_f_copy(out, inp))

def emit_f_add(out, x, y) -> str:
    global template_state
    return template_state.emit_text(template_state.emit_f_add(out, x, y))

def emit_f_sub(out, x, y) -> str:
    global template_state
    return template_state.emit_text(template_state.emit_f_sub(out, x, y))

def emit_mulmontx(out, x, y) -> str:
    global template_state
    return template_state.emit_text([template_state.emit_mulmontx(out, x, y)])

def emit_f_mul(out, x, y) -> str:
    global template_state
    return template_state.emit_text(template_state.emit_f_mul(out, x, y))

def emit_f_sqr(out, x) -> str:
    global template_state
    return template_state.emit_text(template_state.emit_f_mul(out, x, x))

def emit_f_set_one(out) -> str:
    global template_state
    return template_state.emit_text(template_state.emit_f_set_one(out))

def emit_f_set_zero(out) -> str:
    global template_state
    return template_state.emit_text(template_state.emit_f_set_zero(out))

def alloc_input(symbol, count):
    pass

def alloc_range(symbol, count):
    global template_state

    template_state.alloc_range(symbol, count)
    return ''

def alloc_val(symbol):
    global template_state

    template_state.alloc_val(symbol)
    return ''

def emit_check_val_nonzero(val):
    global template_state
    return template_state.emit_text(template_state.emit_check_val_nonzero(val))

def ref_item(new_name, old_name):
    global template_state
    template_state.ref_item(new_name, old_name)
    return ''

def emit_set_val_12(output):
    global template_state
    return template_state.emit_text(template_state.emit_set_val_12(output))

func_dict = {
    'alloc_range': alloc_range,
    'alloc_val': alloc_val,
    'start_block': start_block,
    'end_block': end_block,
    'ref_item': ref_item,
    'emit_load_items': emit_load_items,
    'emit_f_copy': emit_f_copy,
    'emit_mulmontx': emit_mulmontx,
    'emit_f_mul': emit_f_mul,
    'emit_f_sqr': emit_f_sqr,
    'emit_f_add': emit_f_add,
    'emit_f_sub': emit_f_sub, 
    'emit_mem_offset': emit_mem_offset,
    'emit_f_set_one': emit_f_set_one,
    'emit_f_set_zero': emit_f_set_zero,
    'emit_f_copy': emit_f_copy,
    'emit_set_val_12': emit_set_val_12,
    'emit_store_constant_32byte_aligned': emit_store_constant_32byte_aligned,
    'emit_check_val_nonzero': emit_check_val_nonzero,
    'emit_slots_used': emit_slots_used,
}

def main():
    global template_state
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
    t.globals.update(func_dict)
    result = t.render(AFFINE_POINT_SIZE=hex(template_state.item_size * 48 * 2), PROJ_POINT_SIZE=hex(template_state.item_size * 48 * 3), exponent_bits=exponent_bits, template_state=template_state)

    with open(os.path.join(os.getcwd(), sys.argv[2]), 'w') as f:
        f.write(result)

if __name__ == "__main__":
    main()
