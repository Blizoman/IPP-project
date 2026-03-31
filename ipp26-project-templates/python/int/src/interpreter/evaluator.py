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


class MessageDispatcher(Protocol):
    """Runtime contract required by Evaluator for dispatching message sends."""

    def send_message(
        self, receiver: SolObject, selector: str, args: list[SolObject], environment: Environment
    ) -> SolObject: ...


class Evaluator:
    def __init__(self, dispatcher: MessageDispatcher) -> None:
        self.dispatcher = dispatcher

    def eval_literal(self, literal_type: str, value: str) -> SolObject:
        if literal_type == "Integer":
            return SolInteger(int(value))
        if literal_type == "String":
            return SolString(value)
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

    def eval_variable(self, name: str, environment: Environment) -> SolObject:
        return environment.get(name)

    def eval_block(self, ast_node: Block, environment: Environment) -> SolBlock:
        return SolBlock(ast_node, environment)

    def eval_send(self, ast_node: Send, environment: Environment) -> SolObject:
        receiver = self.evaluate(ast_node.receiver, environment)

        arguments = []
        for arg in ast_node.args:
            arg_val = self.evaluate(arg.expr, environment)
            if isinstance(arg_val, SolWrapper):
                arg_val = arg_val.actual_receiver
            arguments.append(arg_val)

        return self.dispatcher.send_message(receiver, ast_node.selector, arguments, environment)

    def evaluate(self, expr: Expr, environment: Environment) -> SolObject:
        if expr.literal:
            return self.eval_literal(expr.literal.class_id, expr.literal.value)
        if expr.var:
            return self.eval_variable(expr.var.name, environment)
        if expr.block:
            return self.eval_block(expr.block, environment)
        if expr.send:
            return self.eval_send(expr.send, environment)

        raise InterpreterError(ErrorCode.INT_OTHER, "Expression has no evaluable value")
