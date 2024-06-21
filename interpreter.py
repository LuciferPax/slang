from definitions import *

stack_suspened = []
stack = []
call_stack = []
functions = {}

def simulate(program, using_functions=False):

    global stack
    global stack_suspened
    global functions
    
    def pop_stack():
        return stack.pop()

    def pop_bottom():
        return stack.pop(0)

    def push_bottom(x):
        stack.insert(0, x)

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

    def extract_block(program, start_index):
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
        elif opcode[0] == SWAP:
            top = pop_stack()
            second = pop_stack()
            push_stack(top)
            push_stack(second)
        elif opcode[0] == ROT:
            top = pop_stack() # top becomes third
            second = pop_stack() # second becomes first
            third = pop_stack() # third becomes second
            push_stack(top)
            push_stack(third)
            push_stack(second)
        elif opcode[0] == OVER:
            push_stack(copy_pop(-2))
        elif opcode[0] == MUL:
            push_stack(pop_stack() * pop_stack())
        elif opcode[0] == DIV:
            push_stack(pop_stack() / pop_stack())
        elif opcode[0] == DECREMENT:
            top = pop_stack()
            push_stack(top - 1)
        elif opcode[0] == FLIP:
            top = pop_stack()
            bottom = pop_bottom()

            push_bottom(top)
            push_stack(bottom)
        elif opcode[0] == INCREMENT:
            top = pop_stack()
            push_stack(top + 1)
        elif opcode[0] == DUMP:
            print(stack[-1])
        elif opcode[0] == DUP:
            push_stack(copy_pop())
        elif opcode[0] == BREAK:
            break
        elif opcode[0] == FUNCTION:
            name = opcode[1]
            argcount = opcode[2]
            block, end_index = extract_block(program, i + 2)
            functions[name] = {
                "name": name,
                "number_of_args": argcount,
                "body": block
            }
            i = end_index
        elif opcode[0] == RETURN:
            if using_functions:
                stack_suspened.append(stack.pop())
                stack = stack_suspened
                return
            else:
                raise Exception("Return outside of function")
        elif opcode[0] == CALL:
            if opcode[1] in functions:
                stack_suspened = stack
                stack = []
                number_of_args = functions[opcode[1]]["number_of_args"]
                for _ in range(number_of_args):
                    stack.append(stack_suspened.pop())
                simulate(functions[opcode[1]]["body"], using_functions=True)
                stack = stack_suspened
                stack_suspened = []
            else:
                raise Exception("Function {} not found".format(opcode[1]))
        elif opcode[0] == IF:
            condition_opcode = program[i + 1]
            truth = evaluate_condition(condition_opcode)
            block, end_index = extract_block(program, i + 3)
            if truth:
                simulate(block)
            i = end_index
        elif opcode[0] == WHILE:
            start_i = i
            condition_opcode = program[i + 1]
            block, end_index = extract_block(program, i + 3)
            while evaluate_condition(condition_opcode):
                simulate(block)
            i = end_index
        else:
            raise Exception("Unknown opcode: {}".format(opcode))
        i += 1
