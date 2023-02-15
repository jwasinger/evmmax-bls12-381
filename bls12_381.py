SUBGROUP_ORDER = 0x73eda753299d7d483339d80809a1d80553bda402fffe5bfeffffffff00000001
fq_mod = 0x1a0111ea397fe69a4b1ba7b6434bacd764774b84f38512bf6730d2a0f6b0f6241eabfffeb153ffffb9feffffffffaaab
r = 1 << 384
mod_inv = pow(r, -1, fq_mod)
r_squared = (r ** 2) % fq_mod

def mulmont(x, y) -> int:
    return x * y * mod_inv % fq_mod

def to_mont(val):
    return mulmont(val, r_squared)

def to_norm(val):
    return mulmont(val, 1)

def fq_add(x, y) -> int:
    return (x + y) % fq_mod

def fq_sub(x, y) -> int:
    return (x - y) % fq_mod

def fq_mul(x, y) -> int:
    return mulmont(x, y)

def fq_sqr(x) -> int:
    return mulmont(x, x)

def fq_inv(x) -> int:
    # TODO implement this using fermat's little theorem with the generated addchain
    x_norm = to_norm(x)
    res = pow(x, -1, fq_mod)
    return to_mont(res)

class AffinePoint:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class G1ProjPoint:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def from_affine(affine_point):
        return G1ProjPoint(affine_point.x, affine_point.y, to_mont(1))

    def to_affine(self):
        if self.is_inf():
            return AffinePoint(0, 0)

        z_inv = fq_inv(self.z)
        return AffinePoint(fq_mul(self.x, z_inv), fq_mul(self.y, z_inv))

    def add(p1, p2):
        pass

    def double(p1, p2):
        pass

    def is_on_curve(self):
        # TODO: return Y^2 Z = X^3 + b Z^3
        pass

    def is_inf(self):
        pass

def fq2_mul(x, y) -> (int, int):
    t0 = fq_mul(x[0], y[0])
    t1 = fq_mul(x[1], y[1])
    t2 = fq_mul(x[0], y[1])
    t3 = fq_mul(x[1], y[0])

    return (
        fq_sub(t0, t1),
        fq_add(t2, t3)
    )

def fq2_inv(x) -> (int, int):
    t0 = fq_sqr(x[0])
    t1 = fq_sqr(x[1])
    t0 = fq_add(t0, t1)
    t0 = fq_inv(t0)
    res_0 = fq_mul(t0, x[0])
    res_1 = fq_sub(0, t0)
    res_1 = fq_mul(x[1], res_1)

    return (
        res_0,
        res_1)

def fq2_add(x, y) -> (int, int):
    res = (
        fq_add(x[0], y[0]),
        fq_add(x[1], y[1]))
    return res

class G2ProjPoint:
    def __init__(self, x0, x1, y0, y1, z0, z1):
        self.x0 = x0
        self.x1 = x1
        self.y0 = y0
        self.y1 = y1
        self.z0 = z0
        self.z1 = z1

    def to_affine(self):
        # TODO: add back in
        #if self.is_inf():
        #    return AffinePoint(0, 0)

        import pdb; pdb.set_trace()
        z_inv = fq2_inv((self.z0, self.z1))
        return AffinePoint(fq2_mul((self.x0, self.x1), z_inv), fq2_mul((self.y0, self.y1), z_inv))

def g2_point_from_raw(raw):
    return G2ProjPoint(to_norm(int(raw[0:96], 16)),
    to_norm(int(raw[96:192], 16)),
    to_norm(int(raw[192:288], 16)),
    to_norm(int(raw[288:384], 16)),
    to_norm(int(raw[384:480], 16)),
    to_norm(int(raw[480:576], 16)))
    
g1_gen_x = 3685416753713387016781088315183077757961620795782546409894578378688607592378376318836054947676345821548104185464507
g1_gen_y = 1339506544944476473020471379941921221584933875938349620426543736416511423956333506472724655353366534992391756441569
g1_gen_point = G1ProjPoint(g1_gen_x, g1_gen_y, 1)

g2_gen_x_0 = 352701069587466618187139116011060144890029952792775240219908644239793785735715026873347600343865175952761926303160
g2_gen_x_1 = 3059144344244213709971259814753781636986470325476647558659373206291635324768958432433509563104347017837885763365758
g2_gen_y_0 = 1985150602287291935568054521177171638300868978215655730859378665066344726373823718423869104263333984641494340347905
g2_gen_y_1 = 927553665492332455747201965776037880757740193453592970025027978793976877002675564980949289727957565575433344219582
g2_gen_z_0 = 1
g2_gen_z_1 = 0

g2_gen_point = G2ProjPoint(g2_gen_x_0, g2_gen_x_1, g2_gen_y_0, g2_gen_y_1, g2_gen_z_0, g2_gen_z_1)

def g1_gen():
    return g1_gen_point

def g2_gen():
    return g2_gen_point

def run_tests():
    # test g1_gen + inf == g1_gen
    # test double(g1_gen) is on curve
    pass

if __name__ == "__main__":
    run_tests()
    print("success")
