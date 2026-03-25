from interpreter.input_model import Program
from interpreter.sol_objects import SolObject, SolInteger, SolString, SolBlock, SolWrapper, SOL_TRUE, SOL_FALSE, SOL_NIL
from interpreter.environment import Environment
from interpreter.evaluator import Evaluator
from interpreter.error_codes import ErrorCode
from interpreter.exceptions import SemanticError
from interpreter.exceptions import InterpreterError
from typing import TextIO

class Dispatcher:
    def __init__(self, program: 'Program', input_io: 'TextIO') -> None:
        self.program = program
        self.input_io = input_io
        self.evaluator = Evaluator(self)

    def _run_block(self, block_object: SolBlock) -> 'SolObject':
        local_environment = Environment(block_object.environment)
        result = SOL_NIL

        for node in block_object.ast_node.assigns:
            evaluated = self.evaluator.evaluate(node.expr, local_environment)
            result = local_environment.set(node.target.name, evaluated)

        return result

    def execute_user_method(self, method, def_class, receiver, args):
        environment = Environment()
        environment.variables["self"] = receiver

        environment.variables["super"] = SolWrapper(receiver, def_class.parent) # TODO: fix def_class

        for i, param in enumerate(method.block.parameters):
            environment.set(param.name, args[i])

        return self._run_block(SolBlock(method.block, environment))

    def send_message(self, receiver: 'SolObject', selector: str, 
                    args: list['SolObject'], environment: 'Environment') -> 'SolObject':
        
        if isinstance(receiver, SolWrapper):
            actual_receiver = receiver.actual_receiver
            start_class_name = receiver.start_class_name
        else:
            actual_receiver = receiver
            start_class_name = receiver.sol_class_name

        # 1.1 BUILT IN METHODS ## and, or, ifTrue:ifFalse, whileTrue, timesRepeat, value

        if selector == "ifTrue:ifFalse:":
            if actual_receiver is SOL_TRUE:
                return self._run_block(args[0])
            elif actual_receiver is SOL_FALSE:
                return self._run_block(args[1])
        
        if selector == "value" or selector == "value:":
            if isinstance(actual_receiver, SolBlock):
                return self._run_block(actual_receiver)

        if selector == "timesRepeat:":
            if not isinstance(actual_receiver, SolInteger):
                raise SemanticError(ErrorCode.SEM_ERROR)
            
            result = SOL_NIL
            if actual_receiver.value > 0:
                for i in range(1, actual_receiver.value+1):
                    counter = SolInteger(i)
                    result = self.send_message(args[0], "value:", [counter], environment)
            return result

        if selector == "whileTrue:":
            result = SOL_NIL
            condition = self.send_message(actual_receiver, "value", [], environment)
            
            while(condition is SOL_TRUE):
                result = self.send_message(args[0], "value", [], environment)
                condition = self.send_message(actual_receiver, "value", [], environment)
            return result

        if selector == "and:":
            if actual_receiver is SOL_FALSE:
                return SOL_FALSE
            elif actual_receiver is SOL_TRUE:
                return self.send_message(args[0], "value", [], environment)
        
        if selector == "or:":
            if actual_receiver is SOL_TRUE:
                return SOL_TRUE
            elif actual_receiver is SOL_FALSE:
                return self.send_message(args[0], "value", [], environment)

        # 1.2 Already defined methods
        # TODO: not_ will not work prob.

        to_python = selector.strip(":")
        to_python = to_python.replace(":", "_")

        if hasattr(actual_receiver, to_python):
            function = getattr(actual_receiver, to_python)
            if callable(function):
                return function(*args)
        
        # 2 USER METHODS

        current_class_name = start_class_name

        while(current_class_name):
            found_class = None
            for cls in self.program.classes:
                if current_class_name == cls.name:
                    found_class = cls
                    break
            if not found_class:
                break
            
            for mtd in found_class.methods:
                if selector == mtd.selector:
                    return self.execute_user_method(mtd, found_class, actual_receiver, args)
            current_class_name = found_class.parent

        # 3 INSTANCNE ATRIBUTY

        if selector.endswith(":") and len(args) == 1:
            actual_receiver.attributes[selector.strip(":")] = args[0]
            return actual_receiver
        
        if len(args) == 0:
            value = actual_receiver.attributes.get(selector)
            if value is not None:
                return value
        raise InterpreterError(
            ErrorCode.INT_DNU
            )



