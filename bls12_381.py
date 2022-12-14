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
    return x + y % fq_mod

def fq_sub(x, y) -> int:
    return x - y % fq_mod

def fq_mul(x, y) -> int:
    return mulmont(x, y)

def fq_inv(x) -> int:
    # TODO implement this using fermat's little theorem with the generated addchain
    return pow(x, -1, fq_mod)

class AffinePoint:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class ProjPoint:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def from_affine(affine_point):
        return ProjPoint(affine_point.x, affine_point.y, to_mont(1))

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


g1_gen_x = 3685416753713387016781088315183077757961620795782546409894578378688607592378376318836054947676345821548104185464507
g1_gen_y = 1339506544944476473020471379941921221584933875938349620426543736416511423956333506472724655353366534992391756441569
g1_gen_point = ProjPoint(to_mont(g1_gen_x), to_mont(g1_gen_y), to_mont(1))

def g1_gen():
    return g1_gen_point

def run_tests():
    # test g1_gen + inf == g1_gen
    # test double(g1_gen) is on curve
    pass

if __name__ == "__main__":
    run_tests()
    print("success")
