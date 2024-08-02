import sys
import os
import math
import yaml

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
    def __init__(self, g2=False):
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

        self.free_slot = 0
        self.field_width = 48 # hardcode to bls for now
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
            'emit_mulmodx': wrap_emit(self, self.emit_mulmodx),
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
            'emit_storex_inputs': wrap_emit(self, self.emit_storex_inputs),
            'emit_loadx_outputs': wrap_emit(self, self.emit_loadx_outputs),
            'emit_loadx_val': wrap_emit(self, self.emit_loadx_val),
            'emit_slots_used': wrap_emit(self, self.emit_slots_used),
            'emit_slot': wrap_emit(self, self.emit_slot)
        }

    def emit_storex_inputs(self):
        res = [
           hex(self.inputs_count),
           '0x0', # inputs always start at offset 0 in memory 
           '0x0', # inputs always start at value index 0
           'storex'
        ]
        return res

    def emit_loadx_outputs(self):
        res = [
           hex(self.output_val_count),
           hex(self.get_outputs_start_idx()),
           hex(self.get_outputs_start_idx() * 48),
           'loadx'
        ]
        return res

    def emit_loadx_val(self, output_symbol, symbol):
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

    def __emit_mulmodx(self, out_slot, x_slot, y_slot):
        return "__mulmontx(s{},s{},s{})".format(out_slot, x_slot, y_slot)

    def __emit_addmodx(self, out_slot, x_slot, y_slot):
        return "__addmodx(s{},s{},s{})".format(out_slot, x_slot, y_slot)

    def __emit_submodx(self, out_slot, x_slot, y_slot):
        return "__submodx(s{},s{},s{})".format(out_slot, x_slot, y_slot)

    def emit_mulmodx(self, out, x, y):
        out_slot = self.allocs[out]
        x_slot = self.allocs[x]
        y_slot = self.allocs[y]
        return [self.__emit_mulmodx(out_slot, x_slot, y_slot)]

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
            self.__emit_mulmodx(out_slot_0, out_slot_0, out_slot_1),
            # out[1] <- 2 * x[0] * x[1]
            self.__emit_mulmodx(out_slot_1, x_slot_0, x_slot_1),
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

            self.__emit_mulmodx(t0, x_slot_0, y_slot_0),
            self.__emit_mulmodx(t1, x_slot_1, y_slot_1),
            self.__emit_mulmodx(t2, x_slot_0, y_slot_1),
            self.__emit_mulmodx(t3, x_slot_1, y_slot_0),
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
            return self.emit_mulmodx(out, x, x)
        else:
            return self.emit_fp2_sqr(out, x)

    def emit_f_mul(self, out, x, y):
        if self.item_size == 1:
            return self.emit_mulmodx(out, x, y)
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
        output_offset = self.allocs[output] * self.field_width
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
        output_offset = self.allocs[output] * self.field_width
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

def load_module_manifest(target_name: str):
    return load_manifest(target_name, 'modules')

def load_contract_manifest(target_name: str):
    return load_manifest(target_name, 'contracts')

def load_manifest(target_name: str, target_parent_dir):
    manifest = None
    with open('templates/{}/{}/manifest.yml'.format(target_parent_dir, target_name)) as f:
        manifest = yaml.safe_load(f)

    return manifest

def __load_dependencies(target_name, target_manifest, depth=0):
    res = {}
    for imp in target_manifest['imports']:
        imp_manifest = load_module_manifest(imp)
        deps = __load_dependencies(imp, imp_manifest, depth+1)
        for dep_name, dep in deps.items():
            if not dep_name in res:
                res[dep_name] = dep

    target_manifest['depth'] = depth
    res[target_name] = target_manifest
    return res

def load_dependencies(target_name, manifest):
    return __load_dependencies(target_name, manifest)

def allocate_dep_alloc_space(cur_free_mem, cur_free_slot, dep):
    temporaries = dep['temporaries']
    if len(set(temporaries.keys())) != len(temporaries):
        raise Exception("duplicate local temp variable declaration")

    offsets = {}
    mem_offsets = {}

    for temp_name, temp_info in temporaries.items():
        if temp_info['type'] == 'memory':
            mem_offsets[temp_name] = cur_free_mem
            cur_free_mem += temp_info['size']
            continue

        if temp_info['type'] == 'fp':
            size = 1
        elif temp_info['type'] == 'field_element':
            size = 1 # hard-coded to G1 for now
        offsets[temp_name] = cur_free_slot + size
        cur_free_slot += size

    return offsets, cur_free_slot, mem_offsets, cur_free_mem
    
def allocate_alloc_space(deps):
    free_slot = 0
    free_mem = 0
    res = {}
    for dep_name, dep in deps:
        dep_alloc, free_slot, mem_offsets, free_mem = allocate_dep_alloc_space(free_mem, free_slot, dep)
        res[dep_name] = {
            'slots': dep_alloc,
            'memory': mem_offsets,
        }

    return res

def build_template(target_name, deps, is_contract: bool):
    template_state = TemplateState()

    env = NativeEnvironment()

    if is_contract:
        template_path = os.path.join(os.getcwd(), "contracts", target_name)
    else:
        template_path = os.path.join(os.getcwd(), "modules", target_name)

    template_content = ""
    with open(template_name) as f:
        template_content = f.read()

    t = env.from_string(template_content)
    t.globals.update(template_state.get_stdlib())
    result = t.render()



def build_templates(deps):
    build_order = reversed(sorted(deps.items(), key=lambda x: x[1]['depth']))
    build_order = map(lambda x: x[0], build_order)

    import pdb; pdb.set_trace()


def parse_manifests(target_name: str):
    manifest = load_contract_manifest(target_name)
    deps = load_dependencies(target_name, manifest)

    # rank all modules by order of their shallowest import
    sorted_deps = sorted(deps.items(), key=lambda x: x[1]['depth'])

    # TODO: for each depth of the same level, the temporary space should collide
    allocs = allocate_alloc_space(sorted_deps)

    for target in deps.keys():
      deps[target]['allocs'] = allocs[target]

    build_templates(deps)



parse_manifests('ecadd')

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


    with open(os.path.join(os.getcwd(), sys.argv[2]), 'w') as f:
        f.write(result)

if __name__ == "__main__":
    main()
