import ply.lex as lex

reserved = {
    'program': 'PROGRAM', 'procedure': 'PROCEDURE', 'function': 'FUNCTION',
    'begin': 'BEGIN', 'end': 'END', 'var': 'VAR', 'integer': 'INTEGER',
    'boolean': 'BOOLEAN', 'if': 'IF', 'then': 'THEN', 'else': 'ELSE',
    'while': 'WHILE', 'do': 'DO', 'read': 'READ', 'write': 'WRITE',
    'true': 'TRUE', 'false': 'FALSE', 'not': 'NOT', 'and': 'AND',
    'or': 'OR', 'div': 'DIV'
}

tokens = [
    'ID', 'NUMBER', 'PLUS', 'MINUS', 'TIMES',
    'LPAREN', 'RPAREN', 'SEMI', 'COLON', 'COMMA', 'DOT', 'ASSIGN',
    'EQUALS', 'NE', 'LT', 'LE', 'GT', 'GE'
] + list(reserved.values())

#Regras de expressão regular para operadores e delimitadores
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_SEMI = r';'
t_COLON = r':'
t_COMMA = r','
t_DOT = r'\.'
t_ASSIGN = r':='
t_EQUALS = r'='
t_NE = r'<>'
t_LT = r'<'
t_LE = r'<='
t_GT = r'>'
t_GE = r'>='
t_ignore = ' \t'

LEXICAL_ERROR = False

def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count('\n')

#Converte a string de dígitos capturada para o tipo int
def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

#Garante que comece com letra e verifica se é palavra reservada ou ID comum.
def t_ID(t):
    r'[a-zA-Z][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value, 'ID')
    return t

# Imprime o caractere inválido, marca a flag de erro e pula o caractere para continuar.
def t_error(t):
    global LEXICAL_ERROR
    print(f"LÉXICO: Caractere ilegal '{t.value[0]}' na linha {t.lexer.lineno}")
    LEXICAL_ERROR = True
    t.lexer.skip(1)

lexer = lex.lex()