from typing import TextIO

from interpreter.environment import Environment
from interpreter.error_codes import ErrorCode
from interpreter.evaluator import Evaluator
from interpreter.exceptions import InterpreterError, SemanticError
from interpreter.input_model import Block, Program
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


class Dispatcher:
    def __init__(self, program: Program, input_io: TextIO) -> None:
        self.program = program
        self.input_io = input_io
        self.evaluator = Evaluator(self)

    def _run_block(self, block_object: SolBlock, block_args: list[SolObject] | None = None) -> SolObject:
        if block_args is None:
            block_args = []

        local_environment = Environment(block_object.environment)
        for i, param in enumerate(block_object.ast_node.parameters):
            local_environment.set(param.name, block_args[i])

        result = SOL_NIL

        for node in block_object.ast_node.assigns:
            evaluated = self.evaluator.evaluate(node.expr, local_environment)
            result = local_environment.set(node.target.name, evaluated)

        return result

    def _has_method(self, class_name: str, method_name: str) -> bool:
        to_python = method_name.replace(":", "_")
        if to_python == "not":
            to_python = "not_"
        current_class_name = class_name
        while current_class_name:
            found_class = None
            for c in self.program.classes:
                if c.name == current_class_name:
                    found_class = c
                    break
            if not found_class:
                break

            for mtd in found_class.methods:
                if mtd.selector == method_name:
                    return True
            current_class_name = found_class.parent

        return False

    def execute_user_method(self, method, def_class, receiver, args):
        environment = Environment()
        environment.variables["self"] = receiver
        environment.variables["super"] = SolWrapper(receiver, def_class.parent)

        return self._run_block(SolBlock(method.block, environment), args)

    #------------------------------------------------------------------------
    #########################################################################
    #------------------------------------------------------------------------

    def send_message(self, receiver: SolObject, selector: str, args: list[SolObject], 
                     environment: Environment) -> SolObject:
        
        # 0. Unpacking wrapper
        if isinstance(receiver, SolWrapper):
            actual_receiver = receiver.actual_receiver
            start_class_name = receiver.start_class_name
        else:
            actual_receiver = receiver
            start_class_name = receiver.sol_class_name

        # 1. CLASS meth (new & from & read)
        if isinstance(actual_receiver, SolClass):
            result = self._handle_class_message(actual_receiver, selector, args)
            if result is not None:
                return result

        # 2. BUILT IN METHODS (and, or, ifTrue:ifFalse, whileTrue, timesRepeat, value)
        result = self._handle_builtin_control(actual_receiver, selector, args, environment)
        if result is not None:
            return result

        # 3. Already defined methods
        result = self._handle_python_builtin(actual_receiver, selector, args)
        if result is not None:
            return result

        # 4. USER METHODS
        result = self._handle_user_method(actual_receiver, start_class_name, selector, args)
        if result is not None:
            return result

        # 5. INSTANCNE ATRIBUTES
        return self._handle_instance_attribute(actual_receiver, start_class_name, selector, args)
    
    def _handle_class_message(self, actual_receiver: SolClass, selector: str, args: list[SolObject]) -> SolObject | None:
        class_name = actual_receiver.value
        
        if selector == "new":
            if class_name == "Nil": 
                return SOL_NIL
            if class_name == "True": 
                return SOL_TRUE
            if class_name == "False": 
                return SOL_FALSE
            if class_name == "Integer": 
                return SolInteger(0)
            if class_name == "String": 
                return SolString("")
            if class_name == "Block":
                empty_node = Block(arity=0, parameters=[], assigns=[])
                return SolBlock(empty_node, Environment())
            return SolObject(class_name)

        if selector == "from":

            if len(args) != 1:
                raise InterpreterError(ErrorCode.INT_DNU)

            if class_name == "Nil": 
                return SOL_NIL
            if class_name == "True": 
                return SOL_TRUE
            if class_name == "False": 
                return SOL_FALSE

            source_object = args[0]
            new_instance = None

            if class_name == "Integer":
                if not isinstance(source_object, SolInteger):
                    raise InterpreterError(ErrorCode.INT_INVALID_ARG)
                new_instance = SolInteger(source_object.value)
            elif class_name == "String":
                if not isinstance(source_object, SolString):
                    raise InterpreterError(ErrorCode.INT_INVALID_ARG)
                new_instance = SolString(source_object.value)
            else:
                new_instance = SolObject(class_name)

            new_instance.attributes = source_object.attributes.copy()
            return new_instance

        if selector == "read" and class_name == "String":
            return SolString.read(self.input_io)
            
        return None

    def _handle_builtin_control(self, actual_receiver: SolObject, selector: str, args: list[SolObject], environment: Environment) -> SolObject | None:
        if selector.startswith("value") and isinstance(actual_receiver, SolBlock):
            expected_args = selector.count(":")
            if expected_args != len(actual_receiver.ast_node.parameters):
                raise InterpreterError(ErrorCode.INT_DNU)
            return self._run_block(actual_receiver, args)

        if selector == "ifTrue:ifFalse:":
            if actual_receiver is SOL_TRUE:
                return self.send_message(args[0], "value", [], environment)
            if actual_receiver is SOL_FALSE:
                return self.send_message(args[1], "value", [], environment)

        if selector == "timesRepeat:":
            if not isinstance(actual_receiver, SolInteger):
                raise SemanticError(ErrorCode.SEM_ERROR)
            result = SOL_NIL
            if actual_receiver.value > 0:
                for i in range(1, actual_receiver.value + 1):
                    counter = SolInteger(i)
                    result = self.send_message(args[0], "value:", [counter], environment)
            return result

        if selector == "whileTrue:":
            result = SOL_NIL
            condition = self.send_message(actual_receiver, "value", [], environment)
            while condition is SOL_TRUE:
                result = self.send_message(args[0], "value", [], environment)
                condition = self.send_message(actual_receiver, "value", [], environment)
            return result

        if selector == "and:":
            if actual_receiver is SOL_FALSE: 
                return SOL_FALSE
            if actual_receiver is SOL_TRUE: 
                return self.send_message(args[0], "value", [], environment)

        if selector == "or:":
            if actual_receiver is SOL_TRUE: 
                return SOL_TRUE
            if actual_receiver is SOL_FALSE: 
                return self.send_message(args[0], "value", [], environment)

        return None

    def _handle_python_builtin(self, actual_receiver: SolObject, selector: str, args: list[SolObject]) -> SolObject | None:
        to_python = selector.strip(":")
        to_python = to_python.replace(":", "_")

        if to_python == "not":
            to_python = "not_"

        if hasattr(actual_receiver, to_python):
            function = getattr(actual_receiver, to_python)
            if callable(function):
                return function(*args)
        
        return None

    def _handle_user_method(self, actual_receiver: SolObject, start_class_name: str, selector: str, args: list[SolObject]) -> SolObject | None:
        current_class_name = start_class_name

        while current_class_name:
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
            
        return None

    def _handle_instance_attribute(self, actual_receiver: SolObject, start_class_name: str, selector: str, args: list[SolObject]) -> SolObject:
        if selector.endswith(":") and len(args) == 1:
            attribute_name = selector.strip(":")
            python_method = attribute_name
            if python_method == "not":
                python_method = "not_"

            if hasattr(actual_receiver, python_method) and callable(getattr(actual_receiver, python_method)):
                raise InterpreterError(ErrorCode.INT_INST_ATTR)

            if self._has_method(start_class_name, attribute_name):
                raise InterpreterError(ErrorCode.INT_INST_ATTR)

            actual_receiver.attributes[attribute_name] = args[0]
            return actual_receiver

        if len(args) == 0:
            value = actual_receiver.attributes.get(selector)
            if value is not None:
                return value
                
        raise InterpreterError(ErrorCode.INT_DNU)