"""
sdvm: parser, pretty printer, interpretador, detecao de smells e refactoring
para a SDVM-Lang (Manutencao e Evolucao de Software, 2026/2027).

    parser.py    texto -> AST (parsy)
    pretty.py    AST -> texto
    interp.py    interpretador (para testar que o refactoring nao muda o comportamento)
    analise.py   analises com estrategias TU (tipos, pureza, nomes usados, ...)
    smells.py    catalogo de smells + detecao
    refactor.py  eliminacao de smells (estrategia TP innermost)
    __main__.py  linha de comandos:  python -m sdvm ...
"""
