from interpreter.error_codes import ErrorCode
from interpreter.input_model import Block, ClassDef, Expr, Program, Var, Literal, Send

from interpreter.exceptions import SemanticError



class StaticAnalyzer:
    def __init__(self, program: Program) -> None:
        self.program = program
        self.scope_stack: list[set[str]] = []
        self.builtins = {"Object", "Nil", "Integer", "String", "Block", "True", "False"}
        self.keywords = {"class", "self", "super", "nil", "true", "false"}
# ===========================================================
# ENTRY POINT
# ===========================================================
    def run(self) -> None:
        self.check_classes()
        self.check_main()
        for cls in self.program.classes:
            self.check_methods(cls)
# ===========================================================
# CHECK CLASSES
# ===========================================================
    def check_classes(self) -> None:
        names = [cls.name for cls in self.program.classes]
        if len(names) != len(set(names)):
            raise SemanticError(ErrorCode.SEM_ERROR)

        for cls in self.program.classes:
            if cls.parent == cls.name:
                raise SemanticError(ErrorCode.SEM_ERROR)
            if cls.parent not in names and cls.parent not in self.builtins:
                raise SemanticError(ErrorCode.SEM_UNDEF)
            if self.is_builtin(cls.name):
                raise SemanticError(ErrorCode.SEM_ERROR)
            if self.is_keyword(cls.name):
                raise SemanticError(ErrorCode.SEM_ERROR)
# ===========================================================
# CHECK MAIN
# ===========================================================
    def check_main(self) -> None:
        for cls in self.program.classes:
            if cls.name == "Main":
                for method in cls.methods:
                    if method.selector == "run":
                        if method.block.arity != 0:
                            raise SemanticError(ErrorCode.SEM_MAIN)
                        return
        raise SemanticError(ErrorCode.SEM_MAIN)
# ===========================================================
# CHECK METHODS
# ===========================================================
    def check_methods(self, cls: ClassDef) -> None:
        selector_names = [m.selector for m in cls.methods]
        if len(selector_names) != len(set(selector_names)):
            raise SemanticError(ErrorCode.SEM_ERROR)

        for method in cls.methods:
            expected_arity = method.selector.count(":")
            if method.block.arity != expected_arity:
                raise SemanticError(ErrorCode.SEM_ARITY)
            
            self.scope_stack.append({'self', 'super', 'true', 'false', 'nil'})
            self.check_block(method.block)
            self.scope_stack.pop()
# ===========================================================
# CHECK BLOCK
# ===========================================================
    def check_block(self, block: Block) -> None:
        if block.arity != len(block.parameters):
            raise SemanticError(ErrorCode.SEM_ARITY)

        param_names = [p.name for p in block.parameters]
        for name in param_names:
            if self.is_keyword(name):
                raise SemanticError(ErrorCode.SEM_ERROR)

        if len(param_names) != len(set(param_names)):
            raise SemanticError(ErrorCode.SEM_ERROR)

        current_scope = set(param_names)
        self.scope_stack.append(current_scope)

        for assign in block.assigns:
            self.check_expr(assign.expr)
            if assign.target.name in param_names:
                raise SemanticError(ErrorCode.SEM_COLLISION)
            
            if self.is_keyword(assign.target.name):
                raise SemanticError(ErrorCode.SEM_COLLISION)

            current_scope.add(assign.target.name)

        self.scope_stack.pop()
# ===========================================================
# CHECK EXPRESSION
# ===========================================================
    def check_expr(self, expr: Expr) -> None:
        if expr.block is not None:
            self.check_block(expr.block)
            return

        if expr.var is not None:
            self.check_var(expr.var)
            return

        if expr.send is not None:
            self.check_send(expr.send)
            return
        
        if expr.literal is not None:
            self.check_literal(expr.literal)
            return
# ===========================================================
# CHECK LITERAL
# ===========================================================
    def check_literal(self, literal: Literal) -> None:
        if literal.class_id == "class":
            class_name = literal.value
            defined_classes = {cls.name for cls in self.program.classes}

            if class_name not in defined_classes and class_name not in self.builtins:
                raise SemanticError(ErrorCode.SEM_UNDEF)
# ===========================================================
# CHECK SEND
# ===========================================================
    def check_send(self, send: Send) -> None:
        self.check_expr(send.receiver) #nikdy nie je None

        # expected_arity = send.selector.count(":")
        # if len(send.args) != expected_arity:
        #    raise SemanticError(ErrorCode.SEM_ARITY)
        
        for arg in send.args:
            self.check_expr(arg.expr)
# ===========================================================
# CHECK VARIABLE
# ===========================================================
    def check_var(self, var: Var) -> None:
        if not self.is_variable_defined(var.name):
            raise SemanticError(ErrorCode.SEM_UNDEF)
        
    def is_variable_defined(self, var_name: str) -> bool:
        for scope in reversed(self.scope_stack):
            if var_name in scope:
                return True
        return False
# ===========================================================
# CHECK KEYWORDS / BUILTINS
# ===========================================================    
    def is_keyword(self, name: str) -> bool:
        return name in self.keywords
    
    def is_builtin(self, name: str) -> bool:
        return name in self.builtins