from interpreter.sol_objects import SolObject
from interpreter.exceptions import SemanticError
from interpreter.error_codes import ErrorCode
from interpreter.sol_objects import SolObject, SOL_TRUE, SOL_FALSE, SOL_NIL

# TODO: double kontorly pre semanticke chyby ? ci treba or ne 
class Environment:
    def __init__(self, parent: 'Environment | None' = None) -> None:
        self.variables: dict[str, SolObject] = {}
        self.parent = parent
        self.parameters: set[str] = set()
        self.context_class: str | None = parent.context_class if parent else None

    def get(self, name: str) -> SolObject:
        if name in self.variables:
            return self.variables[name]
        
        if self.parent is not None:
            return self.parent.get(name)
        
        if name == "true":
            return SOL_TRUE
        if name == "false":
            return SOL_FALSE
        if name == "nil":
            return SOL_NIL
        raise SemanticError(ErrorCode.SEM_UNDEF)
        
    def contains(self, name: str) -> bool:
        if name in self.variables or name in self.parameters:
            return True
        if self.parent is not None:
            return self.parent.contains(name)
        return False

    def set(self, name: str, value: SolObject) -> SolObject:
        if name in ("class", "self", "super", "nil", "true", "false"):
            raise SemanticError(ErrorCode.SEM_ERROR)

        if name in self.parameters:
            raise SemanticError(ErrorCode.SEM_COLLISION)
        
        if name in self.variables:
            self.variables[name] = value
            return value

        if self.parent is not None and self.parent.contains(name):
            return self.parent.set(name, value)
        
        
        self.variables[name] = value
        return value