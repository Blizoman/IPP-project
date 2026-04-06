"""
This module defines the custom exception classes used by the interpreter to represent various error
conditions that can occur during interpretation.

IPP: You can freely modify this file and add any additional exception classes.
     However, the InterpreterError class must be used as a base for any exceptions that control
     the outcome of the interpretation (i.e., those that are caught in solint.py and cause
     the interpreter to exit with a specific error code).

Author: Ondřej Ondryáš <iondryas@fit.vut.cz>
Author: Andrej Bližnák <xblizna00@fit.vut.cz>
"""

from interpreter.error_codes import ErrorCode


# ===========================================================
# GENERAL ERROR CLASS
# ===========================================================
class InterpreterError(Exception):
    """
    A general exception class for errors that occur during interpretation.
    It includes an error code enum instance that can be used to determine the appropriate
    exit code for the program.
    """

    def __init__(self, error_code: ErrorCode, message: str | None = None) -> None:
        """Initialize the base interpreter error. (Added bcs linter)"""
        super().__init__(message)
        self.error_code = error_code


# ===========================================================
# SEMANTIC ERROR CLASS
# ===========================================================
class SemanticError(InterpreterError):
    """
    An exception class for static/semantic errors (represented as 31-35)
    """

    def __init__(self, code: ErrorCode) -> None:
        """Initialize a semantic error with a specific error code"""
        super().__init__(error_code=code, message=f"Static semantic error: {code.name}")


# ===========================================================
# RUNTIME ERROR CLASSES
# ===========================================================
class MessageNotUnderstoodError(InterpreterError):
    """Exception for code 51 - `Receiver does not understand a message`"""

    def __init__(self, message: str = "Message not understood") -> None:
        """Initialize a message not understood error"""
        super().__init__(error_code=ErrorCode.INT_DNU, message=message)


class RuntimeTypeError(InterpreterError):
    """Exception for code 52 - `Runtime errors as .: WrongTypes/...`"""

    def __init__(self, message: str = "Runtime type/operation error") -> None:
        """Initialize a generic runtime type or operation error."""
        super().__init__(error_code=ErrorCode.INT_OTHER, message=message)


class InvalidArgumentError(InterpreterError):
    """Exception for code 53 - `Wrong value of argument .: DivisionByZero/...`"""

    def __init__(self, message: str = "Invalid argument value") -> None:
        """Initialize an invalid argument error"""
        super().__init__(error_code=ErrorCode.INT_INVALID_ARG, message=message)


class AttributeCollisionError(InterpreterError):
    """Exception for code 54 - `Collide error .: Method-X-Attribute`"""

    def __init__(self, message: str = "Instance attribute collides with a method") -> None:
        """Initialize an attribute collision error"""
        super().__init__(error_code=ErrorCode.INT_INST_ATTR, message=message)
