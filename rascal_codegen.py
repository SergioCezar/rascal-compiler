from typing import List
from rascal_ast import *

#Percorre AST e emite instruções MEPA
class CodeGenerator:
    def __init__(self):
        self.code: List[str] = []
        self.next_label_number = 0
        self.current_level = 0  

    # Adiciona uma instrução à lista
    def emit(self, instr: str, *args):
        if args:
            arg_str = ",".join(map(str, args))
            self.code.append(f"     {instr} {arg_str}")
        else:
            self.code.append(f"     {instr}")

    def new_label(self):
        L = f"R{self.next_label_number:02d}"
        self.next_label_number += 1
        return L

    def emit_label(self, label: str):
        self.code.append(f"{label}: NADA")

    #Padrão Visitor manual para mandar nós da AST
    def visit(self, node: Node):
        if not node:
            return
        method = getattr(self, f'visit_{node.type}', self.generic_visit)
        return method(node)

    def generic_visit(self, node: Node):
        pass

    def visit_program(self, node: Program):
        self.emit("INPP")
        self.visit(node.block)
        self.emit("PARA")
        self.emit("FIM")

    def visit_block(self, node: Block):

        #Alocação de memória para variáveis locais do bloco
        vars_count = sum(len(d.identifiers) for d in node.var_declarations)
        if vars_count > 0:
            self.emit("AMEM", vars_count)

        # Se houver sub-rotinas, gera DSVS para não executá-las linearmente
        if node.subroutine_declarations:
            lab_main = self.new_label()
            self.emit("DSVS", lab_main)

            for sub in node.subroutine_declarations:
                self.visit(sub)
            self.emit_label(lab_main)


        self.visit(node.compound_statement)

        if vars_count > 0:
            self.emit("DMEM", vars_count)

    # Declaração de Procedimento
    def visit_proc_declaration(self, node: ProcedureDeclaration):
            label = self.new_label()
            node.entry.label = label
            level = node.entry.level  

            self.emit_label(label)
            self.emit("ENPR", level)

            # Salva o nível anterior e define o atual para o nível deste procedimento
            previous_level = self.current_level
            self.current_level = level

            self.visit(node.block)

            # Restaura o nível anterior (saiu do procedimento)
            self.current_level = previous_level

            num_params = sum(len(p.identifiers) for p in node.params)
            self.emit("RTPR", num_params)

    def visit_func_declaration(self, node: FunctionDeclaration):
            label = self.new_label()
            node.entry.label = label
            level = node.entry.level

            self.emit_label(label)
            self.emit("ENPR", level)

            # Salva o nível anterior e define o atual
            previous_level = self.current_level
            self.current_level = level

            self.visit(node.block)

            # Restaura o nível anterior
            self.current_level = previous_level

            num_params = sum(len(p.identifiers) for p in node.params)
            self.emit("RTPR", num_params)

    #Visita sequência de comandos
    def visit_seq_comandos(self, node: CompoundStatement):
        for stmt in node.statements:
            self.visit(stmt)

    def visit_cmd_atrib(self, node: Assignment):
        self.visit(node.expression)
        entry = node.variable.entry
        if entry:
            self.emit("ARMZ", entry.level, entry.offset)

    #Empilha args e chama
    def visit_proc_call(self, node: ProcedureCall):
            for arg in reversed(node.arguments):
                self.visit(arg)

            label = node.entry.label
            self.emit("CHPR", label, self.current_level)

    def visit_func_call(self, node: FunctionCall):
            self.emit("AMEM", 1)
            for arg in reversed(node.arguments):
                self.visit(arg)

            label = node.entry.label
            self.emit("CHPR", label, self.current_level)

    def visit_read(self, node: Read):
        for var in node.variables:
            self.emit("LEIT")
            entry = var.entry
            if entry:
                self.emit("ARMZ", entry.level, entry.offset)

    def visit_write(self, node: Write):
        for expr in node.expressions:
            self.visit(expr)
            self.emit("IMPR")

    #Carrega valor da variável
    def visit_exp_var(self, node: Var):
        entry = node.entry
        if entry:
            self.emit("CRVL", entry.level, entry.offset)

    #Constantes numéricas e lógicas
    def visit_exp_num(self, node: Number):
        self.emit("CRCT", node.value)

    def visit_exp_logica(self, node: Boolean):
        self.emit("CRCT", 1 if node.value == 'true' else 0)

    def visit_exp_binaria(self, node: BinaryOp):
        self.visit(node.left)
        self.visit(node.right)
        ops = {
            '+': 'SOMA', '-': 'SUBT', '*': 'MULT', 'div': 'DIVI',
            'and': 'CONJ', 'or': 'DISJ',
            '=': 'CMIG', '<>': 'CMDG', '<': 'CMME', '<=': 'CMEG', '>': 'CMMA', '>=': 'CMAG'
        }
        self.emit(ops.get(node.op, 'NADA'))

    def visit_exp_unaria(self, node: UnaryOp):
        self.visit(node.operand)
        if node.op == 'not':
            self.emit("NEGA")
        elif node.op == '-':
            self.emit("INVR")

    def visit_cmd_condicional(self, node: If):
        if node.else_statement:
            lab_end = self.new_label()  
            lab_else = self.new_label()  

            # condição
            self.visit(node.condition)
            self.emit("DSVF", lab_else)

            # bloco THEN
            self.visit(node.then_statement)

            # salto para o fim
            self.emit("DSVS", lab_end)

            # bloco ELSE
            self.emit_label(lab_else)
            self.visit(node.else_statement)

            # fim
            self.emit_label(lab_end)

        else:
            lab_end = self.new_label()

            self.visit(node.condition)
            self.emit("DSVF", lab_end)

            self.visit(node.then_statement)

            self.emit_label(lab_end)


    def visit_cmd_repeticao(self, node: While):
        lab_ini = self.new_label()
        lab_end = self.new_label()
        self.emit_label(lab_ini)
        self.visit(node.condition)
        self.emit("DSVF", lab_end) #Falso sai do loop
        self.visit(node.statement)
        self.emit("DSVS", lab_ini) #Volta para o início
        self.emit_label(lab_end)

    def get_code(self) -> str:
        return "\n".join(self.code)