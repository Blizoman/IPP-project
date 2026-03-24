from typing import Protocol

from interpreter.input_model import Expr, Literal, Send, Block
from interpreter.sol_objects import SolObject, SolInteger, SolString, SolBlock, SOL_TRUE, SOL_FALSE, SOL_NIL
from interpreter.environment import Environment
from interpreter.exceptions import InterpreterError
from interpreter.error_codes import ErrorCode


class MessageDispatcher(Protocol):
    def send_message(
        self,
        receiver: SolObject,
        selector: str,
        args: list[SolObject],
        environment: Environment,
    ) -> SolObject:
        ...

class Evaluator:
    def __init__(self, dispatcher: MessageDispatcher) -> None:
        self.dispatcher = dispatcher          
        

    def eval_literal(self, type: str, value: str) -> SolObject:
        if type == "Integer":
            return SolInteger(int(value))
        elif type == "String":
            return SolString(value)
        elif type == "True":
            return SOL_TRUE
        elif type == "False":
            return SOL_FALSE
        elif type == "Nil":
            return SOL_NIL
        elif type == "class":
            return SolString(value) # TODO: fix classes
        else:
            raise InterpreterError(ErrorCode.INT_OTHER, f"Unknown literal class: {type}")
    
    def eval_variable(self, name: str, environment: Environment) -> SolObject:
        return environment.get(name)
    
    def eval_block(self, ast_node: Block, environment: Environment) -> SolBlock:
        return SolBlock(ast_node, environment)
    
    def eval_send(self, ast_node: Send, environment: Environment) -> SolObject:
        receiver = self.evaluate(ast_node.receiver, environment)

        arguments = []
        for arg in ast_node.args:
            arguments.append(self.evaluate(arg.expr, environment))
        
        return self.dispatcher.send_message(receiver, ast_node.selector, arguments, environment)
    
    def evaluate(self, expr: Expr, environment: Environment) -> SolObject:
        if expr.literal:
            return self.eval_literal(expr.literal.class_id, expr.literal.value)
        elif expr.var:
            return self.eval_variable(expr.var.name, environment)
        elif expr.block:
            return self.eval_block(expr.block, environment)
        elif expr.send:
            return self.eval_send(expr.send, environment)
        else:
            raise InterpreterError(ErrorCode.INT_OTHER, "Expression has no evaluable value")



        
        
        
