from interpreter.input_model import Program
from interpreter.sol_objects import SolObject, SolInteger, SolString, SolBlock, SOL_TRUE, SOL_FALSE, SOL_NIL
from interpreter.environment import Environment
from interpreter.evaluator import Evaluator
from interpreter.error_codes import ErrorCode
from interpreter.exceptions import SemanticError

class Dispatcher:
    def __init__(self, program: 'Program') -> None:
        self.program = program
        self.evaluator = Evaluator(self)

    def _run_block(self, block_object: SolBlock) -> 'SolObject':
        local_environment = Environment(block_object.environment)
        result = SOL_NIL

        for node in block_object.ast_node.assigns:
            evaluated = self.evaluator.evaluate(node.expr, local_environment)
            result = local_environment.set(node.target.name, evaluated)

        return result

    def execute_user_method(self, method, receiver, args):
        environment = Environment()
        environment.variables["self"] = receiver
        environment.variables["super"] = receiver

        for i, param in enumerate(method.block.parameters):
            environment.set(param.name, args[i])

        return self._run_block(SolBlock(method.block, environment))

    def send_message(self, receiver: 'SolObject', selector: str, 
                    args: list['SolObject'], environment: 'Environment') -> 'SolObject':

        # 1.1 BUILT IN METHODS ## and, or, ifTrue:ifFalse, whileTrue, timesRepeat, value

        if selector == "ifTrue:ifFalse:":
            if receiver is SOL_TRUE:
                return self._run_block(args[0])
            elif receiver is SOL_FALSE:
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
            
            while(condition is SOL_TRUE):
                result = self.send_message(args[0], "value", [], environment)
                condition = self.send_message(receiver, "value", [], environment)
            return result

        if selector == "and:":
            if receiver is SOL_FALSE:
                return SOL_FALSE
            elif receiver is SOL_TRUE:
                return self.send_message(args[0], "value", [], environment)
        
        if selector == "or:":
            if receiver is SOL_TRUE:
                return SOL_TRUE
            elif receiver is SOL_FALSE:
                return self.send_message(args[0], "value", [], environment)

        # 1.2 Already defined methods
        # TODO: not_ will not work prob.

        to_python = selector.strip(":")
        to_python = to_python.replace(":", "_")

        if hasattr(receiver, to_python):
            function = getattr(receiver, to_python)
            return function(*args)
        
        # 2 USER METHODS

        class_name = receiver.sol_class_name

        while(class_name):
            found_class = None
            for cls in self.program.classes:
                if class_name == cls.name:
                    found_class = cls
                    break
            if not found_class:
                break
            
            for mtd in found_class.methods:
                if selector == mtd.selector:
                    return self.execute_user_method(mtd, receiver, args)
            class_name = found_class.parent

        # 3 INSTANCNE ATRIBUTY

        if selector.endswith(":") and len(args) == 1:
            receiver.attributes[selector.strip(":")] = args[0]
            return receiver
        
        if len(args) == 0:
            value = receiver.attributes[selector]
            if value is not None:
                return value
            raise SemanticError(ErrorCode.SEM_UNDEF)



