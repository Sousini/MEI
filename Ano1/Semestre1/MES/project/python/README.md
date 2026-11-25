# SDVM-Lang em Python: parser, smells e refactoring

Projeto de Manutenção e Evolução de Software. Esta parte cobre:

- [x] parser + AST (`sdvm_parser.py`)
- [x] deteção de smells: catálogo de maus cheiros e respetivos refactorings ([CATALOGO_SMELLS.md](CATALOGO_SMELLS.md))
- [x] refactoring / eliminação de smells
- [ ] injeção (aleatória) de smells (`once_randomTP`)
- [ ] cálculo de Technical Debt
- [ ] métricas (LOCs, ifs, complexidade ciclomática, nº de smells, TD, ...)

## Instalar

É preciso Python 3.12 ou mais recente (o pyZtrategic usa a sintaxe de genéricos do 3.12)
e a biblioteca `parsy`:

```
pip install parsy
```

A biblioteca de programação estratégica **pyZtrategic** está incluída na pasta `pyztrategic/`.

## Correr

```
python sdvm_mes.py catalogo                              # catálogo de smells
python sdvm_mes.py smells exemplos/* testes_smells/*     # deteção
python sdvm_mes.py refactor testes_smells/codigo_morto   # programa refatorado + smells antes/depois
python sdvm_mes.py refactor testes_smells/booleanos -o novo.sdvm
python sdvm_mes.py refactor testes_smells/booleanos --so S01,S02   # só alguns refactorings

python sdvm_interp.py exemplos/io_and_void 17            # correr um programa (inputs no fim)
python test_smells.py                                    # testes (~1 min)

python sdvm_parser.py exemplos/*                         # parser: OK / ERRO
python sdvm_parser.py --ast exemplos/factorial           # parser: mostra a AST
```

Exemplo:

```
$ python sdvm_mes.py refactor testes_smells/codigo_morto -o novo.sdvm
antes:          25 smells: S03 x3, S07 x2, S08 x2, S09 x1, S12 x2, S13 x1, S14 x1, S15 x1, S16 x3, S17 x1, S20 x3, S22 x1, S23 x4
refactorings:   S03 x3, S07 x2, S08 x2, S09 x1, S12 x2, S13 x1, S14 x5, S15 x1, S16 x3
depois:         5 smells: S20 x2, S22 x1, S23 x2
```

## Ficheiros

| Ficheiro | O que faz |
|---|---|
| `sdvm_parser.py` | parser (parsy) e AST |
| `sdvm_pretty.py` | pretty printer: AST → código (round-trip com o parser) |
| `sdvm_analise.py` | análises com estratégias TU: tipos, pureza, nomes usados, chamadas, ... |
| `sdvm_smells.py` | **catálogo** + regras dos smells + **deteção** (estratégias TU) |
| `sdvm_refactor.py` | **refactoring** (estratégia TP `innermost` até ao ponto fixo) |
| `sdvm_mes.py` | ferramenta de linha de comandos |
| `sdvm_interp.py` | interpretador, usado para verificar que o refactoring não muda o comportamento |
| `test_smells.py` | testes |
| `testes_smells/` | programas com smells (`booleanos`, `codigo_morto`, `estrutura`) |
| `CATALOGO_SMELLS.md` | catálogo de smells e refactorings, com exemplos |
| `pyztrategic/` | biblioteca pyZtrategic (zippers + estratégias) |

## Programação estratégica usada

- **Deteção** (`sdvm_smells.detecta_regras`): `st.full_tdTU(step, obj(decl))` com
  `step = adhocTU(failTU, em_no)`: em cada nó testa todas as regras e devolve a lista de smells.
- **Refactoring** (`sdvm_refactor.refatora_decl`): `st.innermost(step, obj(decl))` com
  `step = adhocTP(failTP, g)`: `g` aplica a primeira regra que serve ou falha
  (`StrategicError`); o `innermost` repete até nenhuma regra se aplicar.
- **Análises** (`sdvm_analise.recolhe`): `full_tdTU` genérico para recolher chamadas,
  nomes usados, declarações, literais, condições, ...

Nota: o `adhocTP`/`adhocTU` do pyZtrategic apanham `AttributeError`, `TypeError` e
`ValueError` e tratam-nos como "não se aplica", o que esconde erros nas regras.
Por isso as nossas funções são embrulhadas por `protege`, que transforma esses erros
em `ErroInterno`.

## Limitações conhecidas

- Os comentários do programa original perdem-se no programa refatorado (o parser não os guarda).
- O pretty printer põe chavetas num `if` sem `else` que esteja dentro de um `if` com `else`
  (para evitar o *dangling else*).
