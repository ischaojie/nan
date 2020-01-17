"""
AST: Abstract Syntax Tree

it just like this:

program : PROGRAM variable SEMI block DOT
block : declarations compound_statement
declarations : (VAR (variable_declaration SEMI)+)*
   | (PROCEDURE ID (LPAREN formal_parameter_list RPAREN)? SEMI block SEMI)*
   | empty
variable_declaration : ID (COMMA ID)* COLON type_spec
formal_params_list : formal_parameters
                   | formal_parameters SEMI formal_parameter_list
formal_parameters : ID (COMMA ID)* COLON type_spec
type_spec : INTEGER
compound_statement : BEGIN statement_list END
statement_list : statement
               | statement SEMI statement_list
statement : compound_statement
          | assignment_statement
          | empty
assignment_statement : variable ASSIGN expr
empty :
expr : term ((PLUS | MINUS) term)*
term : factor ((MUL | INTEGER_DIV | FLOAT_DIV) factor)*
factor : PLUS factor
       | MINUS factor
       | INTEGER_CONST
       | REAL_CONST
       | LPAREN expr RPAREN
       | variable
variable: ID

"""


class AST(object):
    pass


# PROGRAM: root node
# program : PROGRAM variable SEMI block DOT
class Program(AST):
    def __init__(self, name, block):
        self.name = name  # program name
        self.block = block  # contain's block(declaration and compound)


# block
# block : declarations compound_statement
class Block(AST):
    def __init__(self, declarations, compound_statement):
        self.declarations = declarations  # contain's declarations
        self.compound_statement = compound_statement  # contain's compound


"""
declarations: 
var declarations or procedure declarations or
empty
"""


# var declarations
# a : int
class VarDecl(AST):
    def __init__(self, var_node, type_node):
        self.var_node = var_node  # var
        self.type_node = type_node  # type<int or float or string>


# procedure declarations
class ProcedureDecl(AST):
    def __init__(self, proc_name, params, block_node):
        self.proc_name = proc_name
        self.params = params  # a list of Param nodes
        self.block_node = block_node  # block


class ProcedureCall(AST):
    def __init__(self, proc_name, actual_params, token):
        self.proc_name = proc_name
        self.actual_params = actual_params
        self.token = token


# procedure params
# just like VarDecl
class Param(AST):
    def __init__(self, var_node, type_node):
        self.var_node = var_node
        self.type_node = type_node


# compound
# BEGIN...END
class Compound(AST):
    def __init__(self):
        self.children = []


# assign
# just like a := 10
class Assign(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.token = self.op = op
        self.right = right


"""
basic ast node
type Var Num
"""


# type integer or float
class Type(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value


# var
class Var(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value


# number
class Num(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value


# no operation
class NoOp(AST):
    pass


# binary operation
# + - * /
class BinOp(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.token = self.op = op
        self.right = right


# unary operation
# 5--3
class UnaryOp(AST):
    def __init__(self, op, expr):
        self.token = self.op = op
        self.expr = expr
