from pyztrategic.zipper import obj
from pyztrategic import strategy as st
from letAST import *


def etiqueta_var(ast):

    def step(x):
        if isinstance(x, Var):
            return Var("v_" + x.name)
        elif isinstance(x, Assign):
            return Assign("v_" + x.name, x.exp, x.lst)
        elif isinstance(x, NestedLet):
            return NestedLet("v_" + x.name, x.let_val, x.lst)
        raise st.StrategicError

    def etiqueta(x):
        return st.adhocTP(st.idTP, step, x)

    return st.full_tdTP(etiqueta, obj(ast)).node()





def optimise(ast):
    def opt(x):
        if isinstance(x, Add) and isinstance(x.y, Const) and x.y.value == 0:
            return x.x
        if isinstance(x, Add) and isinstance(x.x, Const) and x.x.value == 0:
            return x.y
        if isinstance(x, Mul) and isinstance(x.y, Const) and x.y.value == 1:
            return x.x
        if isinstance(x, Mul) and isinstance(x.x, Const) and x.x.value == 1:
            return x.y

        raise st.StrategicError

    def strategy(z):
        return st.adhocTP(st.idTP, opt, z)

    return st.full_tdTP(strategy, obj(ast)).node()
        



def optimiseInnerMost(ast):
    def optI(x):

        if isinstance(x, Add) and isinstance(x.x, Const) and isinstance(x.y, Const):
            return Const(x.x.value + x.y.value)
        if isinstance(x, Sub) and isinstance(x.x, Const) and isinstance(x.y, Const):
            return Const(x.x.value - x.y.value)
        if isinstance(x, Mul) and isinstance(x.x, Const) and isinstance(x.y, Const):
            return Const(x.x.value * x.y.value)


        if isinstance(x, Add) and isinstance(x.y, Const) and x.y.value == 0:
            return x.x
        if isinstance(x, Add) and isinstance(x.x, Const) and x.x.value == 0:
            return x.y
        if isinstance(x, Sub) and isinstance(x.y, Const) and x.y.value == 0:
            return x.x
        if isinstance(x, Sub) and isinstance(x.x, Const) and x.x.value == 0:
            return x.y;
            
        if isinstance(x, Mul) and isinstance(x.y, Const) and x.y.value == 1:
            return x.x
        if isinstance(x, Mul) and isinstance(x.x, Const) and x.x.value == 1:
            return x.y

        raise st.StrategicError

    def strategyI(z):
        return st.adhocTP(st.failTP, optI, z)

    return st.innermost(strategyI, obj(ast)).node()
        

#print(optimiseInnerMost(example))


def recolheVars(ast):

    vars = set()

    def step(x):
        if isinstance(x, Var):
            vars.add(x.name)
        elif isinstance(x, Assign):
            vars.add(x.name)
        elif isinstance(x, NestedLet):
            vars.add(x.name)

        return x

    def strategy(z):
        return st.adhocTP(st.idTP, step, z)

    st.full_buTP(strategy, obj(ast))

    return vars

print(recolheVars(example))