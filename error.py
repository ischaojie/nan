"""errors"""

from enum import Enum


class ErrorCode(Enum):
    UNEXPECTED_TOKEN = 'Unexpected token'
    ID_NOT_FOUND = 'Identifier not found'
    DUPLICATE_ID = 'Duplicate id found'


class Error(Exception):
    def __init__(self, error_code=None, token=None, message=None):
        self.error_code = error_code  # error code
        self.token = token  # token
        self.message = f'{self.__class__.__name__}: {message}'  # error message


class LexerError(Error):
    pass


class ParserError(Error):
    pass


class SemanticError(Error):
    pass
