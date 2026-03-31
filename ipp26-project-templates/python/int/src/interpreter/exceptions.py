"""
This module defines the custom exception classes used by the interpreter to represent various error
conditions that can occur during interpretation.

IPP: You can freely modify this file and add any additional exception classes.
     However, the InterpreterError class must be used as a base for any exceptions that control
     the outcome of the interpretation (i.e., those that are caught in solint.py and cause
     the interpreter to exit with a specific error code).

Author: Ondřej Ondryáš <iondryas@fit.vut.cz>
"""

from interpreter.error_codes import ErrorCode


class InterpreterError(Exception):
    """
    A general exception class for errors that occur during interpretation.
    It includes an error code enum instance that can be used to determine the appropriate
    exit code for the program.
    """

    def __init__(self, error_code: ErrorCode, message: str | None = None) -> None:
        super().__init__(message)
        self.error_code = error_code


# ===========================================================
# Semantic Error CLass
# ===========================================================
class SemanticError(InterpreterError):
    def __init__(self, code: ErrorCode) -> None:
        super().__init__(error_code=code, message=f"Static semantic error: {code.name}")


# ===========================================================
# Runtime Errors (5x) - Používať v dispatcher.py, evaluator.py atď.
# ===========================================================
class MessageNotUnderstoodError(InterpreterError):
    """Kód 51: Príjemca nerozumie zaslanej správe."""

    def __init__(self, message: str = "Message not understood") -> None:
        super().__init__(error_code=ErrorCode.INT_DNU, message=message)


class RuntimeTypeError(InterpreterError):
    """Kód 52: Iné behové chyby (napr. zlé typy operandov pre operácie)."""

    def __init__(self, message: str = "Runtime type/operation error") -> None:
        super().__init__(error_code=ErrorCode.INT_OTHER, message=message)


class InvalidArgumentError(InterpreterError):
    """Kód 53: Zlá hodnota argumentu (napr. delenie nulou, zlý from:)."""

    def __init__(self, message: str = "Invalid argument value") -> None:
        super().__init__(error_code=ErrorCode.INT_INVALID_ARG, message=message)


class AttributeCollisionError(InterpreterError):
    """Kód 54: Pokus o vytvorenie instančného atribútu, ktorý koliduje s metódou."""

    def __init__(self, message: str = "Instance attribute collides with a method") -> None:
        super().__init__(error_code=ErrorCode.INT_INST_ATTR, message=message)
