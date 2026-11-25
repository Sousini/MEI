"""
Catalogo de code smells da SDVM-Lang e sua detecao.

Cada smell tem um codigo (S01, S02, ...). Ha dois grupos:

  * S01-S16: smells com refactoring automatico. Cada um e uma REGRA:
        regra(no, ctx) -> (no_novo, excerto)
    ou levanta NaoAplica se o smell nao estiver naquele no.
    A MESMA regra serve para detetar (estrategia TU: em que nos a regra se
    aplica?) e para refatorar (estrategia TP: trocar o no pelo no_novo).
    Assim, tudo o que e detetado e eliminado pelo refactoring.

  * S17-S25: smells so detetados (o refactoring precisa de decisoes de
    desenho - nomes, partir funcoes, ... - e fica para o programador).

Ver CATALOGO_SMELLS.md para a descricao completa com exemplos.
"""

from collections import Counter, defaultdict
from dataclasses import dataclass, replace

from pyztrategic import strategy as st

from sdvm_analise import (NUMERICOS, como_instrucao, conta_instrucoes,
                          contexto, espalha, funcoes_chamadas, nega,
                          nomes_escritos, nomes_usados, profundidade,
                          puro, recolhe, recolhe_tipo, tamanho,
                          tem_declaracoes, termina, tipo, unico, vazio)
from sdvm_parser import (Array, Assign, AssignIndex, Binary, Block, BoolLit,
                         Call, Cast, ExpStmt, FloatLit, For, Function,
                         GlobalVar, Ident, If, Index, IntLit, LocalVar,
                         Return, Unary, While)
from sdvm_pretty import pretty_no

# ----------------------------------------------------------------------
# limites usados nos smells so detetados (podem ser ajustados)
# ----------------------------------------------------------------------
LIMITE_INSTRUCOES = 20          # S17 funcao longa
LIMITE_PARAMETROS = 4           # S18 lista de parametros longa
LIMITE_ANINHAMENTO = 3          # S19 aninhamento profundo
NUMEROS_NORMAIS = {0, 1, 2}     # S20 numeros que nao sao "magicos"
LIMITE_DUPLICADO = 12           # S21 tamanho minimo (n. de nos) do codigo duplicado
NOMES_CURTOS_OK = {"i", "j", "k"}   # S23 contadores de ciclos
LIMITE_OPERADORES_LOGICOS = 3   # S25 condicao complexa (n. de && e ||)


class NaoAplica(st.StrategicError):
    """a regra nao se aplica a este no"""


# ======================================================================
# Catalogo
# ======================================================================

@dataclass
class InfoSmell:
    codigo: str
    nome: str
    descricao: str
    refactoring: str
    automatico: bool


CATALOGO = {s.codigo: s for s in [
    InfoSmell("S01", "Comparacao redundante com booleano",
              "comparar uma expressao booleana com true/false (b == true)",
              "Simplificar: b == true -> b ; b == false -> !b", True),
    InfoSmell("S02", "Operador unario redundante",
              "dupla negacao (!!b, - -x) ou + unario",
              "Remover os operadores: !!b -> b ; - -x -> x ; +x -> x", True),
    InfoSmell("S03", "Operacao com elemento neutro",
              "x + 0, 0 + x, x - 0, x * 1, 1 * x, x / 1, 0 - x (x numerico)",
              "Remover a operacao: x + 0 -> x ; 0 - x -> -x", True),
    InfoSmell("S04", "Cast redundante",
              "cast para o tipo que a expressao ja tem ((int) n, com n int)",
              "Remover o cast", True),
    InfoSmell("S05", "If que devolve um booleano",
              "if (c) return true; else return false;",
              "Devolver a condicao: return c;", True),
    InfoSmell("S06", "If que atribui um booleano",
              "if (c) x = true; else x = false;",
              "Atribuir a condicao: x = c;", True),
    InfoSmell("S07", "Condicao constante",
              "if (true) / if (false) / while (false): ha codigo que nunca corre",
              "Ficar so com o ramo que corre (remove codigo morto)", True),
    InfoSmell("S08", "Codigo inalcancavel",
              "instrucoes depois de return, break ou continue",
              "Remover as instrucoes que nunca correm", True),
    InfoSmell("S09", "Ramos identicos",
              "if (c) S else S: os dois ramos sao iguais",
              "Trocar o if pelo ramo (se c nao tiver efeitos laterais)", True),
    InfoSmell("S10", "Ramo vazio",
              "if (c) {} else S, ou if (c) S else {}",
              "if (!c) S ; remover o else vazio; remover o if vazio", True),
    InfoSmell("S11", "Ifs aninhados que podem ser juntos",
              "if (a) { if (b) S }  (sem else)",
              "Consolidar condicoes: if (a && b) S", True),
    InfoSmell("S12", "Else desnecessario depois de return",
              "if (c) { ... return x; } else { R }",
              "Tirar o else: if (c) { ... return x; } R  (menos aninhamento)", True),
    InfoSmell("S13", "Auto-atribuicao",
              "x = x;  ou  a[i] = a[i];",
              "Remover a instrucao", True),
    InfoSmell("S14", "Bloco vazio ou redundante",
              "{ } solto, ou { ... } sem declaracoes dentro de outro bloco",
              "Remover o bloco vazio / juntar o bloco ao bloco de fora", True),
    InfoSmell("S15", "Variavel local nao usada",
              "variavel declarada e nunca usada",
              "Remover a declaracao (se o valor inicial nao tiver efeitos laterais)", True),
    InfoSmell("S16", "Codigo morto (funcao ou variavel global nao usada)",
              "funcao que nunca e chamada a partir de main, ou global nunca usada",
              "Remover a declaracao", True),
    InfoSmell("S17", "Funcao longa",
              "funcao com mais de %d instrucoes" % LIMITE_INSTRUCOES,
              "Extract Function: partir em funcoes mais pequenas", False),
    InfoSmell("S18", "Lista de parametros longa",
              "funcao com %d ou mais parametros" % LIMITE_PARAMETROS,
              "Reduzir parametros (calcular dentro da funcao / partir a funcao)", False),
    InfoSmell("S19", "Aninhamento profundo",
              "mais de %d niveis de if/while/for" % LIMITE_ANINHAMENTO,
              "Guard clauses / Extract Function", False),
    InfoSmell("S20", "Numero magico",
              "literal numerico sem nome (fora de %s)" % sorted(NUMEROS_NORMAIS),
              "Dar nome ao numero (variavel global com nome claro)", False),
    InfoSmell("S21", "Codigo duplicado",
              "o mesmo bloco de codigo (>= %d nos) aparece mais que uma vez" % LIMITE_DUPLICADO,
              "Extract Function e chamar a funcao nos dois sitios", False),
    InfoSmell("S22", "Estado global mutavel",
              "funcao que altera uma variavel global",
              "Passar o valor por parametro / devolver o resultado", False),
    InfoSmell("S23", "Identificador demasiado curto",
              "nome com uma letra (exceto i, j, k)",
              "Rename: dar um nome que diga para que serve", False),
    InfoSmell("S24", "Parametro nao usado",
              "parametro que a funcao nunca usa",
              "Remover o parametro (e os argumentos nas chamadas)", False),
    InfoSmell("S25", "Condicao complexa",
              "condicao com %d ou mais operadores && / ||" % LIMITE_OPERADORES_LOGICOS,
              "Decompose Conditional: guardar partes em variaveis bool com nome", False),
]}


@dataclass
class Smell:
    """um smell encontrado num programa"""
    codigo: str
    onde: str           # nome da funcao, ou "global"
    detalhe: str        # excerto de codigo / explicacao

    @property
    def info(self):
        return CATALOGO[self.codigo]

    def __str__(self):
        det = self.detalhe.replace("\n", "\n" + " " * 8)
        return "[%s] %s (%s)\n        %s" % (self.codigo, self.info.nome, self.onde, det)


# ======================================================================
# Regras S01-S14: ao nivel de um no (expressao ou instrucao)
# ======================================================================

def s01_comparacao_booleana(n, ctx):
    if isinstance(n, Binary) and n.op in ("==", "!="):
        for (lit, x) in ((n.right, n.left), (n.left, n.right)):
            if isinstance(lit, BoolLit) and tipo(x, ctx) == "bool":
                igual = (n.op == "==") == lit.value
                return (x if igual else nega(x, ctx)), n
    raise NaoAplica


def s02_unario_redundante(n, ctx):
    if isinstance(n, Unary):
        x = n.exp
        if n.op == "!" and isinstance(x, Unary) and x.op == "!" and tipo(x.exp, ctx) == "bool":
            return x.exp, n
        if n.op == "-" and isinstance(x, Unary) and x.op == "-" and tipo(x.exp, ctx) in NUMERICOS:
            return x.exp, n
        if n.op == "+" and tipo(x, ctx) in NUMERICOS:
            return x, n
    raise NaoAplica


def _e_int(e, v):
    return isinstance(e, IntLit) and e.value == v


def _e_neutro(e, v, x, ctx):
    """e e o literal v (0 ou 1)? aceita 0.0 / 1.0 se x for double"""
    if _e_int(e, v):
        return True
    return (isinstance(e, FloatLit) and float(e.value) == v
            and tipo(x, ctx) == "double")


def s03_elemento_neutro(n, ctx):
    if isinstance(n, Binary):
        a, b = n.left, n.right
        # NOTA: com double, x + 0 e 0 - x nao sao iguais a x / -x quando
        # x = -0.0 (o sinal do zero muda), por isso essas so se aplicam a int
        if tipo(a, ctx) in NUMERICOS:
            if n.op == "+" and _e_int(b, 0) and tipo(a, ctx) == "int":
                return a, n
            if n.op == "-" and _e_neutro(b, 0, a, ctx):
                return a, n
            if n.op in ("*", "/") and _e_neutro(b, 1, a, ctx):
                return a, n
        if tipo(b, ctx) in NUMERICOS:
            if n.op == "+" and _e_int(a, 0) and tipo(b, ctx) == "int":
                return b, n
            if n.op == "*" and _e_neutro(a, 1, b, ctx):
                return b, n
            if n.op == "-" and _e_int(a, 0) and tipo(b, ctx) == "int":
                return Unary("-", b), n
    raise NaoAplica


def s04_cast_redundante(n, ctx):
    if isinstance(n, Cast) and tipo(n.exp, ctx) == n.type:
        return n.exp, n
    raise NaoAplica


def _retorno_bool(s):
    s = unico(s)
    if isinstance(s, Return) and isinstance(s.exp, BoolLit):
        return s.exp.value
    return None


def s05_if_devolve_booleano(n, ctx):
    # forma 1:  if (c) return true; else return false;
    if isinstance(n, If) and n.else_ is not None and tipo(n.cond, ctx) == "bool":
        v1, v2 = _retorno_bool(n.then), _retorno_bool(n.else_)
        if v1 is not None and v2 is not None and v1 != v2:
            return Return(n.cond if v1 else nega(n.cond, ctx)), n
    # forma 2 (numa lista):  if (c) return true; return false;
    return em_lista(_s05_lista, n, ctx)


def _s05_lista(stmts, ctx):
    for i in range(len(stmts) - 1):
        s, seguinte = stmts[i], stmts[i + 1]
        if isinstance(s, If) and s.else_ is None and tipo(s.cond, ctx) == "bool":
            v1, v2 = _retorno_bool(s.then), _retorno_bool(seguinte)
            if v1 is not None and v2 is not None and v1 != v2:
                r = Return(s.cond if v1 else nega(s.cond, ctx))
                return stmts[:i] + [r] + stmts[i + 2:], [s, seguinte]
    raise NaoAplica


def s06_if_atribui_booleano(n, ctx):
    if isinstance(n, If) and n.else_ is not None and tipo(n.cond, ctx) == "bool":
        a, b = unico(n.then), unico(n.else_)
        if (isinstance(a, Assign) and isinstance(b, Assign) and a.name == b.name
                and isinstance(a.exp, BoolLit) and isinstance(b.exp, BoolLit)
                and a.exp.value != b.exp.value):
            return Assign(a.name, n.cond if a.exp.value else nega(n.cond, ctx)), n
    raise NaoAplica


def s07_condicao_constante(n, ctx):
    if isinstance(n, If) and isinstance(n.cond, BoolLit):
        if n.cond.value:
            return como_instrucao(n.then), n
        return (Block([]) if n.else_ is None else como_instrucao(n.else_)), n
    if isinstance(n, While) and n.cond == BoolLit(False):
        return Block([]), n
    raise NaoAplica


def _s08_lista(stmts, ctx):
    for i, s in enumerate(stmts[:-1]):
        if termina(s):
            return stmts[:i + 1], stmts[i + 1:]
    raise NaoAplica


def s08_codigo_inalcancavel(n, ctx):
    return em_lista(_s08_lista, n, ctx)


def s09_ramos_identicos(n, ctx):
    if (isinstance(n, If) and n.else_ is not None and unico(n.then) == unico(n.else_)
            and puro(n.cond)):
        return como_instrucao(n.then), n
    raise NaoAplica


def s10_ramo_vazio(n, ctx):
    if isinstance(n, If):
        if n.else_ is not None and vazio(n.else_):
            return If(n.cond, n.then, None), n
        if vazio(n.then) and n.else_ is not None:
            return If(nega(n.cond, ctx), n.else_, None), n
        if vazio(n.then) and n.else_ is None:
            if puro(n.cond):
                return Block([]), n
            if isinstance(n.cond, Call):
                return ExpStmt(n.cond), n
    raise NaoAplica


def s11_ifs_aninhados(n, ctx):
    if isinstance(n, If) and n.else_ is None:
        dentro = unico(n.then)
        if isinstance(dentro, If) and dentro.else_ is None:
            return If(Binary("&&", n.cond, dentro.cond), dentro.then, None), n
    raise NaoAplica


def _s12_lista(stmts, ctx):
    for i, s in enumerate(stmts):
        if isinstance(s, If) and s.else_ is not None and termina(s.then):
            novo = [If(s.cond, s.then, None)] + espalha(s.else_)
            return stmts[:i] + novo + stmts[i + 1:], s
    raise NaoAplica


def s12_else_apos_return(n, ctx):
    return em_lista(_s12_lista, n, ctx)


def _auto_atribuicao(s):
    if isinstance(s, Assign):
        return s.exp == Ident(s.name)
    if isinstance(s, AssignIndex):
        return s.exp == Index(Ident(s.name), s.index) and puro(s.index)
    return False


def _s13_lista(stmts, ctx):
    for i, s in enumerate(stmts):
        if _auto_atribuicao(s):
            return stmts[:i] + stmts[i + 1:], s
    raise NaoAplica


def s13_auto_atribuicao(n, ctx):
    return em_lista(_s13_lista, n, ctx)


def _s14_lista(stmts, ctx):
    for i, s in enumerate(stmts):
        if isinstance(s, Block) and not tem_declaracoes(s.stmts):
            return stmts[:i] + s.stmts + stmts[i + 1:], s
    raise NaoAplica


def s14_bloco_redundante(n, ctx):
    return em_lista(_s14_lista, n, ctx)


def _s15_lista(stmts, ctx):
    for i, s in enumerate(stmts):
        if isinstance(s, LocalVar) and s.decl.name not in ctx.usados:
            d = s.decl
            iniciais = (d.init or []) if isinstance(d, Array) else [d.init]
            if all(puro(e) for e in iniciais):
                return stmts[:i] + stmts[i + 1:], s
    raise NaoAplica


def s15_variavel_nao_usada(n, ctx):
    if ctx.funcao is None:
        raise NaoAplica
    return em_lista(_s15_lista, n, ctx)


def em_lista(f, n, ctx):
    """aplica uma regra sobre listas de instrucoes (f(stmts, ctx)) a um
    no que tem uma lista de instrucoes: um bloco ou o corpo de uma funcao"""
    if isinstance(n, Block):
        novas, excerto = f(n.stmts, ctx)
        return Block(novas), excerto
    if isinstance(n, Function):
        novas, excerto = f(n.body, ctx)
        return replace(n, body=novas), excerto
    raise NaoAplica


# regras aplicadas no a no (a ordem conta: as primeiras tem prioridade)
REGRAS = [
    ("S01", s01_comparacao_booleana),
    ("S02", s02_unario_redundante),
    ("S03", s03_elemento_neutro),
    ("S04", s04_cast_redundante),
    ("S05", s05_if_devolve_booleano),
    ("S06", s06_if_atribui_booleano),
    ("S07", s07_condicao_constante),
    ("S08", s08_codigo_inalcancavel),
    ("S09", s09_ramos_identicos),
    ("S10", s10_ramo_vazio),
    ("S11", s11_ifs_aninhados),
    ("S12", s12_else_apos_return),
    ("S13", s13_auto_atribuicao),
    ("S14", s14_bloco_redundante),
    ("S15", s15_variavel_nao_usada),
]


def regras(codigos=None):
    """as regras a usar (todas, ou so as dos codigos dados)"""
    return [(c, r) for (c, r) in REGRAS if codigos is None or c in codigos]


# ======================================================================
# S16: codigo morto ao nivel do programa
# ======================================================================

def codigo_morto(prog):
    """declaracoes de topo que podem ser removidas: lista de (decl, motivo)

    - funcoes que nao sao alcancaveis a partir de main (grafo de chamadas)
    - variaveis globais que nunca sao usadas (e com valor inicial sem chamadas)
    So se aplica se o programa tiver main.
    """
    funcoes = {d.name: d for d in prog if isinstance(d, Function)}
    if "main" not in funcoes:
        return []
    globais = [d for d in prog if isinstance(d, GlobalVar)]
    # funcoes alcancaveis: a partir de main e dos valores iniciais das globais
    pendentes = ["main"] + sorted(funcoes_chamadas(globais))
    alcancaveis = set()
    while pendentes:
        f = pendentes.pop()
        if f in alcancaveis or f not in funcoes:
            continue
        alcancaveis.add(f)
        pendentes += sorted(funcoes_chamadas(funcoes[f].body))

    mortos = []
    for f in funcoes.values():
        if f.name not in alcancaveis:
            mortos.append((f, "funcao %s nao e chamada a partir de main" % f.name))
    vivas = [f for f in funcoes.values() if f.name in alcancaveis]
    usados = nomes_usados([f.body for f in vivas] + [g.decl for g in globais])
    for g in globais:
        d = g.decl
        iniciais = (d.init or []) if isinstance(d, Array) else [d.init]
        if d.name not in usados and all(puro(e) for e in iniciais):
            mortos.append((g, "variavel global %s nunca e usada" % d.name))
    return mortos


def remove_codigo_morto(prog):
    mortos = codigo_morto(prog)
    ids = {id(d) for (d, _) in mortos}
    return [d for d in prog if id(d) not in ids], len(mortos)


# ======================================================================
# Detecao
# ======================================================================

def onde(decl):
    return decl.name if isinstance(decl, Function) else "global"


def detecta_regras(prog, codigos=None):
    """S01-S15: em que nos se aplica cada regra (estrategia TU full_tdTU)"""
    encontrados = []
    rs = regras(codigos)
    for decl in prog:
        ctx = contexto(prog, decl)

        def em_no(n):
            achados = []
            for (codigo, regra) in rs:
                try:
                    _, excerto = regra(n, ctx)
                    achados.append(Smell(codigo, onde(decl), pretty_no(excerto)))
                except NaoAplica:
                    pass
            return achados
        encontrados += recolhe(em_no, decl)
    return encontrados


def detecta_estruturais(prog):
    """S17-S25: smells que so sao detetados"""
    achados = []
    funcoes = [d for d in prog if isinstance(d, Function)]
    globais = {d.decl.name for d in prog if isinstance(d, GlobalVar)}

    for f in funcoes:
        ctx = contexto(prog, f)
        locais = {n for (_, n) in f.params} | {d.name for d in locais_decls(f)}
        # S17
        n = conta_instrucoes(f.body)
        if n > LIMITE_INSTRUCOES:
            achados.append(Smell("S17", f.name, "%d instrucoes (limite %d)" % (n, LIMITE_INSTRUCOES)))
        # S18
        if len(f.params) >= LIMITE_PARAMETROS:
            achados.append(Smell("S18", f.name, "%d parametros" % len(f.params)))
        # S19
        p = profundidade(f.body)
        if p > LIMITE_ANINHAMENTO:
            achados.append(Smell("S19", f.name, "%d niveis de aninhamento (limite %d)" % (p, LIMITE_ANINHAMENTO)))
        # S20
        contagem = Counter(magicos(f.body))
        for (v, k) in sorted(contagem.items(), key=lambda x: str(x[0])):
            achados.append(Smell("S20", f.name, "%s (aparece %d vez%s)" % (v, k, "es" if k > 1 else "")))
        # S22
        for g in sorted(set(nomes_escritos(f.body))):
            if g in globais and g not in locais:
                achados.append(Smell("S22", f.name, "altera a variavel global %s" % g))
        # S23
        nomes = [n for (_, n) in f.params] + [d.name for d in locais_decls(f)]
        if len(f.name) == 1:
            nomes.append(f.name)
        for nome in sorted(set(nomes)):
            if len(nome) == 1 and nome not in NOMES_CURTOS_OK:
                achados.append(Smell("S23", f.name, "nome '%s'" % nome))
        # S24
        for (_, nome) in f.params:
            if nome not in ctx.usados:
                achados.append(Smell("S24", f.name, "parametro '%s'" % nome))
        # S25
        for c in condicoes(f.body):
            k = len(recolhe(lambda e: [e] if isinstance(e, Binary) and e.op in ("&&", "||") else [], c))
            if k >= LIMITE_OPERADORES_LOGICOS:
                achados.append(Smell("S25", f.name, "%s  (%d operadores logicos)" % (pretty_no(c), k)))

    for g in globais:
        if len(g) == 1 and g not in NOMES_CURTOS_OK:
            achados.append(Smell("S23", "global", "nome '%s'" % g))

    # S21
    achados += duplicados(prog)
    return achados


def locais_decls(f):
    return [x.decl for x in recolhe_tipo(LocalVar, f)]


def magicos(ast):
    def f(n):
        if isinstance(n, IntLit) and n.value not in NUMEROS_NORMAIS:
            return [n.value]
        if isinstance(n, FloatLit) and float(n.value) not in NUMEROS_NORMAIS:
            return [n.value]
        return []
    return recolhe(f, ast)


def condicoes(ast):
    def f(n):
        if isinstance(n, (If, While)):
            return [n.cond]
        if isinstance(n, For) and n.cond is not None:
            return [n.cond]
        return []
    return recolhe(f, ast)


def duplicados(prog):
    """S21: instrucoes compostas iguais (com >= LIMITE_DUPLICADO nos) que
    aparecem mais do que uma vez. So se reporta a maior copia."""
    funcoes = [d for d in prog if isinstance(d, Function)]
    grupos = defaultdict(list)
    for f in funcoes:
        for s in recolhe_tipo((If, While, For, Block), f.body):
            if tamanho(s) >= LIMITE_DUPLICADO:
                grupos[repr(s)].append((f.name, s))
    repetidos = {k: v for (k, v) in grupos.items() if len(v) > 1}
    # tirar os que estao dentro de outro duplicado maior
    maximos = [k for k in repetidos
               if not any(k != o and k in o for o in repetidos)]
    achados = []
    for k in maximos:
        sitios = sorted({nome for (nome, _) in repetidos[k]})
        s = repetidos[k][0][1]
        achados.append(Smell("S21", ", ".join(sitios),
                             "%d copias de:\n%s" % (len(repetidos[k]), pretty_no(s))))
    return achados


def detecta(prog, codigos=None):
    """todos os smells de um programa, ordenados por codigo"""
    achados = detecta_regras(prog, codigos)
    if codigos is None or "S16" in codigos:
        for (d, motivo) in codigo_morto(prog):
            achados.append(Smell("S16", onde(d), motivo))
    if codigos is None:
        achados += detecta_estruturais(prog)
    else:
        achados += [s for s in detecta_estruturais(prog) if s.codigo in codigos]
    return sorted(achados, key=lambda s: s.codigo)


def resumo(smells):
    """Counter codigo -> numero de ocorrencias"""
    return Counter(s.codigo for s in smells)
