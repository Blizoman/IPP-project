"""
This module defines the Evaluator responsible for processing AST expressions
into runtime SOL26 objects.

Author: Andrej Bližnák <xblizna00@fit.vut.cz>
"""

from typing import Protocol

from interpreter.environment import Environment
from interpreter.error_codes import ErrorCode
from interpreter.exceptions import InterpreterError
from interpreter.input_model import Block, Expr, Send
from interpreter.sol_objects import (
    SOL_FALSE,
    SOL_NIL,
    SOL_TRUE,
    SolBlock,
    SolClass,
    SolInteger,
    SolObject,
    SolString,
    SolWrapper,
)


# ===========================================================
# DISPATCHER PROTOCOL
# ===========================================================
class MessageDispatcher(Protocol):
    """Runtime contract required by Evaluator for dispatching message sends."""

    def send_message(
        self, receiver: SolObject, selector: str, args: list[SolObject], environment: Environment
    ) -> SolObject:
        """Contract: Route message to the actual dispatcher implementation."""
        ...


# ===========================================================
# EVALUATOR ENGINE
# ===========================================================
class Evaluator:
    """Main/Core component: Translates static AST nodes into live memory objects."""

    def __init__(self, dispatcher: MessageDispatcher) -> None:
        """Initialization of Evaluator with reference to MessageDispatcher."""
        self.dispatcher = dispatcher

    @staticmethod
    def _decode_string_literal(value: str) -> str:
        """Decode the string escapes supported by SOL26 literals."""
        escape_map = {"n": "\n", "'": "'", "\\": "\\"}
        decoded: list[str] = []
        i = 0

        while i < len(value):
            if value[i] == "\\" and i + 1 < len(value):
                escaped = value[i + 1]
                mapped = escape_map.get(escaped)
                if mapped is not None:
                    decoded.append(mapped)
                    i += 2
                    continue

            decoded.append(value[i])
            i += 1

        return "".join(decoded)

    def _eval_literal(self, literal_type: str, value: str) -> SolObject:
        """Transform: AST Literal node to corresponding SOL26 memory object."""
        if literal_type == "Integer":
            return SolInteger(int(value))
        if literal_type == "String":
            return SolString(self._decode_string_literal(value))
        if literal_type == "True":
            return SOL_TRUE
        if literal_type == "False":
            return SOL_FALSE
        if literal_type == "Nil":
            return SOL_NIL
        if literal_type == "class":
            return SolClass(value)

        raise InterpreterError(
            ErrorCode.INT_OTHER,
            f"Unknown literal class: {literal_type}",
        )

    def _eval_variable(self, name: str, environment: Environment) -> SolObject:
        """Retrieve: Variable value from current memory Environment."""
        return environment.get(name)

    def _eval_block(self, ast_node: Block, environment: Environment) -> SolBlock:
        """Transform: AST Block node to live SOL26 Block (Closure)."""
        return SolBlock(ast_node, environment)

    def _eval_send(self, ast_node: Send, environment: Environment) -> SolObject:
        """Evaluate: Receiver and arguments, unwrap proxies, and dispatch message."""
        receiver = self.evaluate(ast_node.receiver, environment)

        arguments = []
        for arg in ast_node.args:
            arg_val = self.evaluate(arg.expr, environment)
            # Un-wrap "super"
            if isinstance(arg_val, SolWrapper):
                arg_val = arg_val.actual_receiver
            arguments.append(arg_val)

        return self.dispatcher.send_message(receiver, ast_node.selector, arguments, environment)

    def evaluate(self, expr: Expr, environment: Environment) -> SolObject:
        """Route: Given AST expression to its specific evaluation method."""
        if expr.literal:
            return self._eval_literal(expr.literal.class_id, expr.literal.value)
        if expr.var:
            return self._eval_variable(expr.var.name, environment)
        if expr.block:
            return self._eval_block(expr.block, environment)
        if expr.send:
            return self._eval_send(expr.send, environment)

        raise InterpreterError(ErrorCode.INT_OTHER, "Expression has no evaluable value")
