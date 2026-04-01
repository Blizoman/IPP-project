"""
This module defines the Dispatcher, the core-heavy runtime engine for routing messages
and executing methods in the SOL26 environment.
"""

import inspect
from typing import TextIO, cast

from interpreter.environment import Environment
from interpreter.evaluator import Evaluator
from interpreter.exceptions import (
    AttributeCollisionError,
    InvalidArgumentError,
    MessageNotUnderstoodError,
    RuntimeTypeError,
    SemanticError,
)
from interpreter.input_model import Block, ClassDef, Method, Program
from interpreter.sol_objects import (
    SOL_FALSE,
    SOL_NIL,
    SOL_TRUE,
    SolBlock,
    SolBoolean,
    SolClass,
    SolFalse,
    SolInteger,
    SolNil,
    SolObject,
    SolString,
    SolTrue,
    SolWrapper,
)


# ===========================================================
# DISPATCHER CLASS
# ===========================================================
class Dispatcher:
    """Core engine: Routes messages and executes methods in SOL26."""

    def __init__(self, program: Program, input_io: TextIO) -> None:
        """Initialization of Dispatcher with program AST and input stream."""
        self.program = program
        self.input_io = input_io
        self.evaluator = Evaluator(self)

    def _run_block(
        self, block_object: SolBlock, block_args: list[SolObject] | None = None
    ) -> SolObject:
        """Execute: Block object with mapped arguments in local memory scope."""

        if block_args is None:
            block_args = []

        if len(block_args) != len(block_object.ast_node.parameters):
            raise MessageNotUnderstoodError()

        local_environment = Environment(block_object.environment)
        for i, param in enumerate(block_object.ast_node.parameters):
            local_environment.set(param.name, block_args[i])

        result: SolObject = SOL_NIL

        for node in block_object.ast_node.assigns:
            evaluated = self.evaluator.evaluate(node.expr, local_environment)
            if isinstance(evaluated, SolWrapper):
                evaluated = evaluated.actual_receiver
            result = local_environment.set(node.target.name, evaluated)

        return result

    def _has_method(self, class_name: str, method_name: str) -> bool:
        """Compare if: Method exists in the given class or its parents."""
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

    def _get_base_builtin(self, class_name: str) -> str:
        """Retrieve: Base built-in class name from the inheritance hierarchy."""
        current = class_name
        while current:
            if current in ("Integer", "String", "Block", "True", "False", "Nil", "Object"):
                return current

            found_parent = None
            for c in self.program.classes:
                if c.name == current:
                    found_parent = c.parent
                    break

            if found_parent is None:
                break
            current = found_parent

        return "Object"

    def execute_user_method(
        self, method: Method, def_class: ClassDef, receiver: SolObject, args: list[SolObject]
    ) -> SolObject:
        """Execute: User method in new environment with context of 'self' and 'super'."""

        environment = Environment()
        environment.variables["self"] = receiver
        environment.variables["super"] = SolWrapper(receiver, def_class.parent)
        environment.context_class = def_class.name

        return self._run_block(SolBlock(method.block, environment), args)

    # ===========================================================
    # MESSAGE MANAGER
    # ===========================================================

    def send_message(
        self, receiver: SolObject, selector: str, args: list[SolObject], environment: Environment
    ) -> SolObject:
        """Route: Message to correct handler based on receiver type and selector."""

        is_wrapper = False

        if isinstance(receiver, SolWrapper):
            is_wrapper = True
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
        return self._handle_instance_attribute(
            actual_receiver, start_class_name, selector, args, is_wrapper, environment
        )

    # ===========================================================
    # HANDLERS
    # ===========================================================
    def _handle_class_message(
        self, actual_receiver: SolClass, selector: str, args: list[SolObject]
    ) -> SolObject | None:
        """Handle: Class-level messages like 'new', 'from:', and 'read'."""

        class_name = actual_receiver.value
        base_builtin = self._get_base_builtin(class_name)

        if selector == "new":
            return self._handle_class_new(class_name, base_builtin)
        if selector == "from:":
            return self._handle_class_from(class_name, base_builtin, args)
        if selector == "read" and base_builtin == "String":
            return SolString.read(self.input_io)

        return None

    def _handle_class_new(self, class_name: str, base_builtin: str) -> SolObject:
        """Handle: Creation of a new object instance based on class type."""
        if base_builtin == "Nil":
            return SOL_NIL
        if base_builtin == "True":
            return SOL_TRUE
        if base_builtin == "False":
            return SOL_FALSE

        if base_builtin == "Integer":
            obj_int = SolInteger(0)
            obj_int.sol_class_name = class_name
            return obj_int
        if base_builtin == "String":
            obj_str = SolString("")
            obj_str.sol_class_name = class_name
            return cast(SolObject, obj_str)
        if base_builtin == "Block":
            empty_node = Block(arity=0, parameters=[], assigns=[])
            obj_block = SolBlock(empty_node, Environment())
            obj_block.sol_class_name = class_name
            return cast(SolObject, obj_block)

        return SolObject(class_name)

    def _handle_class_from(
        self, class_name: str, base_builtin: str, args: list[SolObject]
    ) -> SolObject:
        """Handle: Instantiation of a new object from a given source object."""

        if len(args) != 1:
            raise MessageNotUnderstoodError("from: requires exactly 1 argument")

        source_obj = args[0]
        new_inst: SolObject

        if base_builtin == "Integer":
            if not isinstance(source_obj, SolInteger):
                raise InvalidArgumentError("from: expects an Integer")
            new_inst = SolInteger(source_obj.value)
            new_inst.sol_class_name = class_name
        elif base_builtin == "String":
            if not isinstance(source_obj, SolString):
                raise InvalidArgumentError("from: expects a String")
            new_inst = SolString(source_obj.value)
            new_inst.sol_class_name = class_name
        elif base_builtin == "True":
            if (
                not isinstance(source_obj, SolTrue)
                and getattr(source_obj, "value", None) is not True
            ):
                raise InvalidArgumentError("from: expects True")
            new_inst = SolBoolean(class_name, True)
        elif base_builtin == "False":
            if (
                not isinstance(source_obj, SolFalse)
                and getattr(source_obj, "value", None) is not False
            ):
                raise InvalidArgumentError("from: expects False")
            new_inst = SolBoolean(class_name, False)
        elif base_builtin == "Nil":
            if not isinstance(source_obj, SolNil):
                raise InvalidArgumentError("from: expects Nil")
            new_inst = SolNil()
            new_inst.sol_class_name = class_name
        else:
            new_inst = SolObject(class_name)

        new_inst.attributes = source_obj.attributes.copy()
        return new_inst

    def _handle_builtin_control(
        self,
        actual_receiver: SolObject,
        selector: str,
        args: list[SolObject],
        environment: Environment,
    ) -> SolObject | None:
        """Handle: Built-in flow control structures (loops, conditionals, block evaluation)."""

        if selector.startswith("value") and isinstance(actual_receiver, SolBlock):
            if selector.count(":") != len(actual_receiver.ast_node.parameters):
                raise MessageNotUnderstoodError()
            return self._run_block(actual_receiver, args)

        if selector in ("timesRepeat:", "whileTrue:"):
            return self._handle_loops(actual_receiver, selector, args, environment)

        if selector in ("ifTrue:ifFalse:", "and:", "or:"):
            return self._handle_booleans(actual_receiver, selector, args, environment)

        return None

    def _handle_loops(
        self, receiver: SolObject, selector: str, args: list[SolObject], env: Environment
    ) -> SolObject:
        """Handle: Loop constructs 'timesRepeat:' and 'whileTrue:'."""

        if selector == "timesRepeat:":
            if not isinstance(receiver, SolInteger):
                raise RuntimeTypeError()
            res: SolObject = SOL_NIL
            if receiver.value > 0:
                for i in range(1, receiver.value + 1):
                    res = self.send_message(args[0], "value:", [SolInteger(i)], env)
            return res

        if selector == "whileTrue:":
            res_w: SolObject = SOL_NIL
            cond = self.send_message(receiver, "value", [], env)
            while cond is SOL_TRUE:
                res_w = self.send_message(args[0], "value", [], env)
                cond = self.send_message(receiver, "value", [], env)
            return res_w

        return SOL_NIL

    def _handle_booleans(
        self, receiver: SolObject, selector: str, args: list[SolObject], env: Environment
    ) -> SolObject | None:
        """Handle: Boolean operations 'ifTrue:ifFalse:', 'and:', and 'or:'."""

        if selector == "ifTrue:ifFalse:":
            if receiver is SOL_TRUE:
                return self.send_message(args[0], "value", [], env)
            if receiver is SOL_FALSE:
                return self.send_message(args[1], "value", [], env)

        if selector == "and:":
            if receiver is SOL_FALSE:
                return SOL_FALSE
            if receiver is SOL_TRUE:
                return self.send_message(args[0], "value", [], env)

        if selector == "or:":
            if receiver is SOL_TRUE:
                return SOL_TRUE
            if receiver is SOL_FALSE:
                return self.send_message(args[0], "value", [], env)

        return None

    def _handle_python_builtin(
        self, actual_receiver: SolObject, selector: str, args: list[SolObject]
    ) -> SolObject | None:
        """Handle: Native python methods mapped directly from SOL26 message selectors."""

        method_map = {
            "identicalTo:": "identical_to",
            "equalTo:": "equal_to",
            "asString": "as_string",
            "isNumber": "is_number",
            "isString": "is_string",
            "isBlock": "is_block",
            "isNil": "is_nil",
            "isBoolean": "is_boolean",
            "not": "not_",
            "asInteger": "as_integer",
            "greaterThan:": "greater_than",
            "multiplyBy:": "multiply_by",
            "divBy:": "div_by",
            "concatenateWith:": "concatenate_with",
            "startsWith:endsBefore:": "starts_with_ends_before",
        }

        # Check explicit mapping first
        if selector in method_map:
            to_python = method_map[selector]
        else:
            # Fallback to old heuristic
            to_python = selector.strip(":")
            to_python = to_python.replace(":", "_")
            if to_python == "not":
                to_python = "not_"

        if hasattr(actual_receiver, to_python):
            function = getattr(actual_receiver, to_python)
            if callable(function):
                try:
                    inspect.signature(function).bind(*args)
                    return cast("SolObject", function(*args))
                except TypeError:
                    return None

        return None

    def _handle_user_method(
        self,
        actual_receiver: SolObject,
        start_class_name: str,
        selector: str,
        args: list[SolObject],
    ) -> SolObject | None:
        """Handle: User-defined methods located inside the class hierarchy."""

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

    def _handle_instance_attribute(
        self,
        actual_receiver: SolObject,
        start_class_name: str,
        selector: str,
        args: list[SolObject],
        is_wrapper: bool,
        environment: Environment,
    ) -> SolObject:
        """Handle: Instance attribute getters and setters, ensuring no method collisions."""

        if selector.endswith(":") and len(args) == 1:
            attribute_name = selector.strip(":")

            # Map camelCase back to snake_case for collision checking
            method_map = {
                "identicalTo": "identical_to",
                "equalTo": "equal_to",
                "asString": "as_string",
                "isNumber": "is_number",
                "isString": "is_string",
                "isBlock": "is_block",
                "isNil": "is_nil",
                "isBoolean": "is_boolean",
                "not": "not_",
                "asInteger": "as_integer",
                "greaterThan": "greater_than",
                "multiplyBy": "multiply_by",
                "divBy": "div_by",
                "concatenateWith": "concatenate_with",
            }
            python_method = method_map.get(attribute_name, attribute_name)

            if python_method == "not":
                python_method = "not_"

            if hasattr(actual_receiver, python_method) and callable(
                getattr(actual_receiver, python_method)
            ):
                raise AttributeCollisionError()

            check_class: str | None = start_class_name
            if not is_wrapper:
                try:
                    environment_self = environment.get("self")
                    if actual_receiver is environment_self and getattr(
                        environment, "context_class", None
                    ):
                        check_class = environment.context_class
                except SemanticError:
                    ...

            if check_class is not None and self._has_method(check_class, attribute_name):
                raise AttributeCollisionError()

            actual_receiver.attributes[attribute_name] = args[0]
            return actual_receiver

        if len(args) == 0:
            value = actual_receiver.attributes.get(selector)
            if value is not None:
                return value

        raise MessageNotUnderstoodError()
