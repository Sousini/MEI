"""
Linha de comandos da SDVM-Lang. Correr a partir da pasta python/:

    python -m sdvm parse    PROGRAMAS...        OK / ERRO de sintaxe para cada programa
    python -m sdvm ast      PROGRAMA            mostra a AST
    python -m sdvm pretty   PROGRAMA            reescreve o programa a partir da AST
    python -m sdvm run      PROGRAMA [INPUTS]   corre o programa (INPUTS = valores dos read())
    python -m sdvm catalogo                     catalogo de smells
    python -m sdvm smells   PROGRAMAS...        lista os smells de cada programa
    python -m sdvm refactor PROGRAMA [-o SAIDA] [--so S01,S08,...]
                                                elimina os smells S01-S16

Exemplo:
    python -m sdvm refactor ../programas/smells/codigo_morto
"""

import sys

from parsy import ParseError

from .interp import executa
from .parser import mensagem_erro, parse_ficheiro, parse_sdvm, testar
from .pretty import pretty
from .refactor import refatora
from .smells import CATALOGO, detecta, resumo


def le(nome):
    with open(nome, encoding="utf-8") as f:
        src = f.read()
    try:
        return parse_sdvm(src)
    except ParseError as e:
        sys.exit("Erro de sintaxe em " + nome + ", " + mensagem_erro(e))


def linha_resumo(smells):
    r = resumo(smells)
    if not r:
        return "sem smells"
    return "%d smells: " % len(smells) + ", ".join("%s x%d" % (c, n) for (c, n) in sorted(r.items()))


# ----------------------------------------------------------------------
# parser / interpretador
# ----------------------------------------------------------------------

def cmd_parse(ficheiros):
    for nome in ficheiros:
        testar(nome)


def cmd_ast(ficheiros):
    for nome in ficheiros:
        print("==== " + nome)
        parse_ficheiro(nome)


def cmd_pretty(ficheiros):
    for nome in ficheiros:
        print(pretty(le(nome)), end="")


def cmd_run(args):
    if not args:
        sys.exit("uso: python -m sdvm run PROGRAMA [INPUTS...]")
    saida, r = executa(le(args[0]), [int(x) for x in args[1:]])
    print("\n".join(saida))
    print("-- main devolveu", r)


# ----------------------------------------------------------------------
# smells
# ----------------------------------------------------------------------

def cmd_catalogo(_):
    print("Catalogo de smells (A = refactoring automatico, D = so detecao)\n")
    for info in CATALOGO.values():
        print("%s [%s] %s" % (info.codigo, "A" if info.automatico else "D", info.nome))
        print("      smell:       " + info.descricao)
        print("      refactoring: " + info.refactoring)


def cmd_smells(ficheiros):
    for nome in ficheiros:
        smells = detecta(le(nome))
        print("==== %s  (%s)" % (nome, linha_resumo(smells)))
        for s in smells:
            print("  " + str(s))
        print()


def cmd_refactor(args):
    saida, so = None, None
    ficheiros = []
    i = 0
    while i < len(args):
        if args[i] == "-o":
            saida = args[i + 1]
            i += 2
        elif args[i] == "--so":
            so = set(args[i + 1].split(","))
            i += 2
        else:
            ficheiros.append(args[i])
            i += 1
    if len(ficheiros) != 1:
        sys.exit("uso: python -m sdvm refactor PROGRAMA [-o SAIDA] [--so S01,S08,...]")

    ast = le(ficheiros[0])
    antes = detecta(ast)
    novo, log = refatora(ast, so)
    depois = detecta(novo)
    texto = pretty(novo)

    if saida:
        with open(saida, "w", encoding="utf-8") as f:
            f.write(texto)
    else:
        print(texto)

    info = sys.stderr if not saida else sys.stdout
    print("antes:          " + linha_resumo(antes), file=info)
    print("refactorings:   " + (", ".join("%s x%d" % (c, n) for (c, n) in sorted(log.items())) or "nenhum"), file=info)
    print("depois:         " + linha_resumo(depois), file=info)
    if saida:
        print("programa refatorado escrito em " + saida)


COMANDOS = {
    "parse": cmd_parse,
    "ast": cmd_ast,
    "pretty": cmd_pretty,
    "run": cmd_run,
    "catalogo": cmd_catalogo,
    "smells": cmd_smells,
    "refactor": cmd_refactor,
}


def main(argv):
    if not argv or argv[0] not in COMANDOS:
        print(__doc__)
        return
    COMANDOS[argv[0]](argv[1:])


if __name__ == "__main__":
    main(sys.argv[1:])
