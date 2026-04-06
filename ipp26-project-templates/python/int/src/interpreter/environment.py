"""
This module defines the memory environment and variable scope for the SOL26 interpreter.

Author: Andrej Bližnák <xblizna00@fit.vut.cz>
"""

from interpreter.error_codes import ErrorCode
from interpreter.exceptions import SemanticError
from interpreter.sol_objects import SOL_FALSE, SOL_NIL, SOL_TRUE, SolObject


# ===========================================================
# ENVIRONMENT(BACKPACK) CLASS
# ===========================================================
class Environment:
    """Representation of Memory Environment and Variable Scope in SOL26."""

    def __init__(self, parent: Environment | None = None) -> None:
        """Initialization of Environment with optional parent scope."""
        self.variables: dict[str, SolObject] = {}
        self.parent = parent
        self.parameters: set[str] = set()
        self.context_class: str | None = parent.context_class if parent else None

    def get(self, name: str) -> SolObject:
        """Retrieve: Value of variable from current or parent scope."""

        # Search in own backpack
        if name in self.variables:
            return self.variables[name]
        # Search in parent backpack
        if self.parent is not None:
            return self.parent.get(name)
        # Or, if it is BOOLEAN/NIL
        if name == "true":
            return SOL_TRUE
        if name == "false":
            return SOL_FALSE
        if name == "nil":
            return SOL_NIL
        # Otherwise, variable does not exists
        raise SemanticError(ErrorCode.SEM_UNDEF)

    def _contains(self, name: str) -> bool:
        """Compare if: Variable name exists in current or parent scope."""
        if name in self.variables or name in self.parameters:
            return True
        if self.parent is not None:
            return self.parent._contains(name)
        return False

    def set(self, name: str, value: SolObject) -> SolObject:
        """Set: Value to a variable while preventing keyword/parameter collision."""

        # Cannot override keywords
        if name in ("class", "self", "super", "nil", "true", "false"):
            raise SemanticError(ErrorCode.SEM_ERROR)

        # Cannot override paramater
        if name in self.parameters:
            raise SemanticError(ErrorCode.SEM_COLLISION)

        # If, variable exists, override its value
        if name in self.variables:
            self.variables[name] = value
            return value
        
        # Search in its parent
        if self.parent is not None and self.parent._contains(name):
            return self.parent.set(name, value)

        # Create new variable
        self.variables[name] = value
        return value
