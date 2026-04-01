"""
This module defines the internal memory representation of SOL26 objects
and its methods.
"""

from typing import TYPE_CHECKING, TextIO

from interpreter.error_codes import ErrorCode
from interpreter.exceptions import InterpreterError
from interpreter.input_model import Block

if TYPE_CHECKING:
    from interpreter.environment import Environment


# ===========================================================
# RAW OBJECT CLASS
# ===========================================================
class SolObject:
    """General 'parent' class for all other classes of SOL26."""

    def __init__(self, sol_class_name: str) -> None:
        """Initialization of basic SOL26 object with its class-name."""
        self.sol_class_name = sol_class_name
        self.attributes: dict[str, SolObject] = {}

    def set_attribute(self, name: str, value: SolObject) -> SolObject:
        """Set an instance attribute of given object."""
        self.attributes[name] = value
        return self

    def get_attribute(self, name: str) -> SolObject | None:
        """
        Give an instance attribute of requested object or None if
        it not exist.
        """
        return self.attributes.get(name)

    def identical_to(self, other: SolObject) -> SolBoolean:
        """Compare if: Same Objects in memory"""
        if self is other:
            return SOL_TRUE
        return SOL_FALSE

    def equal_to(self, other: SolObject) -> SolBoolean:
        """Compare if: Same value of Objects"""
        return self.identical_to(other)

    def as_string(self) -> SolString:
        """Transforme: Given object to String"""
        return SolString("")

    def is_number(self) -> SolBoolean:
        """Compare if: Given object is a Number"""
        return SOL_FALSE

    def is_string(self) -> SolBoolean:
        """Compare if: Given object is a String"""
        return SOL_FALSE

    def is_block(self) -> SolBoolean:
        """Compare if: Given object is a Block"""
        return SOL_FALSE

    def is_nil(self) -> SolBoolean:
        """Compare if: Given object is a Nil"""
        return SOL_FALSE

    def is_boolean(self) -> SolBoolean:
        """Compare if: Given object is a Boolean"""
        return SOL_FALSE


# ===========================================================
# PROXY CLASS
# ===========================================================
class SolWrapper(SolObject):
    """
    Support class, responsable of context movement when keyword 'super' is called.
    """

    def __init__(self, actual_receiver: SolObject, start_class_name: str) -> None:
        """Initialization of wrapper with Receiver and Starting Class"""
        super().__init__("SuperReference")
        self.actual_receiver = actual_receiver
        self.start_class_name = start_class_name


# ===========================================================
# NIL CLASS
# ===========================================================
class SolNil(SolObject):
    """Representation of NIL Singleton Class in SOL26."""

    def __init__(self) -> None:
        """Initialisation of instance NIL"""
        super().__init__("Nil")

    def is_nil(self) -> SolBoolean:
        """Compare if: Given NIL is type of NIL"""
        return SOL_TRUE

    def as_string(self) -> SolString:
        """Transforme: NIL to String"""
        return SolString("nil")

    def equal_to(self, other: SolObject) -> SolBoolean:
        """Compare if: Given NIL is NIL in memory (Singleton->True)"""
        if isinstance(other, SolNil):
            return SOL_TRUE
        return SOL_FALSE


# ===========================================================
# BOOLEAN CLASS
# ===========================================================
class SolBoolean(SolObject):
    """Representation of Parent Class for boolean vlaues."""

    def __init__(self, class_name: str, value: bool) -> None:
        """Initialization of Boolean object with its value."""
        super().__init__(class_name)
        self.value = value

    def as_string(self) -> SolString:
        """Transform: Boolean to String"""
        if self.value:
            return SolString("true")
        return SolString("false")

    def is_boolean(self) -> SolBoolean:
        """Compare if: Given object is a Boolean"""
        return SOL_TRUE

    def equal_to(self, other: SolObject) -> SolBoolean:
        """Compare if: Same value of Boolean objects"""
        if isinstance(other, SolBoolean) and self.value == other.value:
            return SOL_TRUE
        return SOL_FALSE


# ===========================================================
# TRUE CLASS
# ===========================================================
class SolTrue(SolBoolean):
    """Representation of True Singleton Class in SOL26."""

    def __init__(self) -> None:
        """Initialization of instance True"""
        super().__init__("True", True)

    def not_(self) -> SolFalse:
        """Transform: True to False"""
        return SOL_FALSE


# ===========================================================
# FALSE CLASS
# ===========================================================
class SolFalse(SolBoolean):
    """Representation of False Singleton Class in SOL26."""

    def __init__(self) -> None:
        """Initialization of instance False"""
        super().__init__("False", False)

    def not_(self) -> SolTrue:
        """Transform: False to True"""
        return SOL_TRUE


# ===========================================================
# INTEGER CLASS
# ===========================================================
class SolInteger(SolObject):
    """Representation of Integer Class in SOL26."""

    def __init__(self, value: int) -> None:
        """Initialization of Integer object with its numeric value."""
        self.value = value
        super().__init__("Integer")

    def is_number(self) -> SolTrue:
        """Compare if: Given object is a Number"""
        return SOL_TRUE

    def as_string(self) -> SolString:
        """Transform: Integer to String"""
        return SolString(str(self.value))

    def as_integer(self) -> SolInteger:
        """Transform: Integer to Integer (returns self)"""
        return self

    def equal_to(self, other: SolObject) -> SolBoolean:
        """Compare if: Same value of Integer objects"""
        if isinstance(other, SolInteger) and self.value == other.value:
            return SOL_TRUE
        return SOL_FALSE

    def greater_than(self, other: SolInteger) -> SolBoolean:
        """Compare if: Given Integer is strictly greater than other"""
        if self.value > other.value:
            return SOL_TRUE
        return SOL_FALSE

    def plus(self, other: SolInteger) -> SolInteger:
        """Arithmetic operation: Add given Integer"""
        if not isinstance(other, SolInteger):
            raise InterpreterError(ErrorCode.INT_OTHER)
        return SolInteger(self.value + other.value)

    def minus(self, other: SolInteger) -> SolInteger:
        """Arithmetic operation: Subtract given Integer"""
        if not isinstance(other, SolInteger):
            raise InterpreterError(ErrorCode.INT_OTHER)
        return SolInteger(self.value - other.value)

    def multiply_by(self, other: SolInteger) -> SolInteger:
        """Arithmetic operation: Multiply by given Integer"""
        if not isinstance(other, SolInteger):
            raise InterpreterError(ErrorCode.INT_OTHER)
        return SolInteger(self.value * other.value)

    def div_by(self, other: SolInteger) -> SolInteger:
        """Arithmetic operation: Divide by given Integer"""
        if not isinstance(other, SolInteger):
            raise InterpreterError(ErrorCode.INT_OTHER)

        try:
            return SolInteger(int(self.value / other.value))
        except ZeroDivisionError as err:
            raise InterpreterError(error_code=ErrorCode.INT_INVALID_ARG) from err


# ===========================================================
# STRING CLASS
# ===========================================================
class SolString(SolObject):
    """Representation of String Class in SOL26."""

    def __init__(self, value: str) -> None:
        """Initialization of String object with its text value."""
        self.value = value
        super().__init__("String")

    def is_string(self) -> SolTrue:
        """Compare if: Given object is a String"""
        return SOL_TRUE

    def equal_to(self, other: SolObject) -> SolBoolean:
        """Compare if: Same value of String objects"""
        if isinstance(other, SolString) and self.value == other.value:
            return SOL_TRUE
        return SOL_FALSE

    def as_string(self) -> SolString:
        """Transform: String to String (returns self)"""
        return self

    def as_integer(self) -> SolObject:
        """Transform: String to Integer or NIL if invalid format"""
        try:
            return SolInteger(int(self.value))
        except ValueError:
            return SOL_NIL

    def concatenate_with(self, other: SolObject) -> SolObject:
        """String operation: Append another String"""
        if isinstance(other, SolString):
            return SolString(self.value + other.value)
        return SOL_NIL

    @classmethod
    def read(cls, input_stream: TextIO) -> SolString:
        """I/O operation: Read line from standard input and transform to String"""
        return cls(input_stream.readline().rstrip("\n"))

    def print(self) -> SolString:
        """I/O operation: Print String to standard output"""
        print(self.value, end="")
        return self

    def starts_with_ends_before(self, start: SolObject, end: SolObject) -> SolObject:
        """String operation: Extract substring using 1-based start and end indices"""
        if not (isinstance(start, SolInteger) and isinstance(end, SolInteger)):
            return SOL_NIL
        if start.value <= 0 or end.value <= 0:
            return SOL_NIL
        if (end.value - start.value) <= 0:
            return SolString("")
        return SolString(self.value[start.value - 1 : end.value - 1])

    def length(self) -> SolInteger:
        """String operation: Calculate length of String as Integer"""
        return SolInteger(len(self.value))


# ===========================================================
# SolClass CLASS
# ===========================================================
class SolClass(SolObject):
    """Representation of Class object in SOL26."""

    def __init__(self, class_name: str) -> None:
        """Initialization of Class object with its name."""
        super().__init__("Class")
        self.value = class_name

    def as_string(self) -> SolString:
        """Transform: Class object to String"""
        return SolString(self.value)

    def equal_to(self, other: SolObject) -> SolBoolean:
        """Compare if: Same value of Class objects"""
        if isinstance(other, SolClass) and self.value == other.value:
            return SOL_TRUE
        return SOL_FALSE


# ===========================================================
# BLOCK CLASS
# ===========================================================
class SolBlock(SolObject):
    """Representation of Block (Closure) Class in SOL26."""

    def __init__(self, ast_node: Block, environment: Environment) -> None:
        """Initialization of Block object with AST node and Environment memory."""
        super().__init__("Block")
        super().__init__("Block")
        self.ast_node = ast_node
        self.environment = environment

    def is_block(self) -> SolBoolean:
        """Compare if: Given object is a Block"""
        return SOL_TRUE

    def as_string(self) -> SolString:
        """Transform: Block to String"""
        return SolString("[block]")


SOL_NIL = SolNil()
SOL_TRUE = SolTrue()
SOL_FALSE = SolFalse()
