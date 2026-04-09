"""
This module performs static semantic analysis on the parsed SOL-XML program.

It checks for class inheritance cycles, variable scoping, arity mismatches,
and other static constraints before the execution begins.

Author: Andrej Bližnák <xblizna00@fit.vut.cz>
"""

from interpreter.error_codes import ErrorCode
from interpreter.exceptions import SemanticError
from interpreter.input_model import Block, ClassDef, Expr, Literal, Program, Send, Var


# ===========================================================
# STATIC AND SEMANTIC CONTROL
# ===========================================================
class StaticAnalyzer:
    """Performs static semantic checks on the AST before evaluation."""

    def __init__(self, program: Program) -> None:
        """Initialize the static analyzer with the parsed program."""
        self.program = program

        # Stack to keep track of variables available in the current scope.
        # Each element in the list is a set of variable names for a specific block/level.
        self.scope_stack: list[set[str]] = []
        # Stack to track parameter names of active nested blocks.
        self.param_scope_stack: list[set[str]] = []

        # Reserved names that cannot be used for inheritance or override.
        self.builtins = {"Object", "Nil", "Integer", "String", "Block", "True", "False"}
        self.keywords = {"class", "self", "super", "nil", "true", "false"}

    # ===========================================================
    # ENTRY POINT
    # ===========================================================
    def run(self) -> None:
        """Run all static semantic checks on the program."""
        self._check_classes()
        self._check_main()
        for cls in self.program.classes:
            self._check_methods(cls)

    # ===========================================================
    # CHECK CLASSES
    # ===========================================================
    def _check_classes(self) -> None:
        """Check class definitions for duplicates, invalid inheritance, and cycles."""
        names = [cls.name for cls in self.program.classes]

        # 1. Ensure, all class names are unique.
        if len(names) != len(set(names)):
            raise SemanticError(ErrorCode.SEM_ERROR)

        for cls in self.program.classes:
            # 2. Prevent a class to inheritate from itself
            if cls.parent == cls.name:
                raise SemanticError(ErrorCode.SEM_ERROR)
            # 3. Check if parent class exist
            if cls.parent not in names and cls.parent not in self.builtins:
                raise SemanticError(ErrorCode.SEM_UNDEF)
            # 4. Prevent from redefining builtin classes or using keywrods as class names
            if self._is_builtin(cls.name):
                raise SemanticError(ErrorCode.SEM_ERROR)
            if self._is_keyword(cls.name):
                raise SemanticError(ErrorCode.SEM_ERROR)

            # 5. Cyclic inheritance check
            visited = set()
            current = cls.name

            # Traverse up the inheritance chain
            while current and current not in self.builtins:
                if current in visited:
                    raise SemanticError(ErrorCode.SEM_ERROR)
                visited.add(current)
                # Find the parent of the current class in the chain
                current_cls = next((c for c in self.program.classes if c.name == current), None)
                if current_cls:
                    current = current_cls.parent
                else:
                    break

    # ===========================================================
    # CHECK MAIN
    # ===========================================================
    def _check_main(self) -> None:
        """Ensure the program has a Main class with a parameterless run method."""
        for cls in self.program.classes:
            if cls.name == "Main":
                for method in cls.methods:
                    if method.selector == "run":
                        # Run method must be without arguments
                        if method.block.arity != 0:
                            raise SemanticError(ErrorCode.SEM_MAIN)
                        return
        # If we loop through everything and don`t return, Main or run() is missing
        raise SemanticError(ErrorCode.SEM_MAIN)

    # ===========================================================
    # CHECK METHODS
    # ===========================================================
    def _check_methods(self, cls: ClassDef) -> None:
        """Check method definitions for duplicates and correct arity."""
        selector_names = [m.selector for m in cls.methods]

        # Check, if there are not any duplicit names of method selectors.
        if len(selector_names) != len(set(selector_names)):
            raise SemanticError(ErrorCode.SEM_ERROR)

        for method in cls.methods:
            # Checks, if every given ':' has its parameter
            expected_arity = method.selector.count(":")
            if method.block.arity != expected_arity:
                raise SemanticError(ErrorCode.SEM_ARITY)

            # Setup the base scope for the method
            self.scope_stack.append({"self", "super", "true", "false", "nil"})
            self._check_block(method.block)
            self.scope_stack.pop()

    # ===========================================================
    # CHECK BLOCK
    # ===========================================================
    def _check_block(self, block: Block) -> None:
        """Check block parameters and variable assignments for scoping rules."""
        if block.arity != len(block.parameters):
            raise SemanticError(ErrorCode.SEM_ARITY)

        # Check, if block params are not named as keywords
        param_names = [p.name for p in block.parameters]
        for name in param_names:
            if self._is_keyword(name):
                raise SemanticError(ErrorCode.SEM_ERROR)

        if len(param_names) != len(set(param_names)):
            raise SemanticError(ErrorCode.SEM_ERROR)

        current_scope = set(param_names)
        self.scope_stack.append(current_scope)
        self.param_scope_stack.append(set(param_names))

        # Creation of variable
        for assign in block.assigns:
            self._check_expr(assign.expr)
            if self._is_parameter_name(assign.target.name):
                raise SemanticError(ErrorCode.SEM_COLLISION)

            if self._is_keyword(assign.target.name):
                raise SemanticError(ErrorCode.SEM_ERROR)

            current_scope.add(assign.target.name)

        self.param_scope_stack.pop()
        self.scope_stack.pop()

    # ===========================================================
    # CHECK EXPRESSION
    # ===========================================================
    def _check_expr(self, expr: Expr) -> None:
        """Route the expression to the appropriate type checker."""
        if expr.block is not None:
            self._check_block(expr.block)
            return

        if expr.var is not None:
            self._check_var(expr.var)
            return

        if expr.send is not None:
            self._check_send(expr.send)
            return

        if expr.literal is not None:
            self._check_literal(expr.literal)
            return

    # ===========================================================
    # CHECK LITERAL
    # ===========================================================
    def _check_literal(self, literal: Literal) -> None:
        """Validate literal expressions, ensuring class literals exist."""
        if literal.class_id == "class":
            class_name = literal.value
            defined_classes = {cls.name for cls in self.program.classes}

            if class_name not in defined_classes and class_name not in self.builtins:
                raise SemanticError(ErrorCode.SEM_UNDEF)

    # ===========================================================
    # CHECK SEND
    # ===========================================================
    def _check_send(self, send: Send) -> None:
        """Check message sending, validating selector keywords and argument arity."""
        self._check_expr(send.receiver)

        for arg in send.args:
            self._check_expr(arg.expr)

    # ===========================================================
    # CHECK VARIABLE
    # ===========================================================
    def _check_var(self, var: Var) -> None:
        """Check if a variable usage is valid within current scope."""
        if not self._is_variable_defined(var.name):
            raise SemanticError(ErrorCode.SEM_UNDEF)

    def _is_variable_defined(self, var_name: str) -> bool:
        """Determine if a variable is defined in any active scope stack."""

        # Checks trough scopes, if variable is defined somewhere
        return any(var_name in scope for scope in reversed(self.scope_stack))

    def _is_parameter_name(self, var_name: str) -> bool:
        """Check if a variable name collides with any active block parameter."""

        return any(var_name in params for params in reversed(self.param_scope_stack))

    # ===========================================================
    # CHECK KEYWORDS / BUILTINS
    # ===========================================================
    def _is_keyword(self, name: str) -> bool:
        """Check if the given name is a reserved keyword."""
        return name in self.keywords

    def _is_builtin(self, name: str) -> bool:
        """Check if the given name is a built-in class."""
        return name in self.builtins
