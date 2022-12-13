with open('addchain_example.txt', 'r') as f:
    for i, line in enumerate(f):
        if line.startswith("_"):
            pass
        elif line.startswith("i"):
            pass
        elif line.startswith("return"):
            pass
        else:
            raise Exception("unexpected")
