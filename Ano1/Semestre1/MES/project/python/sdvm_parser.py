"""
Parser para a linguagem SDVM-Lang
Manutencao e Evolucao de Software

Feito com parser combinators (biblioteca parsy), como o exemplo
expAST.py dado nas aulas. E a traducao para Python do parser em Haskell.

Instalar a biblioteca:
    pip install parsy

Correr:
    python sdvm_parser.py exemplos/factorial exemplos/fibonacci ...   -> OK / ERRO
    python sdvm_parser.py --ast exemplos/factorial                    -> mostra a AST

Testar pecas soltas (no terminal interativo do Python):
    python -i sdvm_parser.py
    >>> expression.parse("1 + 2 * 3")
"""

import re
import sys
from dataclasses import dataclass

from parsy import (ParseError, alt, eof, fail, forward_declaration,
                   line_info_at, regex, seq, string, success)

# ======================================================================
# 1. AST (a arvore que o parser constroi)
# ======================================================================

# ---------- tipos ----------
# guardamos os tipos como texto: "int", "double", "char", "bool", "void"

# ---------- expressoes ----------

@dataclass
class IntLit:
    value: int

@dataclass
class FloatLit:
    value: str

@dataclass
class CharLit:
    value: str              # com as plicas, ex: "'A'"

@dataclass
class StringLit:
    value: str              # com as aspas, ex: '"ola"'

@dataclass
class BoolLit:
    value: bool

@dataclass
class Ident:
    name: str

@dataclass
class Index:                # a[i]
    array: object
    index: object

@dataclass
class Call:                 # f(x, y)
    function: object
    args: list

@dataclass
class Unary:                # -x   !b
    op: str
    exp: object

@dataclass
class Binary:               # a + b
    op: str
    left: object
    right: object

@dataclass
class Cast:                 # (double) x
    type: str
    exp: object

# ---------- declaracoes de variaveis ----------

@dataclass
class Var:                  # int x = 1;
    type: str
    name: str
    init: object            # None se nao tiver valor inicial

@dataclass
class Array:                # int a[3] = {1,2,3};
    type: str
    name: str
    size: int
    init: object            # lista de expressoes, ou None

# ---------- instrucoes ----------

@dataclass
class Block:
    stmts: list

@dataclass
class LocalVar:
    decl: object

@dataclass
class Assign:               # x = e;
    name: str
    exp: object

@dataclass
class AssignIndex:          # a[i] = e;
    name: str
    index: object
    exp: object

@dataclass
class If:
    cond: object
    then: object
    else_: object           # None se nao tiver else

@dataclass
class While:
    cond: object
    body: object

@dataclass
class For:
    init: object            # None se nao existir
    cond: object            # None se nao existir
    update: object          # None se nao existir
    body: object

@dataclass
class Return:
    exp: object             # None em "return;"

@dataclass
class Print:
    exp: object

@dataclass
class ReadVar:
    name: str

@dataclass
class Break:
    pass

@dataclass
class Continue:
    pass

@dataclass
class ExpStmt:              # f(x);
    exp: object

# ---------- topo do programa ----------

@dataclass
class GlobalVar:
    decl: object

@dataclass
class Function:
    ret_type: str
    name: str
    params: list            # lista de pares (tipo, nome)
    body: list              # lista de instrucoes

# um programa e uma lista de GlobalVar / Function

# ======================================================================
# 2. LEXICO: espacos, comentarios, palavras, numeros, texto
# ======================================================================

# salta espacos, comentarios // e comentarios /* */
spaces = regex(r'(?:\s+|//[^\n]*|/\*.*?\*/)*', flags=re.DOTALL)

def lexeme(p):
    """le p e salta os espacos que vem a seguir"""
    return p << spaces

def sym(s):
    """simbolos: ( ) { } ; , + - == ..."""
    return lexeme(string(s))

KEYWORDS = {"int", "double", "char", "bool", "void",
            "if", "else", "while", "for", "break", "continue", "return",
            "print", "read", "true", "false"}

def kw(k):
    """palavra reservada ("int" nao pode ser o inicio de "integer")"""
    return lexeme(regex(k + r'(?![A-Za-z0-9_])'))

def nao_reservada(nome):
    """so aceita o nome se nao for palavra reservada"""
    if nome in KEYWORDS:
        return fail("identificador (e nao a palavra reservada " + nome + ")")
    return success(nome)

# IDENTIFIER = [A-Za-z][A-Za-z0-9_]*   e nao pode ser palavra reservada
ident = lexeme(regex(r'[A-Za-z][A-Za-z0-9_]*')).bind(nao_reservada)

# FLOAT = [0-9]+\.[0-9]+([eE][+-]?[0-9]+)?
float_lit = lexeme(regex(r'[0-9]+\.[0-9]+(?:[eE][+-]?[0-9]+)?'))

# INTEGER = [0-9]+
int_lit = lexeme(regex(r'[0-9]+')).map(int)

# CHAR = '([^'\\]|\\.)'
char_lit = lexeme(regex(r"'(?:[^'\\]|\\.)'"))

# STRING = "([^"\\]|\\.)*"
string_lit = lexeme(regex(r'"(?:[^"\\]|\\.)*"'))

# ======================================================================
# 3. EXPRESSOES (da menor para a maior prioridade)
# ======================================================================

expression = forward_declaration()     # definida mais abaixo (e recursiva)
unary = forward_declaration()

def left(op, operando):
    """operadores associativos a esquerda:  a - b - c  =  (a - b) - c"""
    def junta(primeiro, resto):
        e = primeiro
        for (o, direita) in resto:
            e = Binary(o, e, direita)
        return e
    return seq(operando, seq(op, operando).many()).combine(junta)

# type ::= "int" | "double" | "char" | "bool"
type_ = kw("int") | kw("double") | kw("char") | kw("bool")

# argument_list ::= expression { "," expression }
args = expression.sep_by(sym(","), min=1)

# primary ::= INTEGER | FLOAT | CHAR | STRING | "true" | "false" | IDENTIFIER
#           | "(" type ")" expression | "(" expression ")"
# NOTA: no cast usamos unary (e nao expression), como em C, para que
#       (double) a / b  seja  ((double) a) / b
primary = alt(
    float_lit.map(FloatLit),
    int_lit.map(IntLit),
    char_lit.map(CharLit),
    string_lit.map(StringLit),
    kw("true").result(BoolLit(True)),
    kw("false").result(BoolLit(False)),
    ident.map(Ident),
    seq(sym("(") >> type_ << sym(")"), unary).combine(Cast),
    sym("(") >> expression << sym(")"),
)

# function_call ::= primary "(" [ argument_list ] ")"
call = seq(primary, sym("(") >> args.optional([]) << sym(")")).combine(Call)

# postfix ::= primary "[" expression "]" | function_call | primary
postfix = alt(
    seq(primary, sym("[") >> expression << sym("]")).combine(Index),
    call,
    primary,
)

# unary ::= [ "+" | "-" | "!" ] postfix
unary.become(
    seq(sym("+") | sym("-") | sym("!"), unary).combine(Unary)
    | postfix
)

# os niveis de prioridade (cada um usa o seguinte)
multiplicative = left(sym("*") | sym("/") | sym("%"), unary)
additive       = left(sym("+") | sym("-"), multiplicative)
comparison     = left(sym("<=") | sym(">=") | sym("<") | sym(">"), additive)
equality       = left(sym("==") | sym("!="), comparison)
logical_and    = left(sym("&&"), equality)
expression.become(left(sym("||"), logical_and))

# ======================================================================
# 4. INSTRUCOES
# ======================================================================

statement = forward_declaration()

# block ::= "{" { statement } "}"
block = sym("{") >> statement.many() << sym("}")

# array_initializer ::= "{" [ expression { "," expression } ] "}"
array_init = sym("{") >> expression.sep_by(sym(",")) << sym("}")

# type IDENTIFIER "[" INTEGER "]" [ "=" array_initializer ]
# | type IDENTIFIER [ "=" expression ]
var_decl_core = alt(
    seq(type_, ident, sym("[") >> int_lit << sym("]"),
        (sym("=") >> array_init).optional()).combine(Array),
    seq(type_, ident, (sym("=") >> expression).optional()).combine(Var),
)

# variable_declaration ::= variable_declaration_core ";"
var_decl = var_decl_core << sym(";")

# assignment ::= IDENTIFIER "[" expression "]" "=" expression
#              | IDENTIFIER "=" expression
assignment = alt(
    seq(ident, sym("[") >> expression << sym("]"),
        sym("=") >> expression).combine(AssignIndex),
    seq(ident, sym("=") >> expression).combine(Assign),
)

# "(" expression ")"
cond = sym("(") >> expression << sym(")")

# if_statement ::= "if" "(" expression ")" statement [ "else" statement ]
if_stmt = seq(kw("if") >> cond, statement,
              (kw("else") >> statement).optional()).combine(If)

# while_statement ::= "while" "(" expression ")" statement
while_stmt = seq(kw("while") >> cond, statement).combine(While)

# for_initializer ::= variable_declaration_core | assignment
for_init = var_decl_core.map(LocalVar) | assignment

# NOTA: a gramatica diz [ expression ], mas os exemplos usam "i = i + 1",
# que e uma atribuicao. Aceitamos as duas coisas.
for_update = assignment | expression.map(ExpStmt)

# for_statement ::= "for" "(" [init] ";" [expression] ";" [update] ")" statement
for_stmt = seq(
    kw("for") >> sym("(") >> for_init.optional() << sym(";"),
    expression.optional() << sym(";"),
    for_update.optional() << sym(")"),
    statement,
).combine(For)

statement.become(alt(
    block.map(Block),
    var_decl.map(LocalVar),
    assignment << sym(";"),
    if_stmt,
    while_stmt,
    for_stmt,
    (kw("return") >> expression.optional() << sym(";")).map(Return),
    (kw("print") >> cond << sym(";")).map(Print),
    (kw("read") >> sym("(") >> ident << sym(")") << sym(";")).map(ReadVar),
    (kw("break") << sym(";")).result(Break()),
    (kw("continue") << sym(";")).result(Continue()),
    (call << sym(";")).map(ExpStmt),
))

# ======================================================================
# 5. PROGRAMA, DECLARACOES E FUNCOES
# ======================================================================

# return_type ::= type | "void"
ret_type = type_ | kw("void")

# parameter_list ::= parameter { "," parameter }
param = seq(type_, ident).map(tuple)
params = param.sep_by(sym(","))

# function_definition ::= return_type IDENTIFIER "(" [ parameter_list ] ")" block
function = seq(ret_type, ident, sym("(") >> params << sym(")"),
               block).combine(Function)

# declaration ::= variable_declaration | function_definition
declaration = function | var_decl.map(GlobalVar)

# program ::= { declaration }
program = spaces >> declaration.many() << eof

# ======================================================================
# 6. CORRER O PARSER
# ======================================================================

def parse_sdvm(src):
    """devolve a AST (lista de declaracoes); da ParseError se houver erro"""
    return program.parse(src)

def mensagem_erro(e):
    """texto do erro com linha e coluna a comecar em 1"""
    linha, coluna = line_info_at(e.stream, e.index)
    esperado = ", ".join(sorted(e.expected))
    return "linha " + str(linha + 1) + ", coluna " + str(coluna + 1) + ": esperava " + esperado

def parse_ficheiro(nome):
    """mostra a AST de um ficheiro, uma declaracao por linha"""
    with open(nome, encoding="utf-8") as f:
        src = f.read()
    try:
        for d in parse_sdvm(src):
            print(d)
    except ParseError as e:
        print("Erro de sintaxe na " + mensagem_erro(e))

def testar(nome):
    """escreve OK ou ERRO para um ficheiro"""
    with open(nome, encoding="utf-8") as f:
        src = f.read()
    try:
        parse_sdvm(src)
        print("OK     " + nome)
    except ParseError as e:
        print("ERRO   " + nome + "   (" + mensagem_erro(e) + ")")

if __name__ == "__main__":
    argumentos = sys.argv[1:]
    if argumentos and argumentos[0] == "--ast":
        for nome in argumentos[1:]:
            print("==== " + nome)
            parse_ficheiro(nome)
    else:
        for nome in argumentos:
            testar(nome)
