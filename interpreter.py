"""
解释器
"""

from collections import OrderedDict
from enum import Enum

from error import SemanticError, ErrorCode
from token import TokenType

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
--------------------    ast node visitor    --------------------    
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


class NodeVisitor(object):
    def visit(self, node):
        # awesome
        method_name = 'visit_' + type(node).__name__
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception('No visit_{} method'.format(type(node).__name__))


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
--------   symbol：type checking & variable declared     ------------
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


class Symbol(object):
    def __init__(self, name, type=None):
        self.name = name
        self.type = type


class BuiltinTypeSymbol(Symbol):
    def __init__(self, name):
        super(BuiltinTypeSymbol, self).__init__(name)

    def __str__(self):
        return self.name

    def __repr__(self):
        return "<{class_name}(name='{name}')>".format(
            class_name=self.__class__.__name__,
            name=self.name,
        )


class VarSymbol(Symbol):
    def __init__(self, name, type):
        super().__init__(name, type)

    def __str__(self):
        return "<{class_name}(name='{name}', type='{type}')>".format(
            class_name=self.__class__.__name__,
            name=self.name,
            type=self.type,
        )

    __repr__ = __str__


class ProcedureSymbol(Symbol):
    def __init__(self, name, params=None):
        super().__init__(name)
        self.params = params if params is not None else []

    def __str__(self):
        return '<{class_name}(name={name}, parameters={params})>'.format(
            class_name=self.__class__.__name__,
            name=self.name,
            params=self.params,
        )

    __repr__ = __str__


# track symbol
# a abstract data type for tracking various symbols
class ScopedSymbolTable(object):
    def __init__(self, scope_name, scope_level, enclosing_scope=None):
        self._symbols = {}
        self.scope_name = scope_name  # scope name
        self.scope_level = scope_level  # scope level
        self.enclosing_scope = enclosing_scope

    def _init_builtins(self):
        """built in type
        INTEGER & REAL
        """
        self.insert(BuiltinTypeSymbol('INTEGER'))
        self.insert(BuiltinTypeSymbol('REAL'))

    def __str__(self):
        h1 = 'SCOPE (SCOPED SYMBOL TABLE)'
        lines = ['\n', h1, '=' * len(h1)]
        for header_name, header_value in (
                ('Scope name', self.scope_name),
                ('Scope level', self.scope_level),
                ('Enclosing scope', self.enclosing_scope.scope_name if self.enclosing_scope else None)
        ):
            lines.append('%-15s: %s' % (header_name, header_value))
        h2 = 'Scope (Scoped symbol table) contents'
        lines.extend([h2, '-' * len(h2)])
        lines.extend(
            ('%7s: %r' % (key, value))
            for key, value in self._symbols.items()
        )
        lines.append('\n')
        s = '\n'.join(lines)
        return s

    __repr__ = __str__

    def insert(self, symbol):
        """insert a symbol"""

        print('Insert: %s' % symbol.name)
        self._symbols[symbol.name] = symbol

    def lookup(self, name, current_scope_only=False):
        """find symbol if existed"""

        print('Lookup: %s. (Scope name: %s)' % (name, self.scope_name))
        symbol = self._symbols.get(name)
        if symbol is not None:
            return symbol
        if current_scope_only:
            return None

        if self.enclosing_scope is not None:
            return self.enclosing_scope.lookup(name)


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
--------------------    SemanticAnalyzer     ------------------------
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


# visit all ast node parse by parser
class SemanticAnalyzer(NodeVisitor):
    def __init__(self):
        self.current_scope = None

    def error(self, error_code, token):
        return SemanticError(
            error_code=error_code,
            token=token,
            message=f'{error_code.value} -> {token}',
        )

    def visit_Program(self, node):
        print('ENTER scope: global')
        global_scope = ScopedSymbolTable(
            scope_name='global',
            scope_level=1,
            enclosing_scope=self.current_scope,
        )
        global_scope._init_builtins()
        self.current_scope = global_scope

        # visit sub block
        self.visit(node.block)

        print(global_scope)
        self.current_scope = self.current_scope.enclosing_scope
        print('LEAVE scope: global')

    def visit_Block(self, node):
        for declaration in node.declarations:
            self.visit(declaration)
        self.visit(node.compound_statement)

    def visit_VarDecl(self, node):
        """variable declaration"""
        type_name = node.type_node.value
        # if existed this type
        type_symbol = self.current_scope.lookup(type_name)
        var_name = node.var_node.value
        # insert the current var
        var_symbol = VarSymbol(var_name, type_symbol)

        # if this symbol already declaration, error
        if self.current_scope.lookup(var_name, current_scope_only=True):
            self.error(
                error_code=ErrorCode.DUPLICATE_ID,
                token=node.var_node.token,
            )
        self.current_scope.insert(var_symbol)

    def visit_ProcedureDecl(self, node):
        proc_name = node.proc_name
        proc_symbol = ProcedureSymbol(proc_name)
        # insert current scope
        self.current_scope.insert(proc_symbol)

        print(f'ENTER scope: {proc_name}')

        # Scope for parameters and local variables
        procedure_scope = ScopedSymbolTable(
            scope_name=proc_name,
            scope_level=self.current_scope.scope_level + 1,
            enclosing_scope=self.current_scope

        )
        self.current_scope = procedure_scope

        # Insert parameters into the procedure scope
        for param in node.params:
            # find current scope params
            param_type = self.current_scope.lookup(param.type_node.value)
            param_name = param.var_node.value
            var_symbol = VarSymbol(param_name, param_type)
            self.current_scope.insert(var_symbol)
            proc_symbol.params.append(var_symbol)

        self.visit(node.block_node)

        print(procedure_scope)
        self.current_scope = self.current_scope.enclosing_scope
        print(f'LEAVE scope: %s {proc_name}')

    def visit_ProcedureCall(self, node):
        for param_node in node.actual_params:
            self.visit(param_node)

    def visit_Compound(self, node):
        for child in node.children:
            self.visit(child)

    def visit_Assign(self, node):
        self.visit(node.right)
        self.visit(node.left)

    def visit_Var(self, node):
        var_name = node.value

        # search if have this node
        var_symbol = self.current_scope.lookup(var_name)

        # can not find this var define
        if var_symbol is None:
            self.error(error_code=ErrorCode.ID_NOT_FOUND, token=node.token)

    def visit_Num(self, node):
        pass

    def visit_BinOp(self, node):
        self.visit(node.left)
        self.visit(node.right)

    def visit_UnaryOp(self, node):
        pass

    def visit_NoOp(self, node):
        pass


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
--------------------    interpreter     -------------------------
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


class CallStack:
    def __init__(self):
        self._records = []

    def push(self, ar):
        self._records.append(ar)

    def pop(self):
        return self._records.pop()

    def peek(self):
        return self._records[-1]

    def __str__(self):
        s = '\n'.join(repr(ar) for ar in reversed(self._records))
        s = f'CALL STACK\n{s}\n'
        return s

    def __repr__(self):
        return self.__str__()


class ARType(Enum):
    PROGRAM = 'PROGRAM'


class ActivationRecord:
    def __init__(self, name, type, nesting_level):
        self.name = name
        self.type = type
        self.nesting_level = nesting_level
        self.members = {}

    def __setitem__(self, key, value):
        self.members[key] = value

    def __getitem__(self, key):
        return self.members[key]

    def get(self, key):
        return self.members.get(key)

    def __str__(self):
        lines = [
            '{level}: {type} {name}'.format(
                level=self.nesting_level,
                type=self.type.value,
                name=self.name,
            )
        ]
        for name, val in self.members.items():
            lines.append(f'   {name:<20}: {val}')

        s = '\n'.join(lines)
        return s

    def __repr__(self):
        return self.__str__()


class Interpreter(NodeVisitor):

    def __init__(self, tree):
        self.tree = tree
        self.call_stack = CallStack()

    def interpret(self):
        tree = self.tree
        if tree is None:
            return ''
        return self.visit(tree)

    def visit_Program(self, node):
        program_name = node.name
        print(f'ENTER: PROGRAM {program_name}')

        ar = ActivationRecord(
            name=program_name,
            type=ARType.PROGRAM,
            nesting_level=1,
        )
        self.call_stack.push(ar)

        self.visit(node.block)

        print(f'LEAVE: PROGRAM {program_name}')
        print(str(self.call_stack))

        self.call_stack.pop()

    def visit_Block(self, node):
        for declaration in node.declarations:
            self.visit(declaration)
        self.visit(node.compound_statement)

    def visit_VarDecl(self, node):
        # Do nothing
        pass

    def visit_ProcedureDecl(self, node):
        pass

    def visit_ProcedureCall(self, node):
        pass

    def visit_Compound(self, node):
        for child in node.children:
            self.visit(child)

    def visit_Assign(self, node):
        var_name = node.left.value
        # save the var value,so use it sometimes
        ar = self.call_stack.peek()
        ar[var_name] = self.visit(node.right)

    def visit_Var(self, node):
        var_name = node.value
        ar = self.call_stack.peek()
        val = ar.get(var_name)
        return val

    def visit_Type(self, node):
        # Do nothing
        pass

    def visit_NoOp(self, node):
        pass

    def visit_BinOp(self, node):
        """calc the value
        """
        if node.op.type == TokenType.PLUS:
            return self.visit(node.left) + self.visit(node.right)
        elif node.op.type == TokenType.MINUS:
            return self.visit(node.left) - self.visit(node.right)
        elif node.op.type == TokenType.MUL:
            return self.visit(node.left) * self.visit(node.right)
        elif node.op.type == TokenType.INTEGER_DIV:
            return self.visit(node.left) // self.visit(node.right)
        elif node.op.type == TokenType.FLOAT_DIV:
            return float(self.visit(node.left)) / float(self.visit(node.right))

    def visit_UnaryOp(self, node):
        op = node.op.type
        if op == TokenType.PLUS:
            return +self.visit(node.expr)
        elif op == TokenType.MINUS:
            return -self.visit(node.expr)

    def visit_Num(self, node):
        return node.value
