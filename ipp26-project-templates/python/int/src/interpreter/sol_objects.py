"""
This module defines the internal memory representation of SOL26 objects.
"""
from interpreter.error_codes import ErrorCode
from interpreter.input_model import Block

from interpreter.exceptions import InterpreterError



class SolObject:
    def __init__(self, class_name: str) -> None:
        self.sol_class_name = class_name
        self.attributes: dict[str, 'SolObject'] = {}

    def set_attribute(self, name: str, value: 'SolObject') -> 'SolObject':
        self.attributes[name] = value
        return self
    
    def get_attribute(self, name: str) -> 'SolObject | None':
        return self.attributes.get(name)

    def identicalTo(self, other: 'SolObject') -> 'SolBoolean':
        if self is other:
            return SOL_TRUE
        return SOL_FALSE

    def equalTo(self, other: 'SolObject') -> 'SolBoolean':
        return self.identicalTo(other)

    def asString(self) -> 'SolString':
        return SolString('')
    
    def isNumber(self) -> 'SolBoolean':
        return SOL_FALSE
    
    def isString(self) -> 'SolBoolean':
        return SOL_FALSE
    
    def isBlock(self) -> 'SolBoolean':
        return SOL_FALSE
    
    def isNil(self) -> 'SolBoolean':
        return SOL_FALSE
    
    def isBoolean(self) -> 'SolBoolean':
        return SOL_FALSE


class SolNil(SolObject):
    def __init__(self) -> None:
        super().__init__("Nil")

    """
    def __new__(cls) -> 'SolNil':
        if cls.instance == None:
            cls.instance = super().__new__(cls)
        return cls.instance
    
    # ??? mby dlt
    def from_(self) -> None | 'SolNil':
        return self
    """

    def isNil(self) -> 'SolBoolean':
        return SOL_TRUE
    
    def asString(self) -> 'SolString':
        return SolString('nil')
    

class SolBoolean(SolObject):

    def __init__(self, class_name: str, value: bool) -> None:
        super().__init__(class_name)
        self.value = value

    def asString(self) -> 'SolString':
        if self.value:
            return SolString('true')
        return SolString('false')

    def isBoolean(self) -> 'SolBoolean':
        return SOL_TRUE


class SolTrue(SolBoolean):
    def __init__(self) -> None:
        super().__init__("True", True)

    def not_(self) -> 'SolFalse':
        return SOL_FALSE

    """ *** DISPECER ?
    def and_(self) -> 'SolTrue':
        return SOL_TRUE
    
    def or_(self) -> 'SolTrue':
        return SOL_TRUE
    
    def ifTrue(self): ...

    def ifFalse(self): ...
    """

class SolFalse(SolBoolean):
    def __init__(self) -> None:
        super().__init__("False", False)

    def not_(self) -> 'SolTrue':
        return SOL_TRUE

    """ *** DISPECER ?
    def and_(self) -> 'SolFalse':
        return SOL_FALSE
    
    def or_(self, argument: 'SolObject') -> 'SolObject':
        if self.value:
            return SOL_TRUE
        return SOL_FALSE
    
    def ifTrue(self): ...

    def ifFalse(self): ...
    """

class SolInteger(SolObject):

    def __init__(self, value: int) -> None:
        self.value = value
        super().__init__("Integer")

    def isNumber(self) -> 'SolTrue': 
        return SOL_TRUE

    def asString(self) -> 'SolString':
        return SolString(str(self.value))
    
    def asInteger(self) -> 'SolInteger':
        return self
    
    def equalTo(self, other: SolObject) -> 'SolBoolean':
        if isinstance(other, SolInteger):
            if self.value == other.value:
                return SOL_TRUE
        return SOL_FALSE
    
    def greaterThan(self, other: 'SolInteger') -> 'SolBoolean':
        if self.value > other.value:
            return SOL_TRUE
        return SOL_FALSE
    
    def plus(self, other: 'SolInteger') -> 'SolInteger':
        return SolInteger(self.value + other.value)
    
    def minus(self, other: 'SolInteger') -> 'SolInteger':
        return SolInteger(self.value - other.value)
    
    def multiplyBy(self, other: 'SolInteger') -> 'SolInteger':
        return SolInteger(self.value * other.value)
    

    #### Raise lepsie spracovat ERR TODO:
    def divBy(self, other: 'SolInteger') -> 'SolInteger':
        try:
            return SolInteger(int(self.value / other.value))
        except ZeroDivisionError:
            raise InterpreterError(error_code=ErrorCode.INT_INVALID_ARG)


class SolString(SolObject):
    def __init__(self, value: str) -> None:
        self.value = value
        super().__init__("String")
    
    def isString(self) -> 'SolTrue':
        return SOL_TRUE
        
    def equalTo(self, other: SolObject) -> 'SolBoolean':
        if isinstance(other, SolString):
            if self.value == other.value:
                return SOL_TRUE
        return SOL_FALSE
    
    def asString(self) -> 'SolString':
        return self
    
    def asInteger(self) -> 'SolObject':
        try:
            return SolInteger(int(self.value))
        except ValueError:
            return SOL_NIL
    
    def concatenateWith(self, other) -> 'SolObject':
        if isinstance(other, SolString):
            return SolString(self.value+other.value)
        return SOL_NIL
    
    @classmethod
    def read(cls) -> 'SolString':
        return cls(input())

    def print(self) -> 'SolString':
        print(self.value, end="")
        return self

    def startsWith_endsBefore_(self, start: 'SolObject', end: 'SolObject') -> 'SolObject':
        if not (isinstance(start, SolInteger) and isinstance(end, SolInteger)):
            return SOL_NIL
        if start.value <= 0 or end.value <= 0:
            return SOL_NIL  
        if (end.value - start.value) <= 0:
            return SolString("")
        return SolString(self.value[start.value-1:end.value-1])

    def length(self) -> 'SolInteger':
        return SolInteger(len(self.value))


class SolBlock(SolObject):
    def __init__(self, ast_node: Block, environment: list[dict[str, SolObject]]) -> None:
        super().__init__("Block")
        self.ast_node = ast_node
        self.environment = environment
    
    def isBlock(self) -> 'SolBoolean':
        return SOL_TRUE
    
    def asString(self) -> 'SolString':
        return SolString("[block]")



SOL_NIL = SolNil()
SOL_TRUE = SolTrue()
SOL_FALSE = SolFalse()