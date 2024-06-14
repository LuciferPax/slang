import sys
import llvmlite.ir as ir
import llvmlite.binding as llvm
import os
import subprocess

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
    def pop_stack():
        return stack.pop()

    def copy_pop(offset=-1):
        return stack[offset]

    def push_stack(x):
        stack.append(x)

    def evaluate_condition(condition_opcode):
        if condition_opcode[0] == IS_EQL:
            return copy_pop() == copy_pop(-2)
        elif condition_opcode[0] == IS_NEQ:
            return copy_pop() != copy_pop(-2)
        elif condition_opcode[0] == IS_GRT:
            return copy_pop() > copy_pop(-2)
        elif condition_opcode[0] == IS_LSS:
            return copy_pop() < copy_pop(-2)
        elif condition_opcode[0] == IS_GEQ:
            return copy_pop() >= copy_pop(-2)
        elif condition_opcode[0] == IS_LEQ:
            return copy_pop() <= copy_pop(-2)
        else:
            raise Exception("Unknown condition opcode: {}".format(condition_opcode))

    i = 0
    while i < len(program):
        opcode = program[i]
        if opcode[0] == PUSH:
            push_stack(opcode[1])
        elif opcode[0] == POP:
            pop_stack()
        elif opcode[0] == ADD:
            push_stack(pop_stack() + pop_stack())
        elif opcode[0] == SUB:
            push_stack(pop_stack() - pop_stack())
        elif opcode[0] == MUL:
            push_stack(pop_stack() * pop_stack())
        elif opcode[0] == DIV:
            push_stack(pop_stack() / pop_stack())
        elif opcode[0] == DUMP:
            print(stack[-1])
        elif opcode[0] == DUP:
            push_stack(copy_pop())
        elif opcode[0] == IF:
            condition_opcode = program[i + 1]
            truth = evaluate_condition(condition_opcode)

            if program[i + 2][0] == BEGIN:
                j = i + 3
                block = []
                while program[j][0] != END:
                    block.append(program[j])
                    j += 1

                if truth:
                    simulate(block)
                i = j
        elif opcode[0] == WHILE:
            start_i = i
            condition_opcode = program[i + 1]
            truth = evaluate_condition(condition_opcode)

            if program[i + 2][0] == BEGIN:
                j = i + 3
                block = []
                while program[j][0] != END:
                    block.append(program[j])
                    j += 1

                while truth:
                    simulate(block)
                    condition_opcode = program[start_i + 1]
                    truth = evaluate_condition(condition_opcode)
                i = j
        else:
            raise Exception("Unknown opcode: {}".format(opcode))
        i += 1

class Codegen:
    def __init__(self, output_file, program):
        self.module = ir.Module(name=__file__)
        self.module.triple = llvm.get_default_triple()
        self.func = ir.Function(self.module, ir.FunctionType(ir.IntType(32), []), name="main")
        self.block = self.func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(self.block)

        # array to act as stack
        self.stack_type = ir.ArrayType(ir.IntType(32), 1024)
        self.stack = self.builder.alloca(self.stack_type)
        self.stack_pointer = self.builder.alloca(ir.IntType(32))
        self.builder.store(ir.Constant(ir.IntType(32), 0), self.stack_pointer)

        # Declare printf once
        printf_ty = ir.FunctionType(ir.IntType(32), [ir.PointerType(ir.IntType(8))], var_arg=True)
        self.printf = ir.Function(self.module, printf_ty, name="printf")

        self.compile(program)

        # return 0
        self.builder.ret(ir.Constant(ir.IntType(32), 0))

        self.compile_to_executable(output_file)

    def pop_stack(self):
        stack_pointer = self.builder.load(self.stack_pointer)
        stack_pointer = self.builder.sub(stack_pointer, ir.Constant(ir.IntType(32), 1))
        self.builder.store(stack_pointer, self.stack_pointer)
        ptr = self.builder.gep(self.stack, [ir.Constant(ir.IntType(32), 0), stack_pointer])
        return self.builder.load(ptr)
    
    def copy_pop(self, offset=-1):
        stack_pointer = self.builder.load(self.stack_pointer)
        ptr = self.builder.gep(self.stack, [ir.Constant(ir.IntType(32), 0), self.builder.add(stack_pointer, ir.Constant(ir.IntType(32), offset))])
        return self.builder.load(ptr)
    
    def push_stack(self, x):
        stack_pointer = self.builder.load(self.stack_pointer)
        ptr = self.builder.gep(self.stack, [ir.Constant(ir.IntType(32), 0), stack_pointer])
        self.builder.store(x, ptr)
        self.builder.store(self.builder.add(stack_pointer, ir.Constant(ir.IntType(32), 1)), self.stack_pointer)

    def evaluate_condition(self, condition_opcode):
        if condition_opcode[0] == IS_EQL:
            return self.builder.icmp_signed("==", self.copy_pop(), self.copy_pop(-2))
        elif condition_opcode[0] == IS_NEQ:
            return self.builder.icmp_signed("!=", self.copy_pop(), self.copy_pop(-2))
        elif condition_opcode[0] == IS_GRT:
            return self.builder.icmp_signed(">", self.copy_pop(), self.copy_pop(-2))
        elif condition_opcode[0] == IS_LSS:
            return self.builder.icmp_signed("<", self.copy_pop(), self.copy_pop(-2))
        elif condition_opcode[0] == IS_GEQ:
            return self.builder.icmp_signed(">=", self.copy_pop(), self.copy_pop(-2))
        elif condition_opcode[0] == IS_LEQ:
            return self.builder.icmp_signed("<=", self.copy_pop(), self.copy_pop(-2))
        else:
            raise Exception("Unknown condition opcode: {}".format(condition_opcode))
        
    def print_stack_top(self):
        stack_pointer = self.builder.load(self.stack_pointer)
        ptr = self.builder.gep(self.stack, [ir.Constant(ir.IntType(32), 0), self.builder.sub(stack_pointer, ir.Constant(ir.IntType(32), 1))])
        value = self.builder.load(ptr)
        format_str = "%d\n\0"
        c_format_str = ir.Constant(ir.ArrayType(ir.IntType(8), len(format_str)), bytearray(format_str.encode("utf8")))
        format_str_ptr = self.builder.alloca(c_format_str.type)
        self.builder.store(c_format_str, format_str_ptr)
        format_str_ptr = self.builder.bitcast(format_str_ptr, ir.PointerType(ir.IntType(8)))
        self.builder.call(self.printf, [format_str_ptr, value])

    def compile_to_executable(self, output_file):  
        with open("temp.ll", "w") as f:
            f.write(str(self.module))

        # Compile to object file
        subprocess.run(["clang", "-c", "temp.ll", "-o", "temp.o"])
    
        # Link to create executable
        subprocess.run(["clang", "temp.o", "-o", output_file])

        # Clean up
        os.remove("temp.ll")
        os.remove("temp.o")

    def compile(self, program):
        i = 0
        while i < len(program):
            opcode = program[i]
            if opcode[0] == PUSH:
                self.push_stack(ir.Constant(ir.IntType(32), opcode[1]))
            elif opcode[0] == POP:
                self.pop_stack()
            elif opcode[0] == ADD:
                self.push_stack(self.builder.add(self.pop_stack(), self.pop_stack()))
            elif opcode[0] == SUB:
                self.push_stack(self.builder.sub(self.pop_stack(), self.pop_stack()))
            elif opcode[0] == MUL:
                self.push_stack(self.builder.mul(self.pop_stack(), self.pop_stack()))
            elif opcode[0] == DIV:
                self.push_stack(self.builder.sdiv(self.pop_stack(), self.pop_stack()))
            elif opcode[0] == DUMP:
                self.print_stack_top()
            elif opcode[0] == DUP:
                self.push_stack(self.copy_pop())
            elif opcode[0] == IF:
                condition_opcode = program[i + 1]
                truth = self.evaluate_condition(condition_opcode)

                if program[i + 2][0] == BEGIN:
                    j = i + 3
                    block = []
                    while program[j][0] != END:
                        block.append(program[j])
                        j += 1

                    with self.builder.if_then(truth):
                        self.compile(block)
                    i = j
            elif opcode[0] == WHILE:
                condition_block = self.builder.append_basic_block(name="condition")
                loop_block = self.builder.append_basic_block(name="loop")
                end_block = self.builder.append_basic_block(name="end")

                # Jump to condition block
                self.builder.branch(condition_block)

                # Build condition block
                self.builder.position_at_end(condition_block)
                condition_opcode = program[i + 1]
                truth = self.evaluate_condition(condition_opcode)
                self.builder.cbranch(truth, loop_block, end_block)

                # Build loop block
                self.builder.position_at_end(loop_block)
                start_i = i
                if program[i + 2][0] == BEGIN:
                    j = i + 3
                    block = []
                    while program[j][0] != END:
                        block.append(program[j])
                        j += 1

                    self.compile(block)
                    # Re-evaluate condition after the block
                    self.builder.branch(condition_block)
                    i = j

                # Position at end block for subsequent instructions
                self.builder.position_at_end(end_block)
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
        elif token == "dup":
            program.append(dup())
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

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python slang.py <file> <mode> [output_file]")
        sys.exit(1)

    file_name = sys.argv[1]
    mode = sys.argv[2]

    if mode == "interpret":
        program = compile_file(file_name)
        simulate(program)
    elif mode == "compile":
        output_file = sys.argv[3]
        program = compile_file(file_name)
        codegen = Codegen(output_file, program)
