from dataclasses import fields, is_dataclass
from typing import Any, Iterator
 
from bc_ast import (
    Bin, BinOp, Not, Num, SIf,
    Program, factorial, program,
    # só para os testes no fim:
    Def, StmtItem, FunDef, ScalarParam, SReturn, SExpr, Call, ArgExp,
    var, Rel, RelOp, SBlock, set_, LVar,
)


 