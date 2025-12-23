import sys
import rascal_lexer 
import rascal_parser 
from rascal_lexer import lexer
from rascal_parser import parser
from rascal_semantic import SemanticAnalyzer
from rascal_codegen import CodeGenerator
from rascal_ast import PrintAST

def main():
    if len(sys.argv) < 3:
        print("Uso: python main.py <entrada.ras> <saida.mepa> [-pp]")
        print("  -pp : opcional, imprime a AST gerada")
        return

    infile = sys.argv[1]
    outfile = sys.argv[2]
    
    print_ast = len(sys.argv) > 3 and sys.argv[3] == '-pp'

    try:
        with open(infile, 'r', encoding='utf-8') as f:
            source = f.read()
    except Exception:
        print("Erro ao abrir arquivo de entrada.")
        return

    # ---------------------------------------------------------
    # 1. Análise Léxica
    # ---------------------------------------------------------
    # Reinicia a flag do módulo lexer
    rascal_lexer.LEXICAL_ERROR = False
    
    lexer.lineno = 1
    lexer.input(source)
    try:
        for _ in lexer: pass
    except:
        rascal_lexer.LEXICAL_ERROR = True
    
    if rascal_lexer.LEXICAL_ERROR:
        print("Erro Léxico detectado. Compilação abortada.")
        return

    # ---------------------------------------------------------
    # 2. Análise Sintática
    # ---------------------------------------------------------
    # Reinicia a flag do módulo parser
    rascal_parser.SYNTACTIC_ERROR = False
    
    lexer.lineno = 1
    lexer.input(source)
    ast = parser.parse(source, lexer=lexer)
    
    # Verifica se houve erro sintático (flag) ou se a AST veio vazia
    if rascal_parser.SYNTACTIC_ERROR or not ast:
        print("Erro Sintático detectado. Compilação abortada.")
        return

    # ---------------------------------------------------------
    # 3. Análise Semântica
    # ---------------------------------------------------------
    sem = SemanticAnalyzer()
    sem.visit(ast)
    
    if sem.has_error:
        print("Erro Semântico detectado. Compilação abortada.")
        return

    # ---------------------------------------------------------
    # 4. Impressão da AST
    # ---------------------------------------------------------
    
    # Só imprime se passou por léxico, sintático e semântico sem erros
    if print_ast:
        print("\n--- AST ---")
        printer = PrintAST()
        printer.visit(ast)
        print("-----------\n")

    # ---------------------------------------------------------
    # 5. Geração de Código
    # ---------------------------------------------------------
    cg = CodeGenerator()
    cg.visit(ast)

    try:
        with open(outfile, 'w', encoding='utf-8') as f:
            f.write(cg.get_code())
        print(f"Sucesso! Gerado '{outfile}'")
    except Exception as e:
        print(f"Erro ao gravar arquivo de saída: {e}")

if __name__ == "__main__":
    main()