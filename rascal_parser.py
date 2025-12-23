import ply.yacc as yacc
from rascal_lexer import tokens
from rascal_ast import *

precedence = (
    ('nonassoc', 'EQUALS', 'NE', 'LT', 'LE', 'GT', 'GE'),
    ('left', 'PLUS', 'MINUS', 'OR'),
    ('left', 'TIMES', 'DIV', 'AND'),
    ('right', 'NOT', 'UMINUS'),
)

def p_programa(p):
    '''programa : PROGRAM ID SEMI bloco DOT'''
    p[0] = Program(p[2], p[4])

def p_bloco(p):
    '''bloco : secao_vars_opt secao_sub_opt comando_composto'''
    p[0] = Block(p[1], p[2], p[3])

def p_secao_vars_opt(p):
    '''secao_vars_opt : VAR declaracao_vars_lista
                      | empty'''
    p[0] = p[2] if len(p) == 3 else []

def p_declaracao_vars(p):
    '''declaracao_vars : lista_ids COLON tipo'''
    p[0] = VarDeclaration(p[1], p[3])

def p_declaracao_vars_lista(p):
    '''declaracao_vars_lista : declaracao_vars_lista declaracao_vars SEMI
                             | declaracao_vars SEMI'''
    p[0] = p[1] + [p[2]] if len(p) == 4 else [p[1]]

def p_lista_ids(p):
    '''lista_ids : lista_ids COMMA ID
                 | ID'''
    if len(p) == 4:
        p[0] = p[1] + [Var(p[3])]
    else:
        p[0] = [Var(p[1])]

def p_secao_sub_opt(p):
    '''secao_sub_opt : secao_sub_opt declaracao_proc SEMI
                      | secao_sub_opt declaracao_func SEMI
                      | empty'''
    if len(p) == 4:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = []

def p_declaracao_proc(p):
    '''declaracao_proc : PROCEDURE ID params_opt SEMI bloco'''
    p[0] = ProcedureDeclaration(p[2], p[3], p[5])

def p_declaracao_func(p):
    '''declaracao_func : FUNCTION ID params_opt COLON tipo SEMI bloco'''
    p[0] = FunctionDeclaration(p[2], p[3], p[5], p[7])

def p_params_opt(p):
    '''params_opt : LPAREN declaracao_params_lista RPAREN
                  | empty'''
    p[0] = p[2] if len(p) == 4 else []

def p_declaracao_params_lista(p):
    '''declaracao_params_lista : declaracao_params_lista SEMI declaracao_vars
                               | declaracao_vars'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

def p_leitura(p):
    '''leitura : READ LPAREN lista_ids RPAREN'''
    p[0] = Read(p[3])

def p_escrita(p):
    '''escrita : WRITE LPAREN lista_exprs RPAREN'''
    p[0] = Write(p[3])    

def p_tipo(p):
    '''tipo : INTEGER
            | BOOLEAN'''
    p[0] = Type(p[1])

def p_lista_comandos(p):
    '''lista_comandos : lista_comandos SEMI comando
                      | comando'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

def p_comando_composto(p):
    '''comando_composto : BEGIN lista_comandos END'''
    p[0] = CompoundStatement(p[2])

def p_comando(p):
    '''comando : atribuicao
               | condicional
               | repeticao
               | leitura
               | escrita
               | chamada_proc
               | comando_composto
               | empty'''
    p[0] = p[1]

def p_chamada_proc(p):
    '''chamada_proc : ID LPAREN lista_exprs RPAREN
                    | ID LPAREN RPAREN'''
    if len(p) == 5:
        p[0] = ProcedureCall(p[1], p[3])
    else:
        p[0] = ProcedureCall(p[1], [])

def p_condicional(p):
    '''condicional : IF expressao THEN comando
                   | IF expressao THEN comando ELSE comando'''
    if len(p) == 5:
        p[0] = If(p[2], p[4])
    else:
        p[0] = If(p[2], p[4], p[6])

def p_repeticao(p):
    '''repeticao : WHILE expressao DO comando'''
    p[0] = While(p[2], p[4])

def p_atribuicao(p):
    '''atribuicao : ID ASSIGN expressao'''
    p[0] = Assignment(Var(p[1]), p[3])

def p_expressao(p):
    '''expressao : expr_simples relacao expr_simples
                 | expr_simples'''
    if len(p) == 4:
        p[0] = BinaryOp(p[1], p[2], p[3])
    else:
        p[0] = p[1]

def p_relacao(p):
    '''relacao : EQUALS
               | NE
               | LT
               | LE
               | GT
               | GE'''
    p[0] = p[1]

def p_lista_exprs(p):
    '''lista_exprs : lista_exprs COMMA expressao
                   | expressao'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

def p_expr_simples(p):
    '''expr_simples : expr_simples PLUS termo
                    | expr_simples MINUS termo
                    | expr_simples OR termo
                    | termo'''
    if len(p) == 4:
        p[0] = BinaryOp(p[1], p[2], p[3])
    else:
        p[0] = p[1]

#Termo (multiplicações e divisões)
def p_termo(p):
    '''termo : termo TIMES fator
             | termo DIV fator
             | termo AND fator
             | fator'''
    if len(p) == 4:
        p[0] = BinaryOp(p[1], p[2], p[3])
    else:
        p[0] = p[1]

#Fator (unidade básica da expressão)
def p_fator(p):
    '''fator : variavel
             | numero
             | logico
             | LPAREN expressao RPAREN
             | NOT fator
             | chamada_func'''
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 3:
        p[0] = UnaryOp(p[1], p[2])
    else:
        p[0] = p[2]

def p_fator_neg(p):
    '''fator : MINUS fator %prec UMINUS'''
    p[0] = UnaryOp(p[1], p[2])

def p_chamada_func(p):
    '''chamada_func : ID LPAREN lista_exprs RPAREN
                    | ID LPAREN RPAREN'''
    if len(p) == 5:
        p[0] = FunctionCall(p[1], p[3])
    else:
        p[0] = FunctionCall(p[1], [])

# Regras básicas para terminais
def p_variavel(p):
    '''variavel : ID'''
    p[0] = Var(p[1])

def p_numero(p):
    '''numero : NUMBER'''
    p[0] = Number(p[1])

def p_logico(p):
    '''logico : TRUE
              | FALSE'''
    p[0] = Boolean(p[1])

def p_empty(p):
    '''empty :'''
    pass

def p_error(p):
    global SYNTACTIC_ERROR
    if p:
        print(f"SINTAXE: Erro em '{p.value}' linha {p.lineno}")
    else:
        print("SINTAXE: Fim inesperado do arquivo")

parser = yacc.yacc()