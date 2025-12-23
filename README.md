# Rascal Compiler 
This repository contains a complete compiler for the Rascal language (a reduced version of Pascal), developed for a Compilers course. The compiler translates Rascal source code into instructions for a stack-based virtual machine called MEPA.

## Technologies
- Python 3.x
- PLY (Python Lex-Yacc): A tool for Lexical (Lex) and Syntactic (LALR) analysis.
- MEPA: A stack machine execution environment for Pascal-like languages.

## Architecture
The compiler is structured following the classic compilation phases, using an Object-Oriented approach for the Intermediate Representation (IR).

1. Lexical Analyzer (rascal_lexer.py)
 - Uses Regular Expressions (Regex) to identify tokens such as reserved keywords (if, then, while, program), identifiers, numbers, and operators.

2. Syntactic Analyzer & AST (rascal_parser.py and rascal_ast.py)
 - LALR Parsing: Implements a context-free grammar using the PLY library.

 - Bottom-Up Construction: The Abstract Syntax Tree (AST) is built from the leaves up to the root during grammar reductions.

 - Structural Mapping: Each language construct (assignment, conditional, loop) is mapped to a specific AST Class, facilitating multi-pass analysis.

3. Semantic Analyzer (rascal_semantic.py)
Implemented using the Visitor Design Pattern.

Scope Management: Hierarchical linked symbol tables that support static scoping (global and local scopes).

Type Checking: Validation of integer and boolean expressions.

Function Returns: Implements an internal variable naming convention (prefixed with @) to map return addresses and values in the MEPA stack.

4. Code Generator (rascal_codegen.py)
Also based on the Visitor Pattern, it traverses the validated AST and emits the corresponding MEPA instructions.

Stack Arithmetic: Translates infix expressions into postfix stack operations.

Control Flow: Manages dynamic labels for jumping instructions (DSVF, DSVS).

📋 Supported Features
[x] Primitive Types: integer, boolean.
[x] Control Structures: if-then-else, while.
[x] Subroutines: Procedures and Functions with recursion support.
[x] I/O Operations: read and write commands.
[x] Static Scoping: Global and local variables with lexical level management.

🛠️ How to Run
Prerequisites: Ensure you have Python 3 and PLY installed:
```
pip install ply
```
Compile a file:
```
python rascal_compiler.py example.rascal
```
Output: The compiler will generate a .mepa file containing the machine code ready to be executed in a MEPA simulator.

## Rascal Code Example

program Example;
var x, res : integer;

function factorial(n : integer) : integer;
begin
    if n = 0 then
        factorial := 1
    else
        factorial := n * factorial(n - 1);
end;

begin
    read(x);
    res := factorial(x);
    write(res);
end.
