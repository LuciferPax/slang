import sys

sys.path.append('includes')

from definitions import *
from interpreter import simulate
from compiler import Codegen

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 slang.py <file name> <mode> [other args....]")
        sys.exit(1)

    file_name = sys.argv[1]
    mode = sys.argv[2]

    if mode == "--intr":
        program = tokenize_file(file_name)
        simulate(program)
    elif mode == "--comp":
        output_file = "a.out"
        if "--out" in sys.argv:
            output_file = sys.argv[sys.argv.index("--out") + 1]

        program = tokenize_file(file_name)
        codegen = Codegen(output_file, program)
