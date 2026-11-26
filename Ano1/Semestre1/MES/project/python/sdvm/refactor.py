"""
Refactoring / eliminacao de smells da SDVM-Lang (S01-S16).

Usa as mesmas regras que a detecao (smells.REGRAS), agora numa
estrategia Type-Preserving:

    st.innermost(step, obj(decl))

innermost aplica as regras de baixo para cima, repetidamente, ate nenhuma
se aplicar (ponto fixo). Por isso, por exemplo,
    if (x == true) { } else { return !!y; }
fica  if (!x) return y;  (S01, S02 e S10 combinados).

Algumas regras so ficam possiveis depois de outras (ex: remover uma
variavel que so era usada noutra variavel nao usada), por isso o processo
completo repete-se ate o programa nao mudar.
"""

from collections import Counter

from pyztrategic import strategy as st
from pyztrategic.zipper import obj

from .analise import contexto, protege
from .smells import NaoAplica, regras, remove_codigo_morto

MAX_ITERACOES = 50


def refatora_decl(decl, rs, ctx, log):
    """aplica as regras rs a uma declaracao (funcao ou global) com innermost"""
    def g(n):
        for (codigo, regra) in rs:
            try:
                novo, _ = regra(n, ctx)
            except NaoAplica:
                continue
            log[codigo] += 1
            return novo
        raise st.StrategicError        # nenhuma regra se aplica a este no

    passo_g = protege(g)

    def step(z):
        return st.adhocTP(st.failTP, passo_g, z)

    return st.innermost(step, obj(decl)).node()


def refatora(prog, codigos=None):
    """devolve (programa refatorado, Counter codigo -> n. de refactorings)

    codigos: None para todos os refactorings, ou um conjunto como {"S01", "S08"}
    """
    rs = regras(codigos)
    log = Counter()
    for _ in range(MAX_ITERACOES):
        antes = prog
        if codigos is None or "S16" in codigos:
            prog, n = remove_codigo_morto(prog)
            if n:
                log["S16"] += n
        prog = [refatora_decl(d, rs, contexto(prog, d), log) for d in prog]
        if prog == antes:
            break
    return prog, log
