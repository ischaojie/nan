"""the main"""
import argparse
import sys

from error import LexerError, ParserError, SemanticError
from interpreter import SemanticAnalyzer, Interpreter
from lexer import Lexer
from parser import Parser


def main():
    parser = argparse.ArgumentParser(
        description='SPI - Simple Pascal Interpreter'
    )
    parser.add_argument('inputfile', help='Pascal source file')
    parser.add_argument(
        '--scope',
        help='Print scope information',
        action='store_true',
    )
    args = parser.parse_args()
    global _SHOULD_LOG_SCOPE
    _SHOULD_LOG_SCOPE = args.scope

    text = open(args.inputfile, 'r').read()

    lexer = Lexer(text)
    try:
        parser = Parser(lexer)
        tree = parser.parse()
    except (LexerError, ParserError) as e:
        print(e.message)
        sys.exit(1)

    semantic_analyzer = SemanticAnalyzer()
    try:
        semantic_analyzer.visit(tree)
    except SemanticError as e:
        print(e.message)
        sys.exit(1)

    interpreter = Interpreter(tree)
    interpreter.interpret()


if __name__ == '__main__':
    main()
