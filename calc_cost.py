# evm instruction overhead cost for double-and-add loop + point_double evm overhead
COST_EVM_ARITH_COMPLETE = 100

def cost_point_add(cost_mul, cost_square, cost_addsub, cost_double):
    cost_point_add = 8 * cost_mul + 5 * cost_square + 8 * cost_addsub + 4 * cost_double

def cost_point_double(cost_mul, cost_square, cost_addsub, cost_double):
    pass

def worst_case_scalar_mul_cost(cost_mul, cost_square, cost_addsub, cost_double):
    cost_padd = cost_point_add(cost_mul, cost_square, cost_addsub, cost_double)
    cost_pdouble = cost_point_double(cost_mul, cost_square, cost_addsub, cost_double)
    return 254 * (cost_point_add + cost_point_double + 110), 254 * COST_EVM_ARITH_COMPLETE

def cost_mul_fp2(mulmont_cost, addsub_cost) -> int:
    pass

def cost_add_fp2(mulmont_cost, addsub_cost) -> int:
    pass

def cost_square_fp2(mulmont_cost, addsub_cost) -> int:
    pass

def main():
    evmmax_cost_models = [[4,2], [3,1], [2,1]]

    # complete algorithm from 
    fp2_costs = None

    for mulmont_cost, addsub_cost in evmmax_cost_models:
        # fp
        cost_mul = mulmont_cost
        cost_square = mulmont_cost
        cost_addsub = addsub_cost
        cost_double = addsub_cost

        cost_point_add = 8 * cost_mul + 5 * cost_square + 8 * cost_addsub + 4 * cost_double
        cost_point_double =  12 * cost_mul + 5 * cost_square + 8 + cost_addsub + 4 * cost_double
        print("cost_add = {}, cost_double = {}".format(cost_point_add, cost_point_double))
        import pdb; pdb.set_trace()

if __name__ == "__main__":
    main()
