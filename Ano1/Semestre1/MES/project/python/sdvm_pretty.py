"""
Pretty printer da SDVM-Lang: escreve o programa a partir da AST.

So poe parenteses quando a prioridade dos operadores o exige, por isso
parse(pretty(ast)) == ast  (round-trip).

NOTA: os comentarios do programa original perdem-se (o parser nao os guarda).

Uso:
    from sdvm_pretty import pretty
    print(pretty(ast))
"""

from sdvm_parser import (Array, Assign, AssignIndex, Binary, Block, BoolLit,
                         Break, Call, Cast, CharLit, Continue, ExpStmt,
                         FloatLit, For, Function, GlobalVar, Ident, If, Index,
                         IntLit, LocalVar, Print, ReadVar, Return, StringLit,
                         Unary, Var, While)

INDENT = "    "

# prioridade dos operadores binarios (maior = liga mais)
PRIORIDADE = {
    "||": 1,
    "&&": 2,
    "==": 3, "!=": 3,
    "<": 4, "<=": 4, ">": 4, ">=": 4,
    "+": 5, "-": 5,
    "*": 6, "/": 6, "%": 6,
}
PRIO_UNARIO = 7
PRIO_POSFIXO = 8
PRIO_PRIMARIO = 9


# ======================================================================
# Expressoes
# ======================================================================

def prioridade(e):
    if isinstance(e, Binary):
        return PRIORIDADE[e.op]
    if isinstance(e, (Unary, Cast)):
        return PRIO_UNARIO
    if isinstance(e, (Index, Call)):
        return PRIO_POSFIXO
    return PRIO_PRIMARIO


def entre_parenteses(e, minimo):
    """escreve e; poe parenteses se a prioridade de e for menor que minimo"""
    s = exp_str(e)
    if prioridade(e) < minimo:
        return "(" + s + ")"
    return s


def exp_str(e):
    if isinstance(e, IntLit):
        return str(e.value)
    if isinstance(e, (FloatLit, CharLit, StringLit)):
        return e.value
    if isinstance(e, BoolLit):
        return "true" if e.value else "false"
    if isinstance(e, Ident):
        return e.name
    if isinstance(e, Index):
        return entre_parenteses(e.array, PRIO_PRIMARIO) + "[" + exp_str(e.index) + "]"
    if isinstance(e, Call):
        args = ", ".join(exp_str(a) for a in e.args)
        return entre_parenteses(e.function, PRIO_PRIMARIO) + "(" + args + ")"
    if isinstance(e, Unary):
        operando = entre_parenteses(e.exp, PRIO_UNARIO)
        # "- -x" e "+ +x": o espaco evita confusao na leitura
        if operando.startswith(("-", "+")):
            return e.op + " " + operando
        return e.op + operando
    if isinstance(e, Cast):
        return "(" + e.type + ") " + entre_parenteses(e.exp, PRIO_UNARIO)
    if isinstance(e, Binary):
        p = PRIORIDADE[e.op]
        # associativo a esquerda: o lado direito precisa de prioridade maior
        return (entre_parenteses(e.left, p) + " " + e.op + " "
                + entre_parenteses(e.right, p + 1))
    raise ValueError("expressao desconhecida: " + repr(e))


# ======================================================================
# Declaracoes e instrucoes
# ======================================================================

def decl_str(d):
    """declaracao sem o ';' final (para poder ser usada no for)"""
    if isinstance(d, Var):
        s = d.type + " " + d.name
        if d.init is not None:
            s += " = " + exp_str(d.init)
        return s
    if isinstance(d, Array):
        s = d.type + " " + d.name + "[" + str(d.size) + "]"
        if d.init is not None:
            s += " = {" + ", ".join(exp_str(x) for x in d.init) + "}"
        return s
    raise ValueError("declaracao desconhecida: " + repr(d))


def simples_str(s):
    """instrucoes que cabem numa linha, sem o ';' (usadas tambem no for)"""
    if isinstance(s, LocalVar):
        return decl_str(s.decl)
    if isinstance(s, Assign):
        return s.name + " = " + exp_str(s.exp)
    if isinstance(s, AssignIndex):
        return s.name + "[" + exp_str(s.index) + "] = " + exp_str(s.exp)
    if isinstance(s, ExpStmt):
        return exp_str(s.exp)
    raise ValueError("instrucao desconhecida: " + repr(s))


def bloco_linhas(stmts, nivel):
    linhas = ["{"]
    for s in stmts:
        linhas += stmt_linhas(s, nivel + 1)
    linhas.append(INDENT * nivel + "}")
    return linhas


def corpo(s, nivel, cabecalho):
    """cabecalho + corpo de if/while/for; o bloco abre na mesma linha"""
    if isinstance(s, Block):
        linhas = bloco_linhas(s.stmts, nivel)
        linhas[0] = INDENT * nivel + cabecalho + " " + linhas[0]
        return linhas
    return [INDENT * nivel + cabecalho] + stmt_linhas(s, nivel + 1)


def stmt_linhas(s, nivel):
    ind = INDENT * nivel
    if isinstance(s, Block):
        linhas = bloco_linhas(s.stmts, nivel)
        linhas[0] = ind + linhas[0]
        return linhas
    if isinstance(s, (LocalVar, Assign, AssignIndex, ExpStmt)):
        return [ind + simples_str(s) + ";"]
    if isinstance(s, Return):
        if s.exp is None:
            return [ind + "return;"]
        return [ind + "return " + exp_str(s.exp) + ";"]
    if isinstance(s, Print):
        return [ind + "print(" + exp_str(s.exp) + ");"]
    if isinstance(s, ReadVar):
        return [ind + "read(" + s.name + ");"]
    if isinstance(s, Break):
        return [ind + "break;"]
    if isinstance(s, Continue):
        return [ind + "continue;"]
    if isinstance(s, While):
        return corpo(s.body, nivel, "while (" + exp_str(s.cond) + ")")
    if isinstance(s, For):
        init = "" if s.init is None else simples_str(s.init)
        cond = "" if s.cond is None else exp_str(s.cond)
        upd = "" if s.update is None else simples_str(s.update)
        cab = "for (" + init + ";" + (" " + cond if cond else "") + ";" + (" " + upd if upd else "") + ")"
        return corpo(s.body, nivel, cab)
    if isinstance(s, If):
        return if_linhas(s, nivel, "if (" + exp_str(s.cond) + ")")
    raise ValueError("instrucao desconhecida: " + repr(s))


def if_linhas(s, nivel, cabecalho):
    then = s.then
    # dangling else: se o ramo then for um if/while/for sem chavetas e houver
    # else, pomos chavetas para o else nao ficar agarrado ao if de dentro
    if s.else_ is not None and isinstance(then, (If, While, For)):
        then = Block([then])
    linhas = corpo(then, nivel, cabecalho)
    if s.else_ is None:
        return linhas
    ind = INDENT * nivel
    els = s.else_
    if isinstance(then, Block):
        linhas[-1] += " else"           # "} else ..."
        prefixo = linhas.pop() + " "
    else:
        prefixo = ind + "else "
    if isinstance(els, If):
        resto = if_linhas(els, nivel, "if (" + exp_str(els.cond) + ")")
    else:
        resto = corpo(els, nivel, "")
    resto[0] = prefixo + resto[0].lstrip()
    if resto[0].endswith(" "):
        resto[0] = resto[0].rstrip()
    return linhas + resto


# ======================================================================
# Programa
# ======================================================================

def funcao_linhas(f):
    params = ", ".join(t + " " + n for (t, n) in f.params)
    linhas = bloco_linhas(f.body, 0)
    linhas[0] = f.ret_type + " " + f.name + "(" + params + ") " + linhas[0]
    return linhas


def pretty(prog):
    """programa (lista de GlobalVar / Function) -> texto"""
    partes = []
    anterior = None
    for d in prog:
        if isinstance(d, GlobalVar):
            if isinstance(anterior, Function):
                partes.append("")
            partes.append(decl_str(d.decl) + ";")
        elif isinstance(d, Function):
            if anterior is not None:
                partes.append("")
            partes += funcao_linhas(d)
        else:
            raise ValueError("declaracao desconhecida: " + repr(d))
        anterior = d
    return "\n".join(partes) + "\n"


def pretty_no(n):
    """escreve qualquer no (expressao, instrucao, funcao) - util nas mensagens"""
    if isinstance(n, Function):
        return "\n".join(funcao_linhas(n))
    if isinstance(n, GlobalVar):
        return decl_str(n.decl) + ";"
    if isinstance(n, list):
        return "\n".join("\n".join(stmt_linhas(s, 0)) for s in n)
    try:
        return exp_str(n)
    except ValueError:
        return "\n".join(stmt_linhas(n, 0))
