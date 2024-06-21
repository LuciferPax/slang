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
FUNCTION = iota()
RETURN = iota()
CALL = iota()
DO = iota()
DECREMENT = iota()
INCREMENT = iota()
SWAP = iota()
ROT = iota()
OVER = iota()
FLIP = iota()
ELSE = iota()
COUNT_OPCODES = 18

# Opcode functions

def swap():
   return (SWAP,)

def flip():
   return (FLIP,)

def else_statement():
   return (ELSE,)

def over():
   return (OVER,)

def rot():
   return (ROT,)

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

def do():
   return (DO,)

def div():
   return (DIV,)

def dump():
   return (DUMP,)

def dup():
   return (DUP,)

def break_loop():
   return (BREAK,)

def function(name, argcount):
   return (FUNCTION, name, argcount)

def returns():
   return (RETURN,)

def call(name):
   return (CALL, name)

def decrement():
   return (DECREMENT,)

def increment():
   return (INCREMENT,)

def tokenize_file(file_name):
   with open(file_name, 'r') as f:
      content = f.read()
      tokens = [x for x in content.split() if x]

   program = []
   i = 0
   while i < len(tokens):
      token = tokens[i]
      if token == "drop":
         program.append(pop())
      elif token == "+":
         program.append(add())
      elif token == "-":
         program.append(sub())
      elif token == "*":
         program.append(mul())
      elif token == "else":
         program.append(else_statement())
      elif token == "/":
         program.append(div())
      elif token == ".":
         program.append(dump())
      elif token == "dup":
         program.append(dup())
      elif token == "rot":
         program.append(rot())
      elif token == "if":
         program.append(if_statement())
      elif token == "begin":
         program.append(begin())
      elif token == "break":
         program.append(break_loop())
      elif token == "call":
         program.append(call(tokens[i + 1]))
         i += 1
      elif token == "do":
         program.append(do())
      elif token == "swap":
         program.append(swap())
      elif token == "over":
         program.append(over())
      elif token == "end":
         program.append(end())
      elif token == ".":
         program.append(dump())
      elif token == "flip":
         program.append(flip())
      elif token == "while":
         program.append(while_statement())
      elif token == "function":
         program.append(function(tokens[i + 1], int(tokens[i + 2])))
         i += 2
      elif token == "return":
         program.append(returns())
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
      elif token == "--":
         program.append(decrement())
      elif token == "++":
         program.append(increment())
      else:
         try:
            program.append(push(int(token)))
         except:
            raise Exception("Unknown token: {}".format(token))
      i += 1

   return program
