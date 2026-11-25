"""
Ferramenta de linha de comandos: detecao e eliminacao de code smells
em programas SDVM-Lang.

    python sdvm_mes.py catalogo
        mostra o catalogo de smells

    python sdvm_mes.py smells programa [programa ...]
        lista os smells de cada programa

    python sdvm_mes.py refactor programa [-o saida] [--so S01,S08,...]
        elimina os smells S01-S16, escreve o programa refatorado
        (no ecra ou no ficheiro saida) e mostra os smells antes/depois
"""

import sys

from parsy import ParseError

from sdvm_parser import mensagem_erro, parse_sdvm
from sdvm_pretty import pretty
from sdvm_refactor import refatora
from sdvm_smells import CATALOGO, detecta, resumo


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


def cmd_catalogo():
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
        sys.exit("uso: python sdvm_mes.py refactor programa [-o saida] [--so S01,S08,...]")

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


def main(argv):
    if not argv or argv[0] not in ("catalogo", "smells", "refactor"):
        print(__doc__)
        return
    if argv[0] == "catalogo":
        cmd_catalogo()
    elif argv[0] == "smells":
        cmd_smells(argv[1:])
    else:
        cmd_refactor(argv[1:])


if __name__ == "__main__":
    main(sys.argv[1:])
