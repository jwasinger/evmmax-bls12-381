SUBGROUP_ORDER = 0xffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551
fq_mod =         0xffffffff00000001000000000000000000000000ffffffffffffffffffffffff
r = 1 << 256 
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
    x_norm = to_norm(x)
    res = pow(x_norm, -1, fq_mod)
    return to_mont(res)

class G1AffinePoint:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def eq(self, other) -> bool:
        return self.x == other.x and self.y == other.y

def mul_by_3b(val):
    val_12 = to_mont(6)
    return fq_mul(val, val_12)

class G1ProjPoint:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    @staticmethod
    def generator_mont():
        g1_gen_x = 0x6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296
        g1_gen_y = 0x4fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5
        g1_gen_z = 1
        g1_gen_point = G1ProjPoint(to_mont(g1_gen_x), to_mont(g1_gen_y), to_mont(g1_gen_z))

        return g1_gen_point

    @staticmethod
    def generator():
        g1_gen_x = 0x6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296
        g1_gen_y = 0x4fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5
        g1_gen_z = 1
        g1_gen_point = G1ProjPoint(g1_gen_x, g1_gen_y, g1_gen_z)

        return g1_gen_point

    def is_on_curve(self):
        # TODO don't convert to affine
        affine_pt = self.to_affine()
        res = fq_mul(affine_pt.y, affine_pt.y) == fq_add(fq_mul(fq_mul(affine_pt.x, affine_pt.x), affine_pt.x), to_mont(2))
        return res

    def infinity():
        return G1ProjPoint(0, 1, 0)

    def infinity_mont():
        return G1ProjPoint(0, to_mont(1), 0)

    def from_affine(affine_point):
        return G1ProjPoint(affine_point.x, affine_point.y, to_mont(1))

    def to_affine(self):
        if self.is_inf():
            return G1AffinePoint(0, 0)

        z_inv = fq_inv(self.z)
        return G1AffinePoint(fq_mul(self.x, z_inv), fq_mul(self.y, z_inv))

    def add(self, rhs):
        t0 = fq_mul(self.x, rhs.x)
        t1 = fq_mul(self.y, rhs.y)
        t2 = fq_mul(self.z, rhs.z)
        t3 = fq_add(self.x, self.y)
        t4 = fq_add(rhs.x, rhs.y)
        t3 = fq_mul(t3, t4)
        t4 = fq_add(t0, t1)
        t3 = fq_sub(t3, t4)
        t4 = fq_add(self.y, self.z)
        x3 = fq_add(rhs.y, rhs.z)
        t4 = fq_mul(t4, x3)
        x3 = fq_add(t1, t2)
        t4 = fq_sub(t4, x3)
        x3 = fq_add(self.x, self.z)
        y3 = fq_add(rhs.x, rhs.z)
        x3 = fq_mul(x3, y3)
        y3 = fq_add(t0, t2)
        y3 = fq_sub(x3, y3)
        x3 = fq_add(t0, t0)
        t0 = fq_add(x3, t0)
        t2 = mul_by_3b(t2);
        z3 = fq_add(t1, t2)
        t1 = fq_sub(t1, t2)
        y3 = mul_by_3b(y3)
        x3 = fq_mul(t4, y3)
        t2 = fq_mul(t3, t1)
        x3 = fq_sub(t2, x3)
        y3 = fq_mul(y3, t0)
        t1 = fq_mul(t1, z3)
        y3 = fq_add(t1, y3)
        t0 = fq_mul(t0, t3)
        z3 = fq_mul(z3, t4)
        z3 = fq_add(z3, t0)

        return G1ProjPoint(x3, y3, z3)

    def double(self):
        t0 = fq_mul(self.y, self.y)
        z3 = fq_add(t0, t0)
        z3 = fq_add(z3, z3)
        z3 = fq_add(z3, z3)
        t1 = fq_mul(self.y, self.z)
        t2 = fq_mul(self.z, self.z)
        t2 = mul_by_3b(t2);
        x3 = fq_mul(t2, z3)
        y3 = fq_add(t0, t2)
        z3 = fq_mul(t1, z3)
        t1 = fq_add(t2, t2)
        t2 = fq_add(t1, t2)
        t0 = fq_sub(t0, t2)
        y3 = fq_mul(t0, y3)
        y3 = fq_add(x3, y3)
        t1 = fq_mul(self.x, self.y)
        x3 = fq_mul(t0, t1)
        x3 = fq_add(x3, x3)

        return G1ProjPoint(x3, y3, z3)

    def mul(self, scalar: int):
        scalar_bits = bin(scalar)[2:]
        scalar_bits = [int(digit) for digit in scalar_bits]

        acc = G1ProjPoint.infinity_mont()

        for bit in scalar_bits:
                acc = acc.double()
                if bit == 1:
                        acc = self.add(acc)

        return acc

    #def is_on_curve(self):
        # TODO: return Y^2 Z = X^3 + b Z^3
        #pass

    def is_inf(self):
        if self.x == 0 and self.y != 0 and self.z == 0:
            return True
        return False

def fq2_mul(x, y) -> (int, int):
    t0 = fq_mul(x[0], y[0])
    t1 = fq_mul(x[1], y[1])
    t2 = fq_mul(x[0], y[1])
    t3 = fq_mul(x[1], y[0])

    res = (
        fq_sub(t0, t1),
        fq_add(t2, t3)
    )
    return res

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

class G2AffinePoint:
    def __init__(self, x0, x1, y0, y1):
        self.x0 = x0
        self.x1 = x1
        self.y0 = y0
        self.y1 = y1

    def eq(self, other) -> bool:
        return self.x0 == other.x0 and self.x1 == other.x1 and self.y0 == other.y0 and self.y1 == other.y1

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
        z_inv = fq2_inv((self.z0, self.z1))
        x = fq2_mul((self.x0, self.x1), z_inv)
        y = fq2_mul((self.y0, self.y1), z_inv)
        return G2AffinePoint(x[0], x[1], y[0], y[1])

def g2_point_from_raw(raw):
    return G2ProjPoint(to_norm(int(raw[0:96], 16)),
    to_norm(int(raw[96:192], 16)),
    to_norm(int(raw[192:288], 16)),
    to_norm(int(raw[288:384], 16)),
    to_norm(int(raw[384:480], 16)),
    to_norm(int(raw[480:576], 16)))
    
# g1_gen_x = 3685416753713387016781088315183077757961620795782546409894578378688607592378376318836054947676345821548104185464507
# g1_gen_y = 1339506544944476473020471379941921221584933875938349620426543736416511423956333506472724655353366534992391756441569
# g1_gen_point = G1ProjPoint(g1_gen_x, g1_gen_y, 1)

g2_gen_x_0 = 352701069587466618187139116011060144890029952792775240219908644239793785735715026873347600343865175952761926303160
g2_gen_x_1 = 3059144344244213709971259814753781636986470325476647558659373206291635324768958432433509563104347017837885763365758
g2_gen_y_0 = 1985150602287291935568054521177171638300868978215655730859378665066344726373823718423869104263333984641494340347905
g2_gen_y_1 = 927553665492332455747201965776037880757740193453592970025027978793976877002675564980949289727957565575433344219582
g2_gen_z_0 = 1
g2_gen_z_1 = 0

g2_gen_point = G2ProjPoint(g2_gen_x_0, g2_gen_x_1, g2_gen_y_0, g2_gen_y_1, g2_gen_z_0, g2_gen_z_1)
g2_gen_point_affine = G2AffinePoint(g2_gen_x_0, g2_gen_x_1, g2_gen_y_0, g2_gen_y_1)

def g1_gen():
    return g1_gen_point

def g2_gen():
    return g2_gen_point

def g2_gen_affine():
    return g2_gen_point_affine

def test_bls12381_alg1():
    a = to_mont(0xffffffff00000001000000000000000000000000fffffffffffffffffffffffc)
    b3 = to_mont(3 * 0x5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b)
    # p1 is generator * (SUBGROUP_ORDER - 1)
    p1 = G1ProjPoint(to_mont(48439561293906451759052585252797914202762949526041747995844080717082404635286), to_mont(79657838253606452964112319029819691573475036742305299123656433055298683448842), to_mont(1))  
    p2 = G1ProjPoint.generator_mont()

    # x_3 = (x_1 * y_2 + x_2 * y_1) * (y1 * y2 - a * (x1 * z2 + x2 * z1) - 3 * b * z1 * z2) - (y1 * z2 + y2 * z1) * (a * x1 * x2 + 3 * b * (x1 * z2 + x2 * z1) - a * a * z1 * z2)
    # compute (x_1 * y_2 + x_2 * y_1) 
    t1 = fq_add(fq_mul(p1.x, p2.y), fq_mul(p2.x, p1.y))
    # compute (y1 * y2 - a * (x1 * z2 + x2 * z1) - 3 * b * z1 * z2)
    t2 = fq_sub(fq_sub(fq_mul(p1.y, p2.y), fq_mul(a, fq_add(fq_mul(p1.x, p2.z), fq_mul(p2.x, p1.z)))), fq_mul(b3, fq_mul(p1.z, p2.z)))
    # compute (y1 * z2 + y2 * z1)
    t3 = fq_add(fq_mul(p1.y, p2.z), fq_mul(p2.y, p1.z))
    # compute (a * x1 * x2 + 3 * b * (x1 * z2 + x2 * z1) - a * a * z1 * z2)
    t4 = fq_sub(fq_add(fq_mul(a, fq_mul(p1.x, p2.x)), fq_mul(b3, fq_add(fq_mul(p1.x, p2.z), fq_mul(p2.x, p1.z)))), fq_mul(fq_mul(a, a), fq_mul(p1.z, p2.z)))

    # y_3 = (3 * x1 * x2 + a * z1 * z2) * (a * x1 * x2 + 3 * b * (x1 * z2 + x2 * z1) - a * a * z1 * z2) + (y1 * y2 + a * (x1 * z2 + x2 * z1) + 3 * b * z1 * z2)
    t1 = fq_add(fq_mul(fq_mul(to_mont(3), point1.x), point2.x), fq_mul(fq_mul(a, point1.z), point2.z)
    t2 = fq_add(fq_mul(fq_mul(a, poin1.x), point2.x), fq_mul(fq_mul(fq_add(fq_mul(point1.x, point2.z), fq_mul(point2.x, point1.z)), b), to_mont(3)))
    t3 = fq_add(fq_add(fq_mul(point1.y, point2.y), fq_mul(fq_mul(fq_add(point1.x, point2.z), fq_mul(point2.x, point1.z))
    output_y = fq

    
    # compute final value
    output_x = fq_sub(fq_mul(t1, t2), fq_mul(t3, t4))
    output_y = 1
    output_z = 0

    assert output_x == 0 and output_y != 0 and output_z == 0
    import pdb; pdb.set_trace()

def run_tests():
    # test g1_gen + inf == g1_gen
    # test double(g1_gen) is on curve
    test_bls12381_alg1()

if __name__ == "__main__":
    run_tests()
    print("success")
