from parsy import *
from dataclasses import dataclass
from functools import reduce

@dataclass
class Val:
    v: int

@dataclass
class Add:
    left: "Exp"
    right: "Exp"

@dataclass
class Mul:
    left: "Exp"
    right: "Exp"

@dataclass
class Equal:
    left: "Exp"
    right: "Exp"

type Exp = Val | Add | Mul | Equal


@generate
def pExp():
    first = yield pTermo
    rest = yield (string('+') >> pTermo).many()
    return reduce(lambda acc, right: Add(acc, right), rest, first)


@generate
def pTermo():
    first = yield pFactor
    rest = yield (string('*') >> pFactor).many()
    return reduce(lambda acc, right: Mul(acc, right), rest, first)

@generate
def pEqual():
    first = yield pExp
    rest = yield (string('==') >> pExp).many()
    return reduce(lambda acc, right: Equal(acc, right), rest, first)


""" @generate 
def pEqual():
    first = yield pExp
    second = yield (string('==') >> pExp).many()
    result = first
    for exp in second:
        result = Equal(result, exp)
    return result  """

pFactor = (
    regex(r'[0-9]+').map(lambda s: Val(int(s)))
    | (string('(') >> pExp << string(')'))
)

print(pEqual.parse("1+2*3==5"))