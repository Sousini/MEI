"""
Software Maintenance and Evolution
2026/2027
University of Minho

Abstract syntax of the Linux bc language (Python version of BCast.hs) made using Claude.

Convenções da tradução:
  * cada construtor Haskell passou a ser uma dataclass imutável (frozen),
    o que dá __repr__ (≈ Show) e __eq__ (≈ Eq) automaticamente;
  * cada tipo soma passou a ser um alias de Union;
  * Maybe a  ->  Optional[a]  (None = Nothing);
  * `Stmt` (construtor de Item) foi renomeado para `StmtItem`, para não
    colidir com o tipo `Stmt`; `Def` mantém-se;
  * `Eq'` (RelOp) passou a `RelOp.Eq`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Union

# POSIX: one lowercase letter; GNU: [a-z][a-z0-9_]*
Name = str


# --------------------------------------------------------------------------
# Enumerações simples
# --------------------------------------------------------------------------

class BinOp(Enum):
    Add = "Add"
    Sub = "Sub"
    Mul = "Mul"
    Div = "Div"
    Mod = "Mod"
    Pow = "Pow"

    def __repr__(self) -> str:
        return self.value


class RelOp(Enum):
    Lt = "Lt"
    Le = "Le"
    Gt = "Gt"
    Ge = "Ge"
    Eq = "Eq"
    Ne = "Ne"

    def __repr__(self) -> str:
        return self.value


class SpecialVar(Enum):
    Scale = "Scale"
    IBase = "IBase"
    OBase = "OBase"
    Last = "Last"   # last (also written ".") is a GNU extension

    def __repr__(self) -> str:
        return self.value


# --------------------------------------------------------------------------
# Parâmetros e locais
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class ScalarParam:          # x
    name: Name


@dataclass(frozen=True)
class ArrayParam:           # a[]
    name: Name


Param = Union[ScalarParam, ArrayParam]


@dataclass(frozen=True)
class ScalarLocal:          # auto x
    name: Name


@dataclass(frozen=True)
class ArrayLocal:           # auto a[]
    name: Name


Local = Union[ScalarLocal, ArrayLocal]


# --------------------------------------------------------------------------
# L-values
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class LVar:                 # x
    name: Name


@dataclass(frozen=True)
class LIndex:               # a[e]
    name: Name
    index: "Exp"


@dataclass(frozen=True)
class LSpecial:             # scale, ibase, obase, last
    var: SpecialVar


LValue = Union[LVar, LIndex, LSpecial]


# --------------------------------------------------------------------------
# Atribuição
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Assign:
    """op=None: '='   op=BinOp.X: +=, -=, *=, /=, %=, ^="""
    op: Optional[BinOp]
    lvalue: LValue
    exp: "Exp"


# --------------------------------------------------------------------------
# Expressões
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Num:                  # kept as written: value depends on ibase (0-9, A-F)
    value: str


@dataclass(frozen=True)
class LV:                   # variable, array element or special variable
    lvalue: LValue


@dataclass(frozen=True)
class AssignE:              # assignment used as an expression, as in (a = 1)
    assign: Assign


@dataclass(frozen=True)
class PreInc:
    lvalue: LValue


@dataclass(frozen=True)
class PreDec:
    lvalue: LValue


@dataclass(frozen=True)
class PostInc:
    lvalue: LValue


@dataclass(frozen=True)
class PostDec:
    lvalue: LValue


@dataclass(frozen=True)
class Neg:
    exp: "Exp"


@dataclass(frozen=True)
class Not:                  # GNU
    exp: "Exp"


@dataclass(frozen=True)
class Bin:
    op: BinOp
    left: "Exp"
    right: "Exp"


@dataclass(frozen=True)
class Rel:
    op: RelOp
    left: "Exp"
    right: "Exp"


@dataclass(frozen=True)
class And:                  # GNU: &&
    left: "Exp"
    right: "Exp"


@dataclass(frozen=True)
class Or:                   # GNU: ||
    left: "Exp"
    right: "Exp"


@dataclass(frozen=True)
class Call:                 # also math library functions, such as s(x) and c(x)
    name: Name
    args: List["Arg"]


@dataclass(frozen=True)
class Length:               # length(e)
    exp: "Exp"


@dataclass(frozen=True)
class Sqrt:                 # sqrt(e)
    exp: "Exp"


@dataclass(frozen=True)
class ScaleOf:              # scale(e): number of digits after the decimal point
    exp: "Exp"


@dataclass(frozen=True)
class Read:                 # GNU: read()
    pass


Exp = Union[
    Num, LV, AssignE,
    PreInc, PreDec, PostInc, PostDec,
    Neg, Not, Bin, Rel, And, Or,
    Call, Length, Sqrt, ScaleOf, Read,
]


@dataclass(frozen=True)
class ArgExp:               # an expression...
    exp: Exp


@dataclass(frozen=True)
class ArgArray:             # ...or a whole array
    name: Name


Arg = Union[ArgExp, ArgArray]


# --------------------------------------------------------------------------
# Instruções
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class PrintStr:
    value: str


@dataclass(frozen=True)
class PrintExp:
    exp: Exp


PrintItem = Union[PrintStr, PrintExp]


@dataclass(frozen=True)
class SAssign:              # a bare assignment: evaluated, not printed
    assign: Assign


@dataclass(frozen=True)
class SExpr:                # any other expression: evaluated and printed
    exp: Exp


@dataclass(frozen=True)
class SString:              # a string: printed
    value: str


@dataclass(frozen=True)
class SPrint:               # GNU: print list
    items: List[PrintItem]


@dataclass(frozen=True)
class SBlock:               # { statement_list }
    stmts: List["Stmt"]


@dataclass(frozen=True)
class SIf:
    cond: Exp
    then: "Stmt"
    orelse: Optional["Stmt"] = None     # the else branch is a GNU extension


@dataclass(frozen=True)
class SWhile:
    cond: Exp
    body: "Stmt"


@dataclass(frozen=True)
class SFor:                 # GNU: the three expressions are optional
    init: Optional[Exp]
    cond: Optional[Exp]
    step: Optional[Exp]
    body: "Stmt"


@dataclass(frozen=True)
class SBreak:
    pass


@dataclass(frozen=True)
class SContinue:            # GNU
    pass


@dataclass(frozen=True)
class SReturn:              # return / return (E)
    exp: Optional[Exp] = None


@dataclass(frozen=True)
class SQuit:                # quit: stops bc when it is read
    pass


@dataclass(frozen=True)
class SHalt:                # GNU: stops bc when it is executed
    pass


@dataclass(frozen=True)
class SLimits:              # GNU pseudo statement
    pass


@dataclass(frozen=True)
class SWarranty:            # GNU pseudo statement
    pass


Stmt = Union[
    SAssign, SExpr, SString, SPrint, SBlock, SIf, SWhile, SFor,
    SBreak, SContinue, SReturn, SQuit, SHalt, SLimits, SWarranty,
]


# --------------------------------------------------------------------------
# Funções e programa
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class FunDef:
    """define [void] name(params) { auto ...; statements }"""
    void: bool                  # GNU extension: define void f(...)
    name: Name
    params: List[Param]
    autos: List[Local]          # the auto declarations, at the start of the body
    body: List[Stmt]


@dataclass(frozen=True)
class Def:
    fundef: FunDef


@dataclass(frozen=True)
class StmtItem:                 # `Stmt` no Haskell (construtor de Item)
    stmt: Stmt


Item = Union[Def, StmtItem]


@dataclass(frozen=True)
class Program:
    """A bc program is a sequence of function definitions and statements"""
    items: List[Item] = field(default_factory=list)


# --------------------------------------------------------------------------
# Abreviaturas para manter a sintaxe abstrata legível
# --------------------------------------------------------------------------

def var(n: Name) -> Exp:
    return LV(LVar(n))


def set_(l: LValue, e: Exp) -> Stmt:
    """a bare assignment statement"""
    return SAssign(Assign(None, l, e))


def upd(op: BinOp, l: LValue, e: Exp) -> Stmt:
    """a compound assignment: +=, /=, ..."""
    return SAssign(Assign(op, l, e))


def set_e(l: LValue, e: Exp) -> Exp:
    """an assignment used as an expression"""
    return AssignE(Assign(None, l, e))


# --------------------------------------------------------------------------
# Factorial do manual do bc:
#   define f (x) { if (x <= 1) return (1); return (f(x-1) * x); }
# --------------------------------------------------------------------------

factorial = Program([
    Def(FunDef(
        False, "f", [ScalarParam("x")], [],
        [
            SIf(Rel(RelOp.Le, var("x"), Num("1")), SReturn(Num("1")), None),
            SReturn(Bin(BinOp.Mul,
                        Call("f", [ArgExp(Bin(BinOp.Sub, var("x"), Num("1")))]),
                        var("x"))),
        ],
    )),
    StmtItem(SExpr(Call("f", [ArgExp(Num("10"))]))),
])


# --------------------------------------------------------------------------
# Programa mais elaborado
#
# /* Fibonacci numbers, the Collatz conjecture and Newton's method */
# define fib(n) {
#     auto a, b, t, i
#     if (n < 2) return (n)
#     a = 0
#     b = 1
#     for (i = 2; i <= n; i++) {
#         t = a + b
#         a = b
#         b = t
#     }
#     return (b)
# }
#
# define sum(a[], n) {
#     auto i, s
#     for (i = 0; i < n; i++) s += a[i]
#     return (s)
# }
#
# define collatz(n) {
#     auto steps
#     while (1) {
#         if (n == 1) break
#         if (n % 2 == 0) {
#             n /= 2
#         } else {
#             n = 3 * n + 1
#         }
#         steps += 1
#     }
#     return (steps)
# }
#
# define void show(x) {
#     print "value: ", x, "\n"
# }
#
# for (k = 0; k < 10; k++) v[k] = fib(k)
# show(sum(v[], 10))
# collatz(27)
# scale = 20
# x = 1
# for (i = 0; i < 6; i++) x = (x + 2 / x) / 2
# x
# sqrt(2)
#
# Run with GNU bc 1.07.1, it prints:
# value: 88
# 111
# 1.41421356237309504880
# 1.41421356237309504880
# --------------------------------------------------------------------------

fib = FunDef(
    False, "fib", [ScalarParam("n")],
    [ScalarLocal("a"), ScalarLocal("b"), ScalarLocal("t"), ScalarLocal("i")],
    [
        SIf(Rel(RelOp.Lt, var("n"), Num("2")), SReturn(var("n")), None),
        set_(LVar("a"), Num("0")),
        set_(LVar("b"), Num("1")),
        SFor(
            set_e(LVar("i"), Num("2")),
            Rel(RelOp.Le, var("i"), var("n")),
            PostInc(LVar("i")),
            SBlock([
                set_(LVar("t"), Bin(BinOp.Add, var("a"), var("b"))),
                set_(LVar("a"), var("b")),
                set_(LVar("b"), var("t")),
            ]),
        ),
        SReturn(var("b")),
    ],
)

sum_fun = FunDef(
    False, "sum", [ArrayParam("a"), ScalarParam("n")],
    [ScalarLocal("i"), ScalarLocal("s")],
    [
        SFor(
            set_e(LVar("i"), Num("0")),
            Rel(RelOp.Lt, var("i"), var("n")),
            PostInc(LVar("i")),
            upd(BinOp.Add, LVar("s"), LV(LIndex("a", var("i")))),
        ),
        SReturn(var("s")),
    ],
)

collatz = FunDef(
    False, "collatz", [ScalarParam("n")], [ScalarLocal("steps")],
    [
        SWhile(
            Num("1"),
            SBlock([
                SIf(Rel(RelOp.Eq, var("n"), Num("1")), SBreak(), None),
                SIf(
                    Rel(RelOp.Eq, Bin(BinOp.Mod, var("n"), Num("2")), Num("0")),
                    SBlock([upd(BinOp.Div, LVar("n"), Num("2"))]),
                    SBlock([
                        set_(LVar("n"),
                             Bin(BinOp.Add,
                                 Bin(BinOp.Mul, Num("3"), var("n")),
                                 Num("1"))),
                    ]),
                ),
                upd(BinOp.Add, LVar("steps"), Num("1")),
            ]),
        ),
        SReturn(var("steps")),
    ],
)

show_fun = FunDef(
    True, "show", [ScalarParam("x")], [],
    [SPrint([PrintStr("value: "), PrintExp(var("x")), PrintStr("\\n")])],
)

program = Program([
    Def(fib), Def(sum_fun), Def(collatz), Def(show_fun),
    StmtItem(SFor(
        set_e(LVar("k"), Num("0")),
        Rel(RelOp.Lt, var("k"), Num("10")),
        PostInc(LVar("k")),
        set_(LIndex("v", var("k")), Call("fib", [ArgExp(var("k"))])),
    )),
    StmtItem(SExpr(Call("show", [
        ArgExp(Call("sum", [ArgArray("v"), ArgExp(Num("10"))])),
    ]))),
    StmtItem(SExpr(Call("collatz", [ArgExp(Num("27"))]))),
    StmtItem(set_(LSpecial(SpecialVar.Scale), Num("20"))),
    StmtItem(set_(LVar("x"), Num("1"))),
    StmtItem(SFor(
        set_e(LVar("i"), Num("0")),
        Rel(RelOp.Lt, var("i"), Num("6")),
        PostInc(LVar("i")),
        set_(LVar("x"),
             Bin(BinOp.Div,
                 Bin(BinOp.Add, var("x"), Bin(BinOp.Div, Num("2"), var("x"))),
                 Num("2"))),
    )),
    StmtItem(SExpr(var("x"))),
    StmtItem(SExpr(Sqrt(Num("2")))),
])


if __name__ == "__main__":
    print(factorial)
    print()
    print(program)
