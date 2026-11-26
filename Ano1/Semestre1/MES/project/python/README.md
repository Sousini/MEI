# SDVM-Lang em Python: parser, smells e refactoring

## Instalar

É preciso **Python 3.12 ou mais recente** (o pyZtrategic usa a sintaxe de genéricos do 3.12).

```
cd python
python --version
python -m pip install -r requirements.txt
```

O `python -m pip` garante que o parsy fica instalado no mesmo Python que corre o projeto.
O pyZtrategic já está incluído em `pyztrategic/`.

## Comandos

Todos se correm a partir desta pasta (`python/`):

| Comando | O que faz |
|---|---|
| `python -m sdvm parse ../programas/exemplos/*` | OK / ERRO de sintaxe para cada programa |
| `python -m sdvm ast ../programas/exemplos/factorial` | mostra a AST |
| `python -m sdvm pretty ../programas/exemplos/factorial` | reescreve o programa a partir da AST |
| `python -m sdvm run ../programas/exemplos/leap_year 2000` | corre o programa (os números no fim são os inputs dos `read()`) |
| `python -m sdvm catalogo` | catálogo de smells (A = automático, D = só deteção) |
| `python -m sdvm smells ../programas/smells/*` | lista os smells de cada programa |
| `python -m sdvm refactor ../programas/smells/codigo_morto` | programa refatorado + smells antes/depois |
| `python -m sdvm refactor PROG -o novo.sdvm` | grava o programa refatorado num ficheiro |
| `python -m sdvm refactor PROG --so S01,S02` | só aplica os refactorings indicados |
| `python tests/test_parser.py` | testes do parser e do pretty printer |
| `python tests/test_smells.py` | testes dos smells e do refactoring (~1 min) |
| `python -m pytest tests` | todos os testes (se tiverem o pytest) |

Exemplo:

```
$ python -m sdvm refactor ../programas/smells/codigo_morto -o novo.sdvm
antes:          25 smells: S03 x3, S07 x2, S08 x2, S09 x1, S12 x2, S13 x1, S14 x1, S15 x1, S16 x3, S17 x1, S20 x3, S22 x1, S23 x4
refactorings:   S03 x3, S07 x2, S08 x2, S09 x1, S12 x2, S13 x1, S14 x5, S15 x1, S16 x3
depois:         5 smells: S20 x2, S22 x1, S23 x2
```

## O pacote `sdvm/`

| Módulo | O que faz |
|---|---|
| `parser.py` | parser (parsy) e AST |
| `pretty.py` | pretty printer: AST -> código (round-trip com o parser) |
| `interp.py` | interpretador, usado para verificar que o refactoring não muda o comportamento |
| `analise.py` | análises com estratégias TU: tipos, pureza, nomes usados, chamadas, ... |
| `smells.py` | **catálogo** + regras dos smells + **deteção** (estratégias TU) |
| `refactor.py` | **refactoring** (estratégia TP `innermost` até ao ponto fixo) |
| `__main__.py` | linha de comandos (`python -m sdvm ...`) |

O catálogo completo, com exemplos antes/depois, está em [`../docs/CATALOGO_SMELLS.md`](../docs/CATALOGO_SMELLS.md).

## Programação estratégica usada

- **Deteção** (`smells.detecta_regras`): `st.full_tdTU(step, obj(decl))` com
  `step = adhocTU(failTU, em_no)`: em cada nó testa todas as regras e devolve a lista de smells.
- **Refactoring** (`refactor.refatora_decl`): `st.innermost(step, obj(decl))` com
  `step = adhocTP(failTP, g)`: `g` aplica a primeira regra que serve ou falha
  (`StrategicError`); o `innermost` repete até nenhuma regra se aplicar.
- **Análises** (`analise.recolhe`): `full_tdTU` genérico para recolher chamadas,
  nomes usados, declarações, literais, condições, ...

Nota: o `adhocTP`/`adhocTU` do pyZtrategic apanham `AttributeError`, `TypeError` e
`ValueError` e tratam-nos como "não se aplica", o que esconde erros nas regras.
Por isso as nossas funções são embrulhadas por `protege`, que transforma esses erros
em `ErroInterno`.

## Limitações conhecidas

- Os comentários do programa original perdem-se no programa refatorado (o parser não os guarda).
- O pretty printer põe chavetas num `if` sem `else` que esteja dentro de um `if` com `else`
  (para evitar o *dangling else*).
