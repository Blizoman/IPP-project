from interpreter.input_model import Expr, Literal, Send
from interpreter.sol_objects import SolObject, SolInteger, SolString, SolBlock, SOL_TRUE, SOL_FALSE, SOL_NIL
from interpreter.environment import Environment
from interpreter.exceptions import SemanticError
from interpreter.error_codes import ErrorCode

class Evaluator:
    def __init__(self):
        ...

    def literal(self, type: str, value: str) -> SolObject:
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
            raise ErrorCode(0x00F) # TODO: err fix
    
    def variable(self, name: str) -> SolObject:
        return Environment.get(name)
        
        
