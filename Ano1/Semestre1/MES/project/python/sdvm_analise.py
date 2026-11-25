"""
Funcoes de analise sobre a AST da SDVM-Lang, usadas pela detecao de smells
e pelos refactorings.

Quase tudo e feito com estrategias Type-Unifying (TU) do pyZtrategic:
    st.full_tdTU(step, obj(ast))
percorre a arvore toda e junta (concatena) as listas devolvidas em cada no.
"""

import sys
from dataclasses import dataclass, field

from pyztrategic import strategy as st
from pyztrategic.zipper import obj

from sdvm_parser import (Array, Assign, AssignIndex, Binary, Block, BoolLit,
                         Break, Call, Cast, CharLit, Continue, ExpStmt,
                         FloatLit, For, Function, GlobalVar, Ident, If, Index,
                         IntLit, LocalVar, Print, ReadVar, Return, StringLit,
                         Unary, Var, While)

# as estrategias do pyZtrategic sao recursivas
sys.setrecursionlimit(20000)


class ErroInterno(Exception):
    """Erro num passo de uma estrategia.

    O adhocTP/adhocTU do pyZtrategic apanham AttributeError, TypeError e
    ValueError e tratam-nos como "a funcao nao se aplica a este no", o que
    esconderia erros de programacao nas nossas regras. Por isso convertemos
    esses erros nesta excecao, que o pyZtrategic deixa passar.
    """


def protege(g):
    """embrulha g: deixa passar StrategicError, converte os outros erros"""
    def h(*args):
        try:
            return g(*args)
        except st.StrategicError:
            raise
        except Exception as e:
            raise ErroInterno(repr(e)) from e
    return h


# ======================================================================
# Estrategias TU genericas
# ======================================================================

def recolhe(f, ast):
    """aplica f (no -> lista) a todos os nos de ast (top-down) e junta tudo"""
    g = protege(f)

    def step(z):
        return st.adhocTU(st.failTU, g, z)
    return st.full_tdTU(step, obj(ast))


def recolhe_tipo(tipos, ast):
    """todos os nos de ast que sao instancias de tipos"""
    def f(n):
        return [n] if isinstance(n, tipos) else []
    return recolhe(f, ast)


def tem_chamadas(e):
    return len(recolhe_tipo(Call, e)) > 0


def puro(e):
    """uma expressao e pura se nao chama funcoes (as funcoes podem fazer print/read)"""
    return e is None or not tem_chamadas(e)


def tamanho(ast):
    """numero de nos da AST (expressoes, instrucoes, declaracoes)"""
    return len(recolhe_tipo(NOS, ast))


def nomes_usados(ast):
    """nomes de variaveis referidos (lidos ou escritos) em ast"""
    def f(n):
        if isinstance(n, Ident):
            return [n.name]
        if isinstance(n, (Assign, AssignIndex, ReadVar)):
            return [n.name]
        return []
    return set(recolhe(f, ast))


def funcoes_chamadas(ast):
    """nomes das funcoes chamadas em ast"""
    def f(n):
        if isinstance(n, Call) and isinstance(n.function, Ident):
            return [n.function.name]
        return []
    return set(recolhe(f, ast))


def nomes_escritos(ast):
    """nomes de variaveis que sao alteradas em ast"""
    def f(n):
        if isinstance(n, (Assign, AssignIndex, ReadVar)):
            return [n.name]
        return []
    return recolhe(f, ast)


def declaracoes_locais(f):
    """declaracoes (Var/Array) locais de uma funcao, incluindo as do for"""
    return [d.decl for d in recolhe_tipo(LocalVar, f)]


def conta_instrucoes(ast):
    return len(recolhe_tipo(INSTRUCOES, ast))


INSTRUCOES = (Block, LocalVar, Assign, AssignIndex, If, While, For, Return,
              Print, ReadVar, Break, Continue, ExpStmt)
EXPRESSOES = (IntLit, FloatLit, CharLit, StringLit, BoolLit, Ident, Index,
              Call, Unary, Binary, Cast)
NOS = INSTRUCOES + EXPRESSOES


# ======================================================================
# Tipos
# ======================================================================

NUMERICOS = {"int", "double"}


@dataclass
class Contexto:
    """informacao sobre o sitio onde estamos (uma funcao ou o nivel global)"""
    vars: dict = field(default_factory=dict)       # nome -> tipo (None se ambiguo)
    arrays: dict = field(default_factory=dict)     # nome -> tipo dos elementos
    funcoes: dict = field(default_factory=dict)    # nome -> tipo de retorno
    globais: set = field(default_factory=set)      # nomes das variaveis globais
    usados: set = field(default_factory=set)       # nomes referidos na funcao
    funcao: object = None                          # Function (ou None)


def _junta(tabela, nome, tipo):
    """se o mesmo nome tiver tipos diferentes, o tipo fica desconhecido (None)"""
    if nome in tabela and tabela[nome] != tipo:
        tabela[nome] = None
    else:
        tabela[nome] = tipo


def contexto(prog, decl):
    """contexto para analisar a declaracao decl do programa prog"""
    ctx = Contexto()
    decls = [d.decl for d in prog if isinstance(d, GlobalVar)]
    ctx.globais = {d.name for d in decls}
    ctx.funcoes = {d.name: d.ret_type for d in prog if isinstance(d, Function)}
    if isinstance(decl, Function):
        ctx.funcao = decl
        decls = decls + [Var(t, n, None) for (t, n) in decl.params]
        decls = decls + declaracoes_locais(decl)
        ctx.usados = nomes_usados(decl.body)
    for d in decls:
        if isinstance(d, Array):
            _junta(ctx.arrays, d.name, d.type)
        else:
            _junta(ctx.vars, d.name, d.type)
    # um nome que e escalar num sitio e array noutro: desconhecido
    for nome in set(ctx.vars) & set(ctx.arrays):
        ctx.vars[nome] = None
        ctx.arrays[nome] = None
    return ctx


def promove(t):
    """char e bool passam a int nas operacoes aritmeticas (como em C)"""
    return "int" if t in ("char", "bool") else t


def tipo(e, ctx):
    """tipo de uma expressao, ou None se nao se souber"""
    if isinstance(e, IntLit):
        return "int"
    if isinstance(e, FloatLit):
        return "double"
    if isinstance(e, CharLit):
        return "char"
    if isinstance(e, StringLit):
        return "string"
    if isinstance(e, BoolLit):
        return "bool"
    if isinstance(e, Ident):
        return ctx.vars.get(e.name)
    if isinstance(e, Index):
        if isinstance(e.array, Ident):
            return ctx.arrays.get(e.array.name)
        return None
    if isinstance(e, Call):
        if isinstance(e.function, Ident):
            return ctx.funcoes.get(e.function.name)
        return None
    if isinstance(e, Cast):
        return e.type
    if isinstance(e, Unary):
        if e.op == "!":
            return "bool"
        t = promove(tipo(e.exp, ctx))
        return t if t in NUMERICOS else None
    if isinstance(e, Binary):
        if e.op in ("&&", "||", "==", "!=", "<", "<=", ">", ">="):
            return "bool"
        t1 = promove(tipo(e.left, ctx))
        t2 = promove(tipo(e.right, ctx))
        if t1 not in NUMERICOS or t2 not in NUMERICOS:
            return None
        if e.op == "%":
            return "int"
        return "double" if "double" in (t1, t2) else "int"
    return None


def nega(c, ctx):
    """!c, mas sem criar duplas negacoes desnecessarias"""
    if isinstance(c, Unary) and c.op == "!" and tipo(c.exp, ctx) == "bool":
        return c.exp
    if isinstance(c, BoolLit):
        return BoolLit(not c.value)
    return Unary("!", c)


# ======================================================================
# Instrucoes
# ======================================================================

def unico(s):
    """{ s }  ->  s   (um bloco com uma so instrucao)"""
    while isinstance(s, Block) and len(s.stmts) == 1:
        s = s.stmts[0]
    return s


def vazio(s):
    return isinstance(s, Block) and len(s.stmts) == 0


def termina(s):
    """True se a instrucao nunca passa para a instrucao seguinte
    (acaba sempre com return, break ou continue)"""
    if isinstance(s, (Return, Break, Continue)):
        return True
    if isinstance(s, Block):
        return any(termina(x) for x in s.stmts)
    if isinstance(s, If):
        return s.else_ is not None and termina(s.then) and termina(s.else_)
    return False


def tem_declaracoes(stmts):
    """True se a lista tem declaracoes de variaveis ao nivel de topo"""
    return any(isinstance(s, LocalVar) for s in stmts)


def como_instrucao(s):
    """uma declaracao solta (ex: resultado de tirar um if) fica dentro de um
    bloco, para nao mudar o ambito da variavel"""
    if isinstance(s, LocalVar):
        return Block([s])
    return s


def espalha(s):
    """instrucoes a colocar no lugar de s numa lista de instrucoes"""
    if isinstance(s, Block):
        if tem_declaracoes(s.stmts):
            return [s]
        return list(s.stmts)
    return [como_instrucao(s)]


def profundidade(s):
    """aninhamento maximo de if/while/for dentro de s
    (um 'else if' conta como o mesmo nivel do if)"""
    if isinstance(s, list):
        return max((profundidade(x) for x in s), default=0)
    if isinstance(s, Block):
        return profundidade(s.stmts)
    if isinstance(s, If):
        p = 1 + profundidade(s.then)
        if s.else_ is not None:
            extra = 0 if isinstance(s.else_, If) else 1
            p = max(p, extra + profundidade(s.else_))
        return p
    if isinstance(s, (While, For)):
        return 1 + profundidade(s.body)
    return 0
