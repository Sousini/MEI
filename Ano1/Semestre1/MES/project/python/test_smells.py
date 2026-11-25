"""
Testes da detecao e do refactoring de smells.

Correr:
    python test_smells.py          (ou: python -m pytest test_smells.py)

O que se testa:
  1. cada smell do catalogo e detetado num exemplo pequeno, e o refactoring
     produz o codigo esperado;
  2. casos em que o refactoring NAO se deve aplicar (mudaria o comportamento);
  3. nos programas de exemplo: o programa refatorado volta a ser aceite pelo
     parser, ja nao tem smells S01-S16, e faz exatamente o mesmo
     (mesmo output e mesmo valor de retorno - corremos os dois com o
     interpretador sdvm_interp);
  4. teste aleatorio: geramos muitos programas cheios de smells e
     confirmamos que o refactoring nunca muda o comportamento.
"""

import glob
import random
import sys

from sdvm_interp import executa
from sdvm_parser import parse_sdvm
from sdvm_pretty import pretty
from sdvm_refactor import refatora
from sdvm_smells import CATALOGO, detecta, resumo

AUTOMATICOS = {c for (c, i) in CATALOGO.items() if i.automatico}


def prog(corpo_main, extra=""):
    return extra + "int main() {\n" + corpo_main + "\n}\n"


def codigos(src):
    return set(resumo(detecta(parse_sdvm(src))))


def refatorado(src):
    p, _ = refatora(parse_sdvm(src))
    return pretty(p)


def corpo_main(src):
    """texto do corpo de main depois do refactoring (sem a 1a e ultima linha)"""
    texto = refatorado(src)
    linhas = texto[texto.index("int main() {"):].strip().splitlines()[1:-1]
    return "\n".join(l[4:] for l in linhas)


# ======================================================================
# 1. um teste por smell
# ======================================================================

CASOS = [
    # (codigo, programa, corpo de main esperado depois do refactoring)
    ("S01", prog("bool b = true;\nif (b == true) print(1);\nif (b != true) print(2);\nreturn 0;"),
     "bool b = true;\nif (b)\n    print(1);\nif (!b)\n    print(2);\nreturn 0;"),
    ("S02", prog("bool b = true;\nint x = 3;\nprint(!!b);\nprint(- -x);\nprint(+x);\nreturn 0;"),
     "bool b = true;\nint x = 3;\nprint(b);\nprint(x);\nprint(x);\nreturn 0;"),
    ("S03", prog("int x = 3;\ndouble d = 2.5;\nprint(x + 0);\nprint(1 * x);\nprint(d * 1);\nprint(0 - x);\nreturn 0;"),
     "int x = 3;\ndouble d = 2.5;\nprint(x);\nprint(x);\nprint(d);\nprint(-x);\nreturn 0;"),
    ("S04", prog("int x = 3;\nprint((int) x);\nprint((double) x);\nreturn 0;"),
     "int x = 3;\nprint(x);\nprint((double) x);\nreturn 0;"),
    ("S05", prog("print(pos(3));\nreturn 0;",
                 "bool pos(int n) {\n    if (n > 0) {\n        return true;\n    } else {\n        return false;\n    }\n}\n"),
     "print(pos(3));\nreturn 0;"),
    ("S06", prog("int x = 3;\nbool b;\nif (x > 2) b = false; else b = true;\nprint(b);\nreturn 0;"),
     "int x = 3;\nbool b;\nb = !(x > 2);\nprint(b);\nreturn 0;"),
    ("S07", prog("if (true) print(1); else print(2);\nwhile (false) print(3);\nreturn 0;"),
     "print(1);\nreturn 0;"),
    ("S08", prog("print(1);\nreturn 0;\nprint(2);"),
     "print(1);\nreturn 0;"),
    ("S09", prog("int x = 3;\nif (x > 1) { print(x); } else { print(x); }\nreturn 0;"),
     "int x = 3;\nprint(x);\nreturn 0;"),
    ("S10", prog("int x = 3;\nif (x > 1) {} else { print(x); }\nreturn 0;"),
     "int x = 3;\nif (!(x > 1)) {\n    print(x);\n}\nreturn 0;"),
    ("S11", prog("int x = 3;\nif (x > 1) { if (x < 5) { print(x); } }\nreturn 0;"),
     "int x = 3;\nif (x > 1 && x < 5) {\n    print(x);\n}\nreturn 0;"),
    ("S12", prog("int x = 3;\nif (x > 1) { return 1; } else { print(x); }\nreturn 0;"),
     "int x = 3;\nif (x > 1) {\n    return 1;\n}\nprint(x);\nreturn 0;"),
    ("S13", prog("int x = 3;\nx = x;\nprint(x);\nreturn 0;"),
     "int x = 3;\nprint(x);\nreturn 0;"),
    ("S14", prog("{ print(1); }\n{}\nreturn 0;"),
     "print(1);\nreturn 0;"),
    ("S15", prog("int x = 3;\nint y = 4;\nprint(x);\nreturn 0;"),
     "int x = 3;\nprint(x);\nreturn 0;"),
]


def test_cada_smell_e_detetado_e_refatorado():
    for (codigo, src, esperado) in CASOS:
        assert codigo in codigos(src), (codigo, codigos(src))
        obtido = corpo_main(src)
        assert obtido == esperado, "%s:\n%s\n--- esperado:\n%s" % (codigo, obtido, esperado)


def test_s05_texto_da_funcao():
    src = CASOS[4][1]
    assert "bool pos(int n) {\n    return n > 0;\n}" in refatorado(src)
    src2 = prog("print(neg(3));\nreturn 0;",
                "bool neg(int n) {\n    if (n < 0) return true;\n    return false;\n}\n")
    assert "S05" in codigos(src2)
    assert "bool neg(int n) {\n    return n < 0;\n}" in refatorado(src2)


def test_s16_codigo_morto():
    src = prog("print(usada(1));\nreturn 0;",
               "int g = 5;\nint usada(int a) { return a; }\n"
               "int morta(int a) { return morta2(a); }\nint morta2(int a) { return a; }\n")
    ss = detecta(parse_sdvm(src))
    assert len([s for s in ss if s.codigo == "S16"]) == 3
    texto = refatorado(src)
    assert "morta" not in texto and "int g" not in texto and "usada" in texto


def test_smells_so_detetados():
    src = (
        "int g = 0;\n"
        "int f(int a, int b, int c, int d) {\n"
        "    int t = 0;\n"
        "    if (a > 0) { while (b > 0) { if (c > 0) { for (int i = 0; i < 3; i = i + 1) { t = t + 1; } } b = b - 1; } }\n"
        "    if (a > 0 && b > 0 || c > 0 && t > 0) t = 99;\n"
        "    g = t;\n"
        "    return t;\n"
        "}\n"
        "int h(int n) {\n"
        "    int s = 0;\n"
        "    while (n > 0) { s = s + n * 10; n = n - 1; }\n"
        "    while (n > 0) { s = s + n * 10; n = n - 1; }\n"
        + "    s = s + 1;\n" * 18 +
        "    return s;\n"
        "}\n"
        "int main() { print(f(1, 2, 3, 4)); print(h(3)); return 0; }\n")
    cs = codigos(src)
    for c in ["S17", "S18", "S19", "S20", "S21", "S22", "S23", "S24", "S25"]:
        assert c in cs, c


# ======================================================================
# 2. casos em que NAO se pode refatorar
# ======================================================================

NAO_APLICA = [
    # x e int: x == true (x == 1) nao e o mesmo que x
    prog("int x = 2;\nif (x == true) print(1);\nreturn 0;"),
    # !!x com x int converte para bool (2 -> true)
    prog("int x = 2;\nprint(!!x);\nreturn 0;"),
    # c + 0 com char da um int (escreve 65 e nao A)
    prog("char c = 'A';\nprint(c + 0);\nreturn 0;"),
    # d + 0 com double: -0.0 + 0 == 0.0
    prog("double d = -0.0;\nprint(d + 0);\nreturn 0;"),
    # a condicao chama uma funcao (pode ter efeitos): nao se tira o if
    prog("int x = 1;\nif (f() > 0) print(x); else print(x);\nreturn 0;",
         "int f() { print(9); return 1; }\n"),
    # variavel nao usada mas o valor inicial chama uma funcao
    prog("int y = f();\nreturn 0;", "int f() { print(9); return 1; }\n"),
    # o else tem declaracoes: fica como bloco (nao se juntam ao bloco de fora)
    prog("int x = 3;\nif (x > 1) return 1; else { int y = 2; print(y); }\nint y = 5;\nprint(y);\nreturn 0;"),
]


def test_casos_que_nao_mudam_o_comportamento():
    for src in NAO_APLICA:
        a = parse_sdvm(src)
        b, _ = refatora(a)
        assert executa(a) == executa(b), src
        parse_sdvm(pretty(b))


def test_nao_aplica_nos_tipos_errados():
    assert "S01" not in codigos(NAO_APLICA[0])
    assert "S02" not in codigos(NAO_APLICA[1])
    assert "S03" not in codigos(NAO_APLICA[2])
    assert "S03" not in codigos(NAO_APLICA[3])
    assert "S09" not in codigos(NAO_APLICA[4])
    assert "S15" not in codigos(NAO_APLICA[5])


# ======================================================================
# 3. programas de exemplo
# ======================================================================

FICHEIROS = sorted(glob.glob("exemplos/*")) + ["testes/extra_ok"] + sorted(glob.glob("testes_smells/*"))
INPUTS = [[17], [2000], [0], [1], [-5], [97]]


def verifica_programa(a, inputs=INPUTS):
    b, log = refatora(a)
    texto = pretty(b)
    # o programa refatorado e valido e o pretty printer faz round-trip
    # (comparamos o texto: o printer pode por chavetas a mais num if
    #  aninhado com else, para evitar o "dangling else")
    assert pretty(parse_sdvm(texto)) == texto
    # ja nao tem smells com refactoring automatico
    restantes = set(resumo(detecta(b))) & AUTOMATICOS
    assert not restantes, restantes
    # refatorar outra vez nao muda nada
    c, log2 = refatora(b)
    assert c == b and not log2, log2
    # mesmo comportamento
    for inp in inputs:
        assert executa(a, inp) == executa(b, inp), (inp, executa(a, inp), executa(b, inp))
    return log


def test_programas_de_exemplo():
    total = 0
    for f in FICHEIROS:
        with open(f, encoding="utf-8") as fh:
            a = parse_sdvm(fh.read())
        log = verifica_programa(a)
        total += sum(log.values())
    assert total > 0


# ======================================================================
# 4. teste aleatorio
# ======================================================================

class Gerador:
    """gera programas aleatorios (que terminam sempre) cheios de smells"""

    def __init__(self, rnd):
        self.r = rnd
        self.contador = 0

    def novo(self, prefixo):
        self.contador += 1
        return prefixo + str(self.contador)

    def int_exp(self, d=0):
        r = self.r
        op = r.randrange(9 if d < 3 else 2)
        if op == 0:
            return str(r.randrange(-3, 10))
        if op == 1:
            return r.choice(["x", "y", "z"])
        if op == 2:
            return "%s %s %s" % (self.int_exp(d + 1), r.choice("+-*"), self.int_exp(d + 1))
        if op == 3:
            return r.choice(["%s + 0", "0 + %s", "%s * 1", "1 * %s", "%s - 0", "0 - %s", "%s / 1"]) % ("(" + self.int_exp(d + 1) + ")")
        if op == 4:
            return "- -(%s)" % self.int_exp(d + 1)
        if op == 5:
            return "(int) (%s)" % self.int_exp(d + 1)
        if op == 6:
            return "f%d(%s)" % (r.randrange(2), self.int_exp(d + 1))
        if op == 7:
            return "(%s) %% %d" % (self.int_exp(d + 1), r.randrange(1, 5))
        return "a[%d]" % r.randrange(3)

    def bool_exp(self, d=0):
        r = self.r
        op = r.randrange(8 if d < 3 else 2)
        if op == 0:
            return r.choice(["true", "false", "b"])
        if op == 1:
            return "%s %s %s" % (self.int_exp(d + 1), r.choice(["<", "<=", ">", ">=", "==", "!="]), self.int_exp(d + 1))
        if op == 2:
            return "(%s) %s (%s)" % (self.bool_exp(d + 1), r.choice(["&&", "||"]), self.bool_exp(d + 1))
        if op == 3:
            return "(%s) %s %s" % (self.bool_exp(d + 1), r.choice(["==", "!="]), r.choice(["true", "false"]))
        if op == 4:
            return "!!(%s)" % self.bool_exp(d + 1)
        if op == 5:
            return "!(%s)" % self.bool_exp(d + 1)
        if op == 6:
            return "p(%s)" % self.int_exp(d + 1)
        return "(bool) (%s)" % self.bool_exp(d + 1)

    def stmt(self, d=0, em_ciclo=False):
        r = self.r
        k = r.randrange(16 if d < 3 else 4)
        v = r.choice(["x", "y", "z"])
        if k == 0:
            return "%s = %s;" % (v, self.int_exp())
        if k == 1:
            return "print(%s);" % self.int_exp()
        if k == 2:
            return "b = %s;" % self.bool_exp()
        if k == 3:
            return "%s = %s;" % (v, v)
        if k == 4:
            return "if (%s) %s else %s" % (self.bool_exp(), self.bloco(d + 1, em_ciclo), self.bloco(d + 1, em_ciclo))
        if k == 5:
            return "if (%s) %s" % (self.bool_exp(), self.bloco(d + 1, em_ciclo))
        if k == 6:
            return "if (%s) {} else %s" % (self.bool_exp(), self.bloco(d + 1, em_ciclo))
        if k == 7:
            return "if (%s) { if (%s) %s }" % (self.bool_exp(), self.bool_exp(), self.bloco(d + 1, em_ciclo))
        if k == 8:
            i = self.novo("i")
            return "for (int %s = 0; %s < %d; %s = %s + 1) %s" % (i, i, r.randrange(4), i, i, self.bloco(d + 1, True))
        if k == 9:
            return "if (%s) b = true; else b = false;" % self.bool_exp()
        if k == 10:
            return "if (%s) %s" % (r.choice(["true", "false"]), self.bloco(d + 1, em_ciclo))
        if k == 11:
            return "{ %s %s }" % (self.stmt(d + 1, em_ciclo), self.stmt(d + 1, em_ciclo))
        if k == 12:
            return "int %s = %s;" % (self.novo("u"), self.int_exp())
        if k == 13 and em_ciclo:
            return "if (%s) { %s break; %s }" % (self.bool_exp(), self.stmt(d + 1, em_ciclo), self.stmt(d + 1, em_ciclo))
        if k == 14 and em_ciclo:
            return "if (%s) { %s continue; %s }" % (self.bool_exp(), self.stmt(d + 1, em_ciclo), self.stmt(d + 1, em_ciclo))
        if k == 15:
            s = self.stmt(d + 1, em_ciclo)
            return "if (%s) %s else %s" % (self.bool_exp(), s, s)
        return "a[%d] = %s;" % (r.randrange(3), self.int_exp())

    def bloco(self, d, em_ciclo):
        n = self.r.randrange(1, 4)
        return "{ " + " ".join(self.stmt(d, em_ciclo) for _ in range(n)) + " }"

    def programa(self):
        corpo = " ".join(self.stmt() for _ in range(self.r.randrange(3, 9)))
        return (
            "int a[3] = {1, 2, 3};\n"
            "int nunca = 7;\n"
            "int f0(int n) { if (n > 5) { return n - 1; } else { return n + 1; } }\n"
            "int f1(int n) { print(n); return n * 1; }\n"
            "bool p(int n) { if (n % 2 == 0) return true; else return false; }\n"
            "int morta(int n) { return n; }\n"
            "int main() { int x = 1; int y = 2; int z = 3; bool b = false; "
            + corpo +
            " print(x); print(y); print(z); print(b); return x; }\n")


def test_aleatorio(n=300, semente=2026):
    rnd = random.Random(semente)
    g = Gerador(rnd)
    usados = set()
    for _ in range(n):
        src = g.programa()
        a = parse_sdvm(src)
        log = verifica_programa(a, inputs=[[]])
        usados |= set(log)
    # o gerador exercita (quase) todos os refactorings
    assert len(usados) >= 14, sorted(usados)


# ======================================================================

if __name__ == "__main__":
    testes = [(nome, f) for (nome, f) in sorted(globals().items())
              if nome.startswith("test_") and callable(f)]
    falhas = 0
    for nome, f in testes:
        try:
            f()
            print("OK     " + nome)
        except AssertionError as e:
            falhas += 1
            print("FALHOU " + nome + "\n" + str(e))
    print("\n%d testes, %d falhas" % (len(testes), falhas))
    sys.exit(1 if falhas else 0)
