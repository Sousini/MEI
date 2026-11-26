# Projeto MES: SDVM-Lang

Projeto em grupo de Manutenção e Evolução de Software (2026/2027), sobre a linguagem
[SDVM-Lang](https://github.com/sooraia/SDVM-lang).

## Estrutura

```
project/
├── README.md               este ficheiro
├── programas/              programas SDVM (partilhados pelo Haskell e pelo Python)
│   ├── exemplos/           os 15 exemplos da linguagem
│   ├── parser/             testes do parser: extra_ok (casos difíceis) + 3 erro_*
│   └── smells/             programas cheios de smells: booleanos, codigo_morto, estrutura
├── haskell/                parser em Haskell (1.ª entrega)
│   ├── README.md
│   └── SDVMParser.hs
├── python/                 parser + smells + refactoring em Python
│   ├── README.md
│   ├── requirements.txt    dependências (parsy)
│   ├── sdvm/               o nosso código (pacote Python)
│   │   ├── __main__.py     linha de comandos: python -m sdvm ...
│   │   ├── parser.py       texto -> AST
│   │   ├── pretty.py       AST -> texto
│   │   ├── interp.py       interpretador (para testar os refactorings)
│   │   ├── analise.py      análises com estratégias TU
│   │   ├── smells.py       catálogo de smells + deteção
│   │   └── refactor.py     eliminação de smells (estratégia TP)
│   ├── pyztrategic/        biblioteca das aulas (zippers + estratégias)
│   └── tests/              test_parser.py, test_smells.py
└── docs/
    ├── CATALOGO_SMELLS.md  catálogo de smells e refactorings, com exemplos
    └── Guia_Projeto_SDVM.pdf
```

## Checklist da entrega (14/12)

- [x] parser + AST (`haskell/`, `python/sdvm/parser.py`)
- [x] deteção de smells: catálogo de maus cheiros e seus refactorings (`docs/CATALOGO_SMELLS.md`, `python/sdvm/smells.py`)
- [x] refactoring / eliminação de smells (`python/sdvm/refactor.py`)
- [ ] injeção (aleatória) de smells em programas (`once_randomTP`)
- [ ] cálculo de Technical Debt (TD)
- [ ] métricas: LOCs, ifs, complexidade ciclomática, n.º de smells, TD, ...

## Começar

```
cd python
python -m pip install -r requirements.txt       # Python 3.12 ou mais recente
python -m sdvm smells ../programas/smells/*
python -m sdvm refactor ../programas/smells/codigo_morto
python tests/test_smells.py
```

Mais comandos em [`python/README.md`](python/README.md); a versão Haskell em [`haskell/README.md`](haskell/README.md).
