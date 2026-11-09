from parsy import *
from dataclasses import dataclass

type Exp = Val | Add | Mul | Equal

@dataclass
class Val:
    v: int

@dataclass
class Add:
    left: Exp
    right: Exp

@dataclass
class Mul:
    left: Exp
    right: Exp

@dataclass
class Equal:
    left: Exp
    right: Exp




@generate
def pExp():
    first = yield pTermo
    second = yield (string('+') >> pExp).optional()
    if second:
        return Add(first,second)
    return first

@generate
def pTermo():
    first = yield pFactor
    second = yield (string('*') >> pTermo).optional()
    if second:
        return Mul(first,second)
    return first




@generate
def pEqual():
    first = yield pExp
    second = yield (string('==') >> pEqual).optional()
    if second:
        return Equal(first,second)
    return first



pFactor = (
    regex(r'[0-9]+').map(lambda s: Val(int(s)))
    | string('(') >> pExp << string(')')
)

print(pEqual.parse("3+4==5*3"))








