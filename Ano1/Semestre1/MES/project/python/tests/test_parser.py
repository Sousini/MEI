"""
Testes do parser e do pretty printer.

Correr (a partir da pasta python/):
    python tests/test_parser.py        (ou: python -m pytest tests)

  1. os programas de programas/exemplos, programas/smells e programas/parser/extra_ok
     sao aceites;
  2. os programas programas/parser/erro_* dao erro de sintaxe;
  3. round-trip: parse(pretty(ast)) == ast.
"""

import sys
from pathlib import Path

PYTHON = Path(__file__).resolve().parent.parent
PROGRAMAS = PYTHON.parent / "programas"
sys.path.insert(0, str(PYTHON))

from parsy import ParseError             # noqa: E402

from sdvm.parser import parse_sdvm       # noqa: E402
from sdvm.pretty import pretty           # noqa: E402

VALIDOS = (sorted((PROGRAMAS / "exemplos").iterdir()) + sorted((PROGRAMAS / "smells").iterdir())
           + [PROGRAMAS / "parser" / "extra_ok"])
ERROS = sorted((PROGRAMAS / "parser").glob("erro_*"))


def test_programas_validos_e_round_trip():
    assert len(VALIDOS) >= 19
    for f in VALIDOS:
        ast = parse_sdvm(f.read_text(encoding="utf-8"))
        texto = pretty(ast)
        assert parse_sdvm(texto) == ast, f.name
        assert pretty(parse_sdvm(texto)) == texto, f.name


def test_programas_com_erros():
    assert len(ERROS) == 3
    for f in ERROS:
        try:
            parse_sdvm(f.read_text(encoding="utf-8"))
        except ParseError:
            continue
        raise AssertionError("devia dar erro: " + f.name)


if __name__ == "__main__":
    falhas = 0
    for nome, f in sorted(globals().items()):
        if nome.startswith("test_") and callable(f):
            try:
                f()
                print("OK     " + nome)
            except AssertionError as e:
                falhas += 1
                print("FALHOU " + nome + "\n" + str(e))
    sys.exit(1 if falhas else 0)
