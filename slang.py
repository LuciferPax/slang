import sys

# Define the iota and opcodes
iota_count = 0
def iota(reset=False):
    global iota_count
    if reset:
        iota_count = 0
        return
    result = iota_count
    iota_count += 1
    return result

# Define opcodes
PUSH = iota(reset=True)
POP = iota()
ADD = iota()
SUB = iota()
MUL = iota()
DIV = iota()
DUMP = iota()
DUP = iota()
BREAK = iota()
END = iota()
BEGIN = iota()
IF = iota()
IS_EQL = iota()
IS_NEQ = iota()
IS_GRT = iota()
IS_LSS = iota()
IS_GEQ = iota()
IS_LEQ = iota()
WHILE = iota()
COUNT_OPCODES = 18

# Opcode functions
def push(x):
    return (PUSH, x)

def pop():
    return (POP,)

def if_statement():
    return (IF,)

def begin():
    return (BEGIN,)

def end():
    return (END,)

def is_eql():
    return (IS_EQL,)

def is_neq():
    return (IS_NEQ,)

def is_grt():
    return (IS_GRT,)

def is_lss():
    return (IS_LSS,)

def is_geq():
    return (IS_GEQ,)

def is_leq():
    return (IS_LEQ,)

def while_statement():
    return (WHILE,)

def add():
    return (ADD,)

def sub():
    return (SUB,)

def mul():
    return (MUL,)

def div():
    return (DIV,)

def dump():
    return (DUMP,)

def dup():
    return (DUP,)

def break_loop():
    return (BREAK,)

stack = []
def simulate(program):

    def pop():
        return stack.pop()

    def copy_pop(offset=-1):
        return stack[offset]

    def push(x):
        stack.append(x)

    i = 0
    while i < len(program):
        opcode = program[i]
        if opcode[0] == PUSH:
            push(opcode[1])
        elif opcode[0] == POP:
            pop()
        elif opcode[0] == ADD:
            push(pop() + pop())
        elif opcode[0] == SUB:
            push(pop() - pop())
        elif opcode[0] == MUL:
            push(pop() * pop())
        elif opcode[0] == DIV:
            push(pop() / pop())
        elif opcode[0] == DUMP:
            print(stack[-1])
        elif opcode[0] == IF:
            truth = False
            condition_opcode = program[i + 1]
            if condition_opcode[0] == IS_EQL:
                a = copy_pop()
                b = copy_pop(-2)
                truth = a == b
            elif condition_opcode[0] == IS_NEQ:
                a = copy_pop()
                b = copy_pop(-2)
                truth = a != b
            elif condition_opcode[0] == IS_GRT:
                a = copy_pop()
                b = copy_pop(-2)
                truth = a > b
            elif condition_opcode[0] == IS_LSS:
                a = copy_pop()
                b = copy_pop(-2)
                truth = a < b
            elif condition_opcode[0] == IS_GEQ:
                a = copy_pop()
                b = copy_pop(-2)
                truth = a >= b
            elif condition_opcode[0] == IS_LEQ:
                a = copy_pop()
                b = copy_pop(-2)
                truth = a <= b

            if program[i + 2][0] == BEGIN:
                # Find the corresponding END for this BEGIN
                j = i + 3
                block = []
                while program[j][0] != END:
                    block.append(program[j])
                    j += 1

                if truth:
                    simulate(block)
                # Skip the block in the main program
                i = j + 1
            else:
                # If no BEGIN after the condition, just move to the next instruction
                i += 2
        elif opcode[0] == WHILE:
            start_i = i
            truth = False
            condition_opcode = program[i + 1]
            if condition_opcode[0] == IS_EQL:
                a = copy_pop()
                b = copy_pop(-2)
                truth = a == b
            elif condition_opcode[0] == IS_NEQ:
                a = copy_pop()
                b = copy_pop(-2)
                truth = a != b
            elif condition_opcode[0] == IS_GRT:
                a = copy_pop()
                b = copy_pop(-2)
                truth = a > b
            elif condition_opcode[0] == IS_LSS:
                a = copy_pop()
                b = copy_pop(-2)
                truth = a < b
            elif condition_opcode[0] == IS_GEQ:
                a = copy_pop()
                b = copy_pop(-2)
                truth = a >= b
            elif condition_opcode[0] == IS_LEQ:
                a = copy_pop()
                b = copy_pop(-2)
                truth = a <= b

            if program[i + 2][0] == BEGIN:
                # Find the corresponding ENDWHILE for this WHILE
                j = i + 3
                block = []
                while program[j][0] != END:
                    block.append(program[j])
                    j += 1

                while truth:
                    simulate(block)
                    # Re-evaluate the condition
                    k = start_i + 1
                    condition_opcode = program[k]
                    if condition_opcode[0] == IS_EQL:
                        a = copy_pop()
                        b = copy_pop(-2)
                        truth = a == b
                    elif condition_opcode[0] == IS_NEQ:
                        a = copy_pop()
                        b = copy_pop(-2)
                        truth = a != b
                    elif condition_opcode[0] == IS_GRT:
                        a = copy_pop()
                        b = copy_pop(-2)
                        truth = a > b
                    elif condition_opcode[0] == IS_LSS:
                        a = copy_pop()
                        b = copy_pop(-2)
                        truth = a < b
                    elif condition_opcode[0] == IS_GEQ:
                        a = copy_pop()
                        b = copy_pop(-2)
                        truth = a >= b
                    elif condition_opcode[0] == IS_LEQ:
                        a = copy_pop()
                        b = copy_pop(-2)
                        truth = a <= b

                # Skip the block in the main program
                i = j + 1
            else:
                # If no BEGIN after the condition, just move to the next instruction
                i += 2
        else:
            raise Exception("Unknown opcode: {}".format(opcode))
        i += 1

def compile_file(file_name):
    with open(file_name, 'r') as f:
        content = f.read()
        tokens = [x for x in content.split() if x]
    
    program = []
    for token in tokens:
        if token == "pop":
            program.append(pop())
        elif token == "add":
            program.append(add())
        elif token == "sub":
            program.append(sub())
        elif token == "mul":
            program.append(mul())
        elif token == "div":
            program.append(div())
        elif token == "dump":
            program.append(dump())
        elif token == "if":
            program.append(if_statement())
        elif token == "begin":
            program.append(begin())
        elif token == "end":
            program.append(end())
        elif token == "while":
            program.append(while_statement())
        elif token == "==":
            program.append(is_eql())
        elif token == "!=":
            program.append(is_neq())
        elif token == ">":
            program.append(is_grt())
        elif token == "<":
            program.append(is_lss())
        elif token == ">=":
            program.append(is_geq())
        elif token == "<=":
            program.append(is_leq())
        elif token == "dump":    
            program.append(dump())
        else:
            try:
                program.append(push(int(token)))
            except:
                raise Exception("Unknown token: {}".format(token))
    return program

# Define input content as a string
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python slang.py <file>")
        sys.exit(1)

    program = compile_file(sys.argv[1])
    simulate(program)
