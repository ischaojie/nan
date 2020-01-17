"""
Parser
parser the AST node

"""
import ast

from error import ParserError, ErrorCode
from token import TokenType


class Parser(object):

    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = self.get_next_token()

    def error(self, error_code, token):
        raise ParserError(
            error_code=error_code,
            token=token,
            message=f'{error_code.value} -> {token}'
        )

    def get_next_token(self):
        return self.lexer.get_next_token()

    def eat(self, token_type):
        """function eat the current token and get next token.
        """
        if self.current_token.type == token_type:
            self.current_token = self.get_next_token()
        else:
            self.error(
                error_code=ErrorCode.UNEXPECTED_TOKEN,
                token=self.current_token
            )

    def parse(self):
        """the parser"""
        node = self.program()
        if self.current_token.type != TokenType.EOF:
            self.error(
                error_code=ErrorCode.UNEXPECTED_TOKEN,
                token=self.current_token
            )

        return node

    def factor(self):
        """factor : PLUS factor
                  | MINUS factor
                  | INTEGER_CONST
                  | REAL_CONST
                  | LPAREN expr RPAREN
                  | variable

        factor calc plus or minus
        """
        token = self.current_token
        # +
        if token.type == TokenType.PLUS:
            self.eat(TokenType.PLUS)
            return ast.UnaryOp(token, self.factor())
        # -
        elif token.type == TokenType.MINUS:
            self.eat(TokenType.MINUS)
            return ast.UnaryOp(token, self.factor())
        # int
        elif token.type == TokenType.INTEGER_CONST:
            self.eat(TokenType.INTEGER_CONST)
            return ast.Num(token)
        # float
        elif token.type == TokenType.REAL_CONST:
            self.eat(TokenType.REAL_CONST)
            return ast.Num(token)
        # (
        elif token.type == TokenType.LPAREN:
            self.eat(TokenType.LPAREN)
            node = self.expr()
            self.eat(TokenType.RPAREN)
            return node
        else:
            return self.variable()

    def term(self):
        """term : factor ((MUL | INTEGER_DIV | FLOAT_DIV) factor)*
        """
        node = self.factor()

        while self.current_token.type in (
                TokenType.MUL,
                TokenType.INTEGER_DIV,
                TokenType.FLOAT_DIV
        ):
            token = self.current_token
            if token.type == TokenType.MUL:
                self.eat(TokenType.MUL)
            elif token.type == TokenType.INTEGER_DIV:
                self.eat(TokenType.INTEGER_DIV)
            elif token.type == TokenType.FLOAT_DIV:
                self.eat(TokenType.FLOAT_DIV)

            node = ast.BinOp(left=node, op=token, right=self.factor())

        return node

    def expr(self):
        """expr : term ((PLUS | MINUS) term)*
        """
        node = self.term()
        while self.current_token.type in (TokenType.PLUS, TokenType.MINUS):
            token = self.current_token
            if token.type == TokenType.PLUS:
                self.eat(TokenType.PLUS)
            elif token.type == TokenType.MINUS:
                self.eat(TokenType.MINUS)

            node = ast.BinOp(left=node, op=token, right=self.term())
        return node

    """""""""""""""""""""""""""""""""""""""""
    --------    parser ast node    ---------
    """""""""""""""""""""""""""""""""""""""""

    def program(self):
        """program : PROGRAM variable SEMI block DOT
        """
        self.eat(TokenType.PROGRAM)
        # get the program name
        var_node = self.variable()
        program_name = var_node.value
        # ;
        self.eat(TokenType.SEMI)
        # block
        block_node = self.block()
        program_node = ast.Program(program_name, block_node)
        # .
        self.eat(TokenType.DOT)
        return program_node

    def block(self):
        """block : declarations compound_statement
        """

        # declarations
        declaration_nodes = self.declarations()
        # compound BEGIN...END
        compound_statement_node = self.compound_statement()
        node = ast.Block(declaration_nodes, compound_statement_node)
        return node

    """declarations: var decl or procedure decl"""

    def declarations(self):
        """declarations : VAR(variable_declaration SEMI) +
                     | (PROCEDURE ID (LPAREN formal_parameter_list RPAREN)? SEMI block SEMI) *
                     | empty
        """
        declarations = []

        # start var decl
        # if current token is a var
        # var a : INTEGER;
        if self.current_token.type == TokenType.VAR:
            # eat VAR
            self.eat(TokenType.VAR)
            # add all var declarations
            while self.current_token.type == TokenType.ID:
                var_decl = self.variable_declaration()
                declarations.extend(var_decl)
                self.eat(TokenType.SEMI)

        # start procedure decl
        # procedure pro;
        while self.current_token.type == TokenType.PROCEDURE:
            proc_decl = self.procedure_declaration()
            # add procedure declaration to declarations
            declarations.append(proc_decl)

        return declarations

    def variable_declaration(self):
        """variable_declaration : ID (COMMA ID)* COLON type_spec
        VAR
            a : INTEGER;
            b : REAL;
        """

        var_nodes = [ast.Var(self.current_token)]
        self.eat(TokenType.ID)

        # while contain ',' just like var a,b,c : INTEGER;
        while self.current_token.type == TokenType.COMMA:
            self.eat(TokenType.COMMA)
            var_nodes.append(ast.Var(self.current_token))
            self.eat(TokenType.ID)
        # :
        self.eat(TokenType.COLON)

        # type special int or float
        type_node = self.type_spec()
        # [a, INTEGER], [b, INTEGER] [c, float]
        var_declarations = [
            ast.VarDecl(var_node, type_node)
            for var_node in var_nodes
        ]
        return var_declarations

    def procedure_declaration(self):
        """procedure_declaration :
             PROCEDURE ID (LPAREN formal_parameter_list RPAREN)? SEMI block SEMI
        """
        self.eat(TokenType.PROCEDURE)
        proc_name = self.current_token.value
        self.eat(TokenType.ID)

        params = []
        if self.current_token.type == TokenType.LPAREN:
            self.eat(TokenType.LPAREN)
            params = self.formal_parameter_list()
            self.eat(TokenType.RPAREN)

        self.eat(TokenType.SEMI)
        block_node = self.block()
        proc_decl = ast.ProcedureDecl(proc_name, params, block_node)
        self.eat(TokenType.SEMI)
        return proc_decl

    def empty(self):
        return ast.NoOp()

    """procedure's formal parameters"""

    def formal_parameter_list(self):
        """ formal_parameter_list : formal_parameters
                                  | formal_parameters SEMI formal_parameter_list

        procedure Foo(a, b : INTEGER; c : REAL);
        """
        if not self.current_token.type == TokenType.ID:
            return []

        param_nodes = self.formal_parameters()

        # while contain ':'
        while self.current_token.type == TokenType.SEMI:
            self.eat(TokenType.SEMI)
            param_nodes.extend(self.formal_parameters())
        return param_nodes

    def formal_parameters(self):
        """ formal_parameters : ID (COMMA ID)* COLON type_spec

        procedure's params, just like Foo(a, b : int)
        current process is a, b : int
        """
        param_nodes = []
        param_tokens = [self.current_token]
        self.eat(TokenType.ID)
        # while contain ','
        while self.current_token.type == TokenType.COMMA:
            self.eat(TokenType.COMMA)
            # add all ID
            param_tokens.append(self.current_token)
            self.eat(TokenType.ID)
        # eat ':'
        self.eat(TokenType.COLON)

        # start params type
        type_node = self.type_spec()
        for param_token in param_tokens:
            var = ast.Var(param_token)
            param_node = ast.Param(var, type_node)
            param_nodes.append(param_node)
        return param_nodes

    def type_spec(self):
        """type_spec : INTEGER
                     | REAL
        """
        token = self.current_token
        if self.current_token.type == TokenType.INTEGER:
            self.eat(TokenType.INTEGER)
        else:
            self.eat(TokenType.REAL)
        node = ast.Type(token)
        return node

    def proccall_statement(self):
        """proccall_statement : ID LPAREN (expr (COMMA expr)*)? RPAREN
        foo(3+5, 2)
        foo(a)
        """

        token = self.current_token
        proc_name = self.current_token.value
        self.eat(TokenType.ID)
        self.eat(TokenType.LPAREN)

        actual_params = []
        # append all actual params
        if self.current_token.type != TokenType.LPAREN:
            node = self.expr()
            actual_params.append(node)

        while self.current_token.type == TokenType.COMMA:
            self.eat(TokenType.COMMA)
            node = self.expr()
            actual_params.append(node)

        self.eat(TokenType.RPAREN)

        node = ast.ProcedureCall(proc_name, actual_params, token)
        return node

    def compound_statement(self):
        """compound_statement: BEGIN statement_list END
        """
        self.eat(TokenType.BEGIN)
        nodes = self.statement_list()
        self.eat(TokenType.END)

        root = ast.Compound()
        for node in nodes:
            root.children.append(node)

        return root

    def statement_list(self):
        """statement_list : statement
                        | statement SEMI statement_list
        """
        node = self.statement()
        results = [node]
        # 分号
        while self.current_token.type == TokenType.SEMI:
            self.eat(TokenType.SEMI)
            # add the statement
            results.append(self.statement())

        return results

    def statement(self):
        """statement : compound_statement
                     | proccall_statement
                     | assignment_statement
                     | empty
        """
        if self.current_token.type == TokenType.BEGIN:
            node = self.compound_statement()
        elif self.current_token.type == TokenType.ID and self.lexer.current_char == '(':
            node = self.proccall_statement()
        elif self.current_token.type == TokenType.ID:
            node = self.assignment_statement()
        else:
            node = self.empty()
        return node

    def assignment_statement(self):
        """assignment_statement : variable ASSIGN expr
        just like a := 1;
        """
        left = self.variable()
        token = self.current_token
        # :=
        self.eat(TokenType.ASSIGN)
        right = self.expr()
        node = ast.Assign(left, token, right)
        return node

    def variable(self):
        """variable : ID
        """
        node = ast.Var(self.current_token)
        self.eat(TokenType.ID)
        return node
