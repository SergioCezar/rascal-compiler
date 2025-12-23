from typing import List, Dict, Optional
from rascal_ast import *

#Armazenar informações de um identificador na tabela de símbolos
class SymbolEntry:
    def __init__(self, name: str, type_: Optional[str], category: str, level: int, offset: int, params: Optional[List[str]]=None, label: Optional[str]=None):
        self.name = name
        self.type = type_
        self.category = category
        self.level = level
        self.offset = offset
        self.params = params or []
        self.label = label

#Gerenciar escopos e identificadores
class SymbolTable:
    def __init__(self, parent: Optional['SymbolTable']=None, level: int=0):
        self.symbols: Dict[str, SymbolEntry] = {}
        self.parent = parent
        self.level = level
        self.offset_counter = 0

    #Insere um novo símbolo no escopo atual.
    def define(self, name: str, type_: Optional[str], category: str, params: Optional[List[str]]=None, force_offset: Optional[int]=None):
        if name in self.symbols:
            return False, None # Erro: símbolo já existe neste escopo
        if force_offset is not None:
            final_offset = force_offset
        else: #Calcula automaticamente o offset se não for forçado
            final_offset = self.offset_counter
            if category == 'var':
                self.offset_counter += 1
        entry = SymbolEntry(name, type_, category, self.level, final_offset, params)
        self.symbols[name] = entry
        return True, entry

    #Busca um símbolo no escopo atual ou nos pais
    def resolve(self, name: str) -> Optional[SymbolEntry]:
        e = self.symbols.get(name)
        if e:
            return e
        if self.parent:
            return self.parent.resolve(name)
        return None

#Visitor que percorre a AST e realiza análise semântica
class SemanticAnalyzer:
    def __init__(self):
        self.scope = SymbolTable(level=0)
        self.has_error = False
        self.current_func_name: Optional[str] = None
        self.return_assigned = False
        self.label_counter = 0  #para criar rótulos únicos para sub-rotinas

    def error(self, msg: str):
        print(f"ERRO SEMÂNTICO: {msg}")
        self.has_error = True

    #Padrão Visitor manual
    def visit(self, node: Node):
        if not node:
            return None
        method = getattr(self, f'visit_{node.type}', self.generic_visit)
        return method(node)

    def generic_visit(self, node: Node):
        for attr, value in node.__dict__.items():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, Node):
                        self.visit(item)
            elif isinstance(value, Node):
                self.visit(value)

    #Cria escopo global e visita o bloco principal
    def visit_program(self, node: Program):
        self.scope.define(node.name, None, 'program') # Registra programa no escopo
        self.visit(node.block)

    #Gerencia declarações de variáveis e sub-rotinas antes de visitar o corpo
    def visit_block(self, node: Block):
        for decl in node.var_declarations:
            self.visit(decl)

        for sub in node.subroutine_declarations:
            cat = 'proc' if isinstance(sub, ProcedureDeclaration) else 'func'
            ret_type = sub.return_type.name if hasattr(sub, 'return_type') else None
            success, entry = self.scope.define(sub.name, ret_type, cat)
            entry.level = self.scope.level + 1 
            
            # Gera label único para a sub-rotina aqui
            if not success:
                self.error(f"Redefinição de '{sub.name}'")
            else:
                # atribui rótulo único já aqui para uso do CodeGenerator
                entry.label = f"R_{sub.name}_{self.label_counter}"
                self.label_counter += 1
            sub.entry = entry

        for sub in node.subroutine_declarations:
            self.visit(sub)

        self.visit(node.compound_statement)

    def visit_var_declaration(self, node: VarDeclaration):
        type_name = node.var_type.name
        for var in node.identifiers:
            success, entry = self.scope.define(var.name, type_name, 'var')
            if not success:
                self.error(f"Variável '{var.name}' já declarada.")
            var.entry = entry

    def visit_proc_declaration(self, node: ProcedureDeclaration):
        parent_scope = self.scope
        self.scope = SymbolTable(parent=parent_scope, level=parent_scope.level + 1)

        all_params = []
        param_types = []
        for p_decl in node.params:
            tname = p_decl.var_type.name
            for v in p_decl.identifiers:
                all_params.append((v, tname))
                param_types.append(tname)

        # Cálculo de offset negativo para parâmetros na pilha MEPA
        for i, (var_node, t_name) in enumerate(all_params):
            offset = -5 - i
            success, entry = self.scope.define(var_node.name, t_name, 'param', force_offset=offset)
            var_node.entry = entry

        proc_sym = parent_scope.resolve(node.name)
        if proc_sym:
            proc_sym.params = param_types

        self.visit(node.block)

        self.scope = parent_scope

    #Parecido com procedimento, mas gerencia variável de retorno
    def visit_func_declaration(self, node: FunctionDeclaration):
        parent_scope = self.scope
        old_func = self.current_func_name
        self.current_func_name = node.name
        self.return_assigned = False

        self.scope = SymbolTable(parent=parent_scope, level=parent_scope.level + 1)

        all_params = []
        param_types = []
        for p_decl in node.params:
            tname = p_decl.var_type.name
            for v in p_decl.identifiers:
                all_params.append((v, tname))
                param_types.append(tname)
 
        total = len(all_params)
        for i, (var_node, t_name) in enumerate(all_params):
            offset = -5 - i
            _, entry = self.scope.define(var_node.name, t_name, 'param', force_offset=offset)
            var_node.entry = entry

        ret_offset = -5 - total

        # declara @func
        func_sym = parent_scope.resolve(node.name)
        ret_type = func_sym.type if func_sym else node.return_type.name
        ret_var_name = f"@{node.name}"
        _, ret_entry = self.scope.define(ret_var_name, ret_type, 'var', force_offset=ret_offset)

        for i, (var_node, t_name) in enumerate(all_params):
            offset = -4 - (total - i)
            _, entry = self.scope.define(var_node.name, t_name, 'param', force_offset=offset)
            var_node.entry = entry

        if func_sym:
            func_sym.params = param_types

        self.visit(node.block)

        if not self.return_assigned:
            self.error(f"Função '{node.name}' não possui atribuição ao valor de retorno.")

        self.current_func_name = old_func
        self.scope = parent_scope



    def visit_cmd_atrib(self, node: Assignment):
        var_name = node.variable.name
        # reconhecer atribuição ao @func (retorno) quando variável tem mesmo nome que função
        if self.current_func_name and var_name == self.current_func_name:
            self.return_assigned = True
            var_name = f"@{self.current_func_name}"

        entry = self.scope.resolve(var_name)
        if not entry:
            self.error(f"Variável '{node.variable.name}' não declarada.")
            return

        if entry.category not in ['var', 'param']:
            self.error(f"Não é possível atribuir valor a '{var_name}' (categoria: {entry.category}).")
            return

        node.variable.entry = entry
        expr_type = self.visit(node.expression)
        if expr_type != entry.type:
            self.error(f"Atribuição incompatível para '{node.variable.name}'. Esperado {entry.type}, encontrado {expr_type}.")

    # Uso de variável em expressão
    def visit_exp_var(self, node: Var):
        entry = self.scope.resolve(node.name)
        if not entry:
            self.error(f"Variável '{node.name}' não encontrada.")
            return 'integer'
        if entry.category == 'func':
            self.error(f"Chamada de função '{node.name}' requer parênteses ou a função não foi usada corretamente.")
            return entry.type
        node.entry = entry
        return entry.type

    #Valida Variáveis
    def visit_read(self, node: Read):
        for var in node.variables:
            entry = self.scope.resolve(var.name)
            if not entry:
                self.error(f"Read em variável não declarada '{var.name}'")
            elif entry.category not in ['var', 'param']:
                self.error(f"Read espera variável, encontrou '{var.name}' ({entry.category})")
            var.entry = entry

    #Chamada de procedimento, verificando declaração e argumentos
    def visit_proc_call(self, node: ProcedureCall):
        sym = self.scope.resolve(node.name)
        if not sym or sym.category != 'proc':
            self.error(f"Procedimento '{node.name}' desconhecido.")
            return
        if len(node.arguments) != len(sym.params):
            self.error(f"Argumentos incorretos para '{node.name}'. Esperado {len(sym.params)}, recebido {len(node.arguments)}.")
            return
        node.entry = sym
        for i, arg in enumerate(node.arguments):
            arg_type = self.visit(arg)
            expected = sym.params[i]
            if arg_type != expected:
                self.error(f"Argumento {i+1} de '{node.name}' incompatível. Esperado {expected}, encontrado {arg_type}.")

    #Chamada de função, verificando e retornando tipo
    def visit_func_call(self, node: FunctionCall):
        sym = self.scope.resolve(node.name)
        if not sym or sym.category != 'func':
            self.error(f"Função '{node.name}' desconhecida.")
            return 'integer'
        if len(node.arguments) != len(sym.params):
            self.error(f"Argumentos incorretos para '{node.name}'. Esperado {len(sym.params)}, recebido {len(node.arguments)}.")
            return sym.type
        node.entry = sym
        for i, arg in enumerate(node.arguments):
            arg_type = self.visit(arg)
            expected = sym.params[i]
            if arg_type != expected:
                self.error(f"Argumento {i+1} de '{node.name}' incompatível. Esperado {expected}, encontrado {arg_type}.")
        return sym.type

    def visit_exp_binaria(self, node: BinaryOp):
        l_type = self.visit(node.left)
        r_type = self.visit(node.right)
        if node.op in ['+', '-', '*', 'div']:
            if l_type != 'integer' or r_type != 'integer':
                self.error(f"Operação '{node.op}' requer inteiros. Encontrado {l_type}, {r_type}.")
            return 'integer'
        if node.op in ['and', 'or']:
            if l_type != 'boolean' or r_type != 'boolean':
                self.error(f"Operação '{node.op}' requer booleanos. Encontrado {l_type}, {r_type}.")
            return 'boolean'
        if node.op in ['=', '<>', '<', '<=', '>', '>=']:
            if node.op in ['<', '<=', '>', '>=']:
                if l_type != 'integer' or r_type != 'integer':
                    self.error(f"Operação relacional '{node.op}' requer inteiros.")
            if l_type != r_type:
                self.error(f"Comparação '{node.op}' entre tipos diferentes: {l_type} e {r_type}.")
            return 'boolean'
        return 'integer'

    def visit_exp_unaria(self, node: UnaryOp):
        t = self.visit(node.operand)
        if node.op == 'not':
            if t != 'boolean': self.error(f"'not' requer booleano.")
            return 'boolean'
        elif node.op == '-':
            if t != 'integer': self.error(f"'-' unário requer inteiro.")
            return 'integer'
        return t

    def visit_exp_num(self, node: Number):
        return 'integer'

    def visit_exp_logica(self, node: Boolean):
        return 'boolean'

    def visit_write(self, node: Write):
        for e in node.expressions:
            t = self.visit(e)
            if t not in ['integer', 'boolean']:
                self.error(f"Write não suporta tipo {t}")

    def visit_cmd_condicional(self, node: If):
        t = self.visit(node.condition)
        if t != 'boolean':
            self.error("Condição do IF deve ser booleana.")
        self.visit(node.then_statement)
        if node.else_statement:
            self.visit(node.else_statement)

    def visit_cmd_repeticao(self, node: While):
        t = self.visit(node.condition)
        if t != 'boolean':
            self.error("Condição do WHILE deve ser booleana.")
        self.visit(node.statement)

    def visit_seq_comandos(self, node: CompoundStatement):
        for s in node.statements:
            self.visit(s)