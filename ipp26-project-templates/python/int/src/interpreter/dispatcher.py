from interpreter.sol_objects import SolObject, SolInteger, SolString, SolBlock, SOL_TRUE, SOL_FALSE, SOL_NIL
from interpreter.environment import Environment
from interpreter.evaluator import Evaluator
from interpreter.error_codes import ErrorCode
from interpreter.exceptions import SemanticError

class Dispatcher:
    def __init__(self, program: 'Program') -> None:
        self.program = program

    def _run_block(self, block_object: SolBlock) -> 'SolObject':
        local_environment = Environment(block_object.environment)
        result = SOL_NIL

        for node in block_object.ast_node.assigns:
            result = self.evaluator.evaluate(node, local_environment)

        return result

    def send_message(self, receiver: 'SolObject', selector: str, 
                    args: list['SolObject'], environment: 'Environment') -> 'SolObject':

        # 1 BUILT IN METHODS ## and, or, ifTrue:ifFalse, whileTrue, timesRepeat, value

        if selector == "ifTrue:ifFalse:":
            if receiver == SOL_TRUE:
                return self._run_block(args[0])
            elif receiver == SOL_FALSE:
                return self._run_block(args[1])
        
        if selector == "value" or selector == "value:":
            if isinstance(receiver, SolBlock):
                return self._run_block(receiver)

        if selector == "timesRepeat:":
            if not isinstance(receiver, SolInteger):
                raise SemanticError(ErrorCode.SEM_ERROR)
            
            result = SOL_NIL
            if receiver.value > 0:
                for i in range(1, receiver.value+1):
                    counter = SolInteger(i)
                    result = self.send_message(args[0], "value:", [counter], environment)
            return result

        if selector == "whileTrue:":
            result = SOL_NIL
            condition = self.send_message(receiver, "value", [], environment)
            
            while(condition == SOL_TRUE):
                result = self.send_message(args[0], "value", [], environment)
            return result

        if selector == "and:":
            if receiver == SOL_FALSE:
                return SOL_FALSE
            elif receiver == SOL_TRUE:
                return self.send_message(args[0], "value", [], environment)
        
        if selector == "or:":
            if receiver == SOL_TRUE:
                return SOL_TRUE
            elif receiver == SOL_FALSE:
                return self.send_message(args[0], "value", [], environment)

        # 2 USER METHODS

        # 3 INSTANCNE ATRIBUTY
