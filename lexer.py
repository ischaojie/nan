"""
Lexer
"""
from error import LexerError
from token import Token, RESERVED_KEYWORDS, TokenType


# lexer
class Lexer(object):
    def __init__(self, text):
        self.text = text  # the program character
        self.pos = 0  # position
        self.current_char = self.text[self.pos]  # the current character

        self.lineno = 1  # line number
        self.column = 1  # column number

    def error(self):
        s = "Lexer error on '{lexeme}' line: {lineno} column: {column}".format(
            lexeme=self.current_char,
            lineno=self.lineno,
            column=self.column,
        )
        raise LexerError(message=s)

    def advance(self):
        """advance the pos pointer
        set current character, and current line number, column number
        """
        if self.current_char == '\n':
            self.lineno += 1
            self.column = 0

        self.pos += 1
        if self.pos > len(self.text) - 1:
            self.current_char = None
        else:
            self.current_char = self.text[self.pos]
            self.column += 1

    def peek(self):
        """get the next current character
        it's for multi-char, just like ':=' or '//' token
        """
        peek_pos = self.pos + 1
        if peek_pos > len(self.text) - 1:
            return None
        else:
            return self.text[peek_pos]

    def skip_whitespace(self):
        """skip the whitespace
        """
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def skip_comment(self):
        """skip the comment
        """
        while self.current_char != '}':
            self.advance()
        self.advance()

    def number(self):
        """function get the multi-number like float or int token.
        for example: '12345' or '32.1213'

        """
        token = Token(type=None, value=None, lineno=self.lineno, column=self.column)

        result = ''
        # while character is digit
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        # if character is '.' , means float number
        if self.current_char == '.':
            result += self.current_char
            self.advance()

            while self.current_char is not None and self.current_char.isdigit():
                result += self.current_char
                self.advance()

            token.type = TokenType.REAL_CONST
            token.value = float(result)
        else:
            token.type = TokenType.INTEGER_CONST
            token.value = int(result)

        return token

    def _id(self):
        """function get reversed-keywords or multi-char.
        if current char is reversed-kw, get it, or multi-char.

        for example: keywords like 'PROGRAM or VAR or BEGIN ...'
        or 'a, b, i, j ...'
        """
        token = Token(type=None, value=None, lineno=self.lineno, column=self.column)
        result = ''
        # while char is digit or letter
        while self.current_char is not None and self.current_char.isalnum():
            result += self.current_char
            self.advance()
        # if reversed keywords is None, get the current result
        token_type = RESERVED_KEYWORDS.get(result.upper())
        if token_type is None:
            token.type = TokenType.ID
            token.value = result
        else:
            # reserved keyword
            token.type = token_type
            token.value = result.upper()

        return token

    def get_next_token(self):
        """function one and one get net token, breaking a sentence apart into tokens
        It's return the current token by choice current char.
        """

        while self.current_char is not None:

            # comment start '{'
            if self.current_char == '{':
                self.advance()
                self.skip_comment()
                continue

            # skip space
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            # get number token
            if self.current_char.isdigit():
                return self.number()

            # get id token
            if self.current_char.isalpha():
                return self._id()

            # assign :=
            # a := 10
            if self.current_char == ':' and self.peek() == '=':
                token = Token(
                    type=TokenType.ASSIGN,
                    value=TokenType.ASSIGN.value,  # ':='
                    lineno=self.lineno,
                    column=self.column,
                )
                self.advance()
                self.advance()
                return token

            # get colon token
            # like: a : int
            if self.current_char == ':' and self.peek() != '=':
                self.advance()
                return Token(TokenType.COLON, ':', self.lineno, self.column)
            # ;
            if self.current_char == ';':
                self.advance()
                return Token(TokenType.SEMI, ';', self.lineno, self.column)

            # .
            if self.current_char == '.':
                self.advance()
                return Token(TokenType.DOT, '.', self.lineno, self.column)

            # ,
            if self.current_char == ',':
                self.advance()
                return Token(TokenType.COMMA, ',', self.lineno, self.column)

            if self.current_char == '+':
                self.advance()
                token = Token(TokenType.PLUS, '+', self.lineno, self.column)
                return token

            if self.current_char == '-':
                self.advance()
                token = Token(TokenType.MINUS, '-', self.lineno, self.column)
                return token

            if self.current_char == '*':
                self.advance()
                return Token(TokenType.MUL, '*', self.lineno, self.column)

            if self.current_char == '/' and self.peek() == '/':
                self.advance()
                self.advance()
                return Token(TokenType.INTEGER_DIV, '//', self.lineno, self.column)

            if self.current_char == '/':
                self.advance()
                return Token(TokenType.FLOAT_DIV, '/', self.lineno, self.column)

            if self.current_char == '(':
                self.advance()
                return Token(TokenType.LPAREN, '(', self.lineno, self.column)

            if self.current_char == ')':
                self.advance()
                return Token(TokenType.RPAREN, ')', self.lineno, self.column)

            self.error()
        # end of file
        return Token(TokenType.EOF, None)
