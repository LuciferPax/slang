import os
import subprocess
import llvmlite.ir as ir
import llvmlite.binding as llvm
from definitions import *

class Codegen:
    def __init__(self, output_file, program):
        self.module = ir.Module(name=__file__)
        self.module.triple = llvm.get_default_triple()
        self.builder = None
        self.functions = {}
        self.main_func = ir.Function(self.module, ir.FunctionType(ir.IntType(32), []), name="main")
        self.block = self.main_func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(self.block)

        # Array to act as stack
        self.stack_type = ir.ArrayType(ir.IntType(32), 1024)
        self.stack = self.builder.alloca(self.stack_type)
        self.stack_pointer = self.builder.alloca(ir.IntType(32))
        self.builder.store(ir.Constant(ir.IntType(32), 0), self.stack_pointer)

        # Declare printf once
        printf_ty = ir.FunctionType(ir.IntType(32), [ir.PointerType(ir.IntType(8))], var_arg=True)
        self.printf = ir.Function(self.module, printf_ty, name="printf")

        # Compile the main program
        self.compile(program)

        # Return 0 from main
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

    def pop_bottom(self):
        ptr = self.builder.gep(self.stack, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)])
        return self.builder.load(ptr)

    def push_bottom(self, x):
        ptr = self.builder.gep(self.stack, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)])
        self.builder.store(x, ptr)

    def evaluate_condition(self, condition_opcode, builder, pop_stack, copy_pop):
        if condition_opcode[0] == IS_EQL:
            return builder.icmp_signed("==", copy_pop(), copy_pop(-2))
        elif condition_opcode[0] == IS_NEQ:
            return builder.icmp_signed("!=", copy_pop(), copy_pop(-2))
        elif condition_opcode[0] == IS_GRT:
            return builder.icmp_signed(">", copy_pop(), copy_pop(-2))
        elif condition_opcode[0] == IS_LSS:
            return builder.icmp_signed("<", copy_pop(), copy_pop(-2))
        elif condition_opcode[0] == IS_GEQ:
            return builder.icmp_signed(">=", copy_pop(), copy_pop(-2))
        elif condition_opcode[0] == IS_LEQ:
            return builder.icmp_signed("<=", copy_pop(), copy_pop(-2))
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
        subprocess.run(["clang", "-static", "temp.o", "-o", output_file])

        # Clean up
        os.remove("temp.ll")
        os.remove("temp.o")

    def extract_block(self, program, start_index):
        block = []
        depth = 0
        i = start_index
        while i < len(program):
            opcode = program[i]
            if opcode[0] in [IF, WHILE, FUNCTION]:
                depth += 1
            elif opcode[0] == END:
                if depth == 0:
                    break
                depth -= 1
            block.append(opcode)
            i += 1
        return block, i

    def compile_function(self, name, body, argcount):
        func_type = ir.FunctionType(ir.IntType(32), [ir.IntType(32)] * argcount)
        function = ir.Function(self.module, func_type, name=name)
        self.functions[name] = function
        block = function.append_basic_block(name="entry")
        builder = ir.IRBuilder(block)
        stack_type = ir.ArrayType(ir.IntType(32), 1024)
        stack = builder.alloca(stack_type)
        stack_pointer = builder.alloca(ir.IntType(32))
        builder.store(ir.Constant(ir.IntType(32), 0), stack_pointer)

        def pop_stack():
            sp = builder.load(stack_pointer)
            sp = builder.sub(sp, ir.Constant(ir.IntType(32), 1))
            builder.store(sp, stack_pointer)
            ptr = builder.gep(stack, [ir.Constant(ir.IntType(32), 0), sp])
            return builder.load(ptr)

        def push_stack(x):
            sp = builder.load(stack_pointer)
            ptr = builder.gep(stack, [ir.Constant(ir.IntType(32), 0), sp])
            builder.store(x, ptr)
            builder.store(builder.add(sp, ir.Constant(ir.IntType(32), 1)), stack_pointer)

        def copy_pop(offset=-1):
            sp = builder.load(stack_pointer)
            ptr = builder.gep(stack, [ir.Constant(ir.IntType(32), 0), builder.add(sp, ir.Constant(ir.IntType(32), offset))])
            return builder.load(ptr)

        def push_bottom(x):
            ptr = builder.gep(stack, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)])
            builder.store(x, ptr)

        def pop_bottom():
            ptr = builder.gep(stack, [ir.Constant(ir.IntType(32), 0), ir.Constant(ir.IntType(32), 0)])
            return builder.load(ptr)

        def print_stack_top():
            sp = builder.load(stack_pointer)
            ptr = builder.gep(stack, [ir.Constant(ir.IntType(32), 0), builder.sub(sp, ir.Constant(ir.IntType(32), 1))])
            value = builder.load(ptr)
            format_str = "%d\n\0"
            c_format_str = ir.Constant(ir.ArrayType(ir.IntType(8), len(format_str)), bytearray(format_str.encode("utf8")))
            format_str_ptr = builder.alloca(c_format_str.type)
            builder.store(c_format_str, format_str_ptr)
            format_str_ptr = builder.bitcast(format_str_ptr, ir.PointerType(ir.IntType(8)))
            builder.call(self.printf, [format_str_ptr, value])

        i = 0
        while i < len(body):
            opcode = body[i]
            if opcode[0] == PUSH:
                push_stack(ir.Constant(ir.IntType(32), opcode[1]))
            elif opcode[0] == POP:
                pop_stack()
            elif opcode[0] == ADD:
                push_stack(builder.add(pop_stack(), pop_stack()))
            elif opcode[0] == OVER:
                push_stack(copy_pop(-2))
            elif opcode[0] == SUB:
                push_stack(builder.sub(pop_stack(), pop_stack()))
            elif opcode[0] == MUL:
                push_stack(builder.mul(pop_stack(), pop_stack()))
            elif opcode[0] == FLIP:
                top = pop_stack()
                bottom = pop_bottom()
                push_bottom(top)
                push_stack(bottom)
            elif opcode[0] == DIV:
                push_stack(builder.sdiv(pop_stack(), pop_stack()))
            elif opcode[0] == SWAP:
                top = pop_stack()
                second = pop_stack()
                push_stack(top)
                push_stack(second)
            elif opcode[0] == ROT:
                top = pop_stack()
                second = pop_stack()
                third = pop_stack()
                push_stack(top)
                push_stack(third)
                push_stack(second)
            elif opcode[0] == DUMP:
                print_stack_top()
            elif opcode[0] == DUP:
                push_stack(copy_pop())
            elif opcode[0] == BREAK:
                break
            elif opcode[0] == RETURN:
                builder.ret(pop_stack())
                return
            elif opcode[0] == IF:
                condition_opcode = body[i + 1]
                truth = self.evaluate_condition(condition_opcode, builder, pop_stack, copy_pop)
                if body[i + 2][0] == DO:
                    j = i + 3
                    block, end_index = self.extract_block(body, j)
                    with builder.if_then(truth):
                        self.compile(block, builder, pop_stack, push_stack, copy_pop, push_bottom, pop_bottom)
                    i = end_index
            elif opcode[0] == WHILE:
                condition_block = builder.append_basic_block(name="condition")
                loop_block = builder.append_basic_block(name="loop")
                end_block = builder.append_basic_block(name="end")
                builder.branch(condition_block)
                builder.position_at_end(condition_block)
                condition_opcode = body[i + 1]
                truth = self.evaluate_condition(condition_opcode, builder, pop_stack, copy_pop)
                builder.cbranch(truth, loop_block, end_block)
                builder.position_at_end(loop_block)
                start_i = i
                if body[i + 2][0] == DO:
                    j = i + 3
                    block, end_index = self.extract_block(body, j)
                    self.compile(block, builder, pop_stack, push_stack, copy_pop, push_bottom, pop_bottom)
                    builder.branch(condition_block)
                    i = end_index
                builder.position_at_end(end_block)
            else:
                raise Exception(f"Unknown opcode: {opcode}")
            i += 1
        builder.ret(ir.Constant(ir.IntType(32), 0))

    def compile(self, program, builder=None, pop_stack=None, push_stack=None, copy_pop=None, push_bottom=None, pop_bottom=None):
        if builder is None:
            builder = self.builder
        if pop_stack is None:
            pop_stack = self.pop_stack
        if push_stack is None:
            push_stack = self.push_stack
        if copy_pop is None:
            copy_pop = self.copy_pop
        if push_bottom is None:
            push_bottom = self.push_bottom
        if pop_bottom is None:
            pop_bottom = self.pop_bottom

        i = 0
        while i < len(program):
            opcode = program[i]
            if opcode[0] == PUSH:
                push_stack(ir.Constant(ir.IntType(32), opcode[1]))
            elif opcode[0] == SWAP:
                top = pop_stack()
                second = pop_stack()
                push_stack(top)
                push_stack(second)
            elif opcode[0] == ROT:
                top = pop_stack()
                second = pop_stack()
                third = pop_stack()
                push_stack(top)
                push_stack(third)
                push_stack(second)
            elif opcode[0] == POP:
                pop_stack()
            elif opcode[0] == ADD:
                push_stack(builder.add(pop_stack(), pop_stack()))
            elif opcode[0] == FLIP:
                top = pop_stack()
                bottom = pop_bottom()
                push_bottom(top)
                push_stack(bottom)
            elif opcode[0] == OVER:
                push_stack(copy_pop(-2))
            elif opcode[0] == SUB:
                push_stack(builder.sub(pop_stack(), pop_stack()))
            elif opcode[0] == MUL:
                push_stack(builder.mul(pop_stack(), pop_stack()))
            elif opcode[0] == DIV:
                push_stack(builder.sdiv(pop_stack(), pop_stack()))
            elif opcode[0] == DUMP:
                self.print_stack_top()
            elif opcode[0] == INCREMENT:
                top = pop_stack()
                push_stack(builder.add(top, ir.Constant(ir.IntType(32), 1)))
            elif opcode[0] == DECREMENT:
                top = pop_stack()
                push_stack(builder.sub(top, ir.Constant(ir.IntType(32), 1)))
            elif opcode[0] == DUP:
                push_stack(copy_pop())
            elif opcode[0] == BREAK:
                break
            elif opcode[0] == FUNCTION:
                name = opcode[1]
                argcount = opcode[2]
                body, end_index = self.extract_block(program, i + 2)
                self.compile_function(name, body, argcount)
                i = end_index
            elif opcode[0] == CALL:
                func_name = opcode[1]
                if func_name in self.functions:
                    func = self.functions[func_name]
                    argcount = len(func.args)
                    args = [pop_stack() for _ in range(argcount)]
                    args.reverse()
                    retval = builder.call(func, args)
                    push_stack(retval)
                else:
                    raise Exception(f"Function {func_name} not found")
            elif opcode[0] == IF:
                condition_opcode = program[i + 1]
                truth = self.evaluate_condition(condition_opcode, builder, pop_stack, copy_pop)
                if program[i + 2][0] == DO:
                    j = i + 3
                    block, end_index = self.extract_block(program, j)
                    with builder.if_then(truth):
                        self.compile(block, builder, pop_stack, push_stack, copy_pop, push_bottom, pop_bottom)
                    i = end_index
            elif opcode[0] == WHILE:
                condition_block = builder.append_basic_block(name="condition")
                loop_block = builder.append_basic_block(name="loop")
                end_block = builder.append_basic_block(name="end")
                builder.branch(condition_block)
                builder.position_at_end(condition_block)
                condition_opcode = program[i + 1]
                truth = self.evaluate_condition(condition_opcode, builder, pop_stack, copy_pop)
                builder.cbranch(truth, loop_block, end_block)
                builder.position_at_end(loop_block)
                start_i = i
                if program[i + 2][0] == DO:
                    j = i + 3
                    block, end_index = self.extract_block(program, j)
                    self.compile(block, builder, pop_stack, push_stack, copy_pop, push_bottom, pop_bottom)
                    builder.branch(condition_block)
                    i = end_index
                builder.position_at_end(end_block)
            else:
                raise Exception(f"Unknown opcode: {opcode}")
            i += 1
