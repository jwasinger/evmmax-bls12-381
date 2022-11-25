import sys
import os
from jinja2.nativetypes import NativeEnvironment

def main():
    if len(sys.argv) != 3:
        raise Exception("bad argument count")

    env = NativeEnvironment()

    template_content = ""
    with open(os.path.join(os.getcwd(),sys.argv[1])) as f:
        template_content = f.read()

    exponent = 1
    exponent_bits = [int(digit) for digit in bin(exponent)[2:]]
    t = env.from_string(template_content)
    result = t.render(exponent_bits=exponent_bits)

    with open(os.path.join(os.getcwd(), sys.argv[2]), 'w') as f:
        f.write(result)

if __name__ == "__main__":
    main()
