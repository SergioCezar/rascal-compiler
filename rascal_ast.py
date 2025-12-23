from __future__ import annotations
from typing import List, Dict, Optional

#Nó base genérico para todos os elementos da árvore
class Node:
    def __init__(self, type: str):
        self.type = type
        self.entry = None

#Representa a raiz do programa (nome + bloco principal)
class Program(Node):
    def __init__(self, name: str, block: 'Block'):
        super().__init__('program')
        self.name = name
        self.block = block

#Representa um escopo: contém declarações e o corpo de comandos
class Block(Node):
    def __init__(self, var_decls: List['VarDeclaration'], sub_decls: List['SubroutineDeclaration'], stmt: 'CompoundStatement'):
        super().__init__('block')
        self.var_declarations = var_decls
        self.subroutine_declarations = sub_decls
        self.compound_statement = stmt

#Declaração de variáveis (ex: x, y : integer)
class VarDeclaration(Node):
    def __init__(self, identifiers: List['Var'], var_type: 'Type'):
        super().__init__('var_declaration')
        self.identifiers = identifiers
        self.var_type = var_type

#Representa os tipos primitivos (integer, boolean)
class Type(Node):
    def __init__(self, name: str):
        super().__init__('type')
        self.name = name

#Classe base abstrata para Funções e Procedimentos
class SubroutineDeclaration(Node):
    pass

#Declaração de Procedimento (sem retorno)
class ProcedureDeclaration(SubroutineDeclaration):
    def __init__(self, name: str, params: List['VarDeclaration'], block: 'Block'):
        super().__init__('proc_declaration')
        self.name = name
        self.params = params
        self.block = block

#Declaração de Função (com tipo de retorno)
class FunctionDeclaration(SubroutineDeclaration):
    def __init__(self, name: str, params: List['VarDeclaration'], return_type: 'Type', block: 'Block'):
        super().__init__('func_declaration')
        self.name = name
        self.params = params
        self.return_type = return_type
        self.block = block

#Bloco de comandos delimitado por begin/end
class CompoundStatement(Node):
    def __init__(self, statements: List['Statement']):
        super().__init__('seq_comandos')
        self.statements = statements

# Classe base para comandos executáveis
class Statement(Node):
    pass

#Comando de atribuição (:=)
class Assignment(Statement):
    def __init__(self, variable: 'Var', expression: 'Expression'):
        super().__init__('cmd_atrib')
        self.variable = variable
        self.expression = expression

#Estrutura condicional
class If(Statement):
    def __init__(self, condition: 'Expression', then_stmt: 'Statement', else_stmt: Optional['Statement']=None):
        super().__init__('cmd_condicional')
        self.condition = condition
        self.then_statement = then_stmt
        self.else_statement = else_stmt

#Estrutura de repetição
class While(Statement):
    def __init__(self, condition: 'Expression', statement: 'Statement'):
        super().__init__('cmd_repeticao')
        self.condition = condition
        self.statement = statement

#Chamada de procedimento como comando
class ProcedureCall(Statement):
    def __init__(self, name: str, args: List['Expression']):
        super().__init__('proc_call')
        self.name = name
        self.arguments = args

#Comando de leitura
class Read(Statement):
    def __init__(self, variables: List['Var']):
        super().__init__('read')
        self.variables = variables

#Comando de escrita
class Write(Statement):
    def __init__(self, expressions: List['Expression']):
        super().__init__('write')
        self.expressions = expressions

# Classe base para expressões que retornam valor
class Expression(Node):
    pass

#Operações binárias (+, -, *, div, and, or, <, >, etc.)
class BinaryOp(Expression):
    def __init__(self, left: Expression, op: str, right: Expression):
        super().__init__('exp_binaria')
        self.left = left
        self.op = op
        self.right = right

#Operações unárias (not)
class UnaryOp(Expression):
    def __init__(self, op: str, operand: Expression):
        super().__init__('exp_unaria')
        self.op = op
        self.operand = operand

#Uso de variável em uma expressão
class Var(Expression):
    def __init__(self, name: str):
        super().__init__('exp_var')
        self.name = name

#Literal numérico
class Number(Expression):
    def __init__(self, value: int):
        super().__init__('exp_num')
        self.value = value

#Literal booleano
class Boolean(Expression):
    def __init__(self, value: str):
        super().__init__('exp_logica')
        self.value = value


#Chamada de função dentro de uma expressão
class FunctionCall(Expression):
    def __init__(self, name: str, args: List[Expression]):
        super().__init__('func_call')
        self.name = name
        self.arguments = args

# ===================================================================
# 2. PRINT AST (Visualizador)
# ===================================================================
class PrintAST:
    def __init__(self):
        self.level = 0

    # Imprime mensagem com indentação certa
    def print_node(self, msg):
        print("  " * self.level + msg)

    #Chama o método específico para o tipo do nó
    def visit(self, node):
        if not node: return
        #Manda para visit_program, visit_block, etc.
        method = getattr(self, f'visit_{node.type}', self.generic_visit)
        return method(node)

    def generic_visit(self, node):
        pass

    def visit_program(self, node):
        self.print_node(f"Program: {node.name}")
        self.level += 1; self.visit(node.block); self.level -= 1

    def visit_block(self, node):
        if node.var_declarations:
            self.print_node("Vars:")
            self.level += 1
            for d in node.var_declarations: self.visit(d)
            self.level -= 1
        if node.subroutine_declarations:
            self.print_node("Subroutines:")
            self.level += 1
            for s in node.subroutine_declarations: self.visit(s)
            self.level -= 1
        self.print_node("Body:"); self.level += 1; self.visit(node.compound_statement); self.level -= 1

    def visit_var_declaration(self, node):
        ids = ", ".join([v.name for v in node.identifiers])
        self.print_node(f"{ids} : {node.var_type.name}")

    def visit_proc_declaration(self, node):
        self.print_node(f"Procedure {node.name}"); self.level += 1
        for p in node.params: self.visit(p)
        self.visit(node.block); self.level -= 1

    def visit_func_declaration(self, node):
        self.print_node(f"Function {node.name} : {node.return_type.name}"); self.level += 1
        for p in node.params: self.visit(p)
        self.visit(node.block); self.level -= 1

    def visit_seq_comandos(self, node):
        self.print_node("Begin"); self.level += 1
        for s in node.statements: self.visit(s)
        self.level -= 1; self.print_node("End")

    def visit_cmd_atrib(self, node):
        self.print_node(f"Assign {node.variable.name} :="); self.level += 1
        self.visit(node.expression); self.level -= 1

    def visit_proc_call(self, node):
        self.print_node(f"Call {node.name}"); self.level += 1
        for a in node.arguments: self.visit(a)
        self.level -= 1

    def visit_func_call(self, node):
        self.print_node(f"CallFunc {node.name}"); self.level += 1
        for a in node.arguments: self.visit(a)
        self.level -= 1

    def visit_cmd_condicional(self, node):
        self.print_node("If"); self.level += 1; self.visit(node.condition); self.level -= 1
        self.print_node("Then"); self.level += 1; self.visit(node.then_statement); self.level -= 1
        if node.else_statement:
            self.print_node("Else"); self.level += 1; self.visit(node.else_statement); self.level -= 1

    def visit_cmd_repeticao(self, node):
        self.print_node("While"); self.level += 1; self.visit(node.condition); self.level -= 1
        self.print_node("Do"); self.level += 1; self.visit(node.statement); self.level -= 1

    def visit_read(self, node):
        ids = ", ".join([v.name for v in node.variables])
        self.print_node(f"Read({ids})")

    def visit_write(self, node):
        self.print_node("Write"); self.level += 1
        for e in node.expressions: self.visit(e)
        self.level -= 1

    def visit_exp_binaria(self, node):
        self.print_node(f"Op {node.op}"); self.level += 1
        self.visit(node.left); self.visit(node.right); self.level -= 1

    def visit_exp_unaria(self, node):
        self.print_node(f"Unary {node.op}"); self.level += 1
        self.visit(node.operand); self.level -= 1

    def visit_exp_var(self, node): self.print_node(f"Var {node.name}")
    def visit_exp_num(self, node): self.print_node(f"Num {node.value}")
    def visit_exp_logica(self, node): self.print_node(f"Bool {node.value}")