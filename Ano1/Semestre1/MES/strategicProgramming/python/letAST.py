from dataclasses import dataclass

type List = NestedLet | Assign | Empty

type Exp = Add | Sub | Mul | Neg | Var | Const


@dataclass
class Let:
    lst: List
    exp: Exp

    def __repr__(self):
        return f"Let({repr(self.lst)}, {repr(self.exp)})"
    
    def __str__(self):
        lst_str = str(self.lst).rstrip()
        lines = lst_str.splitlines()

        if lines:
            indented = [lines[0]] + ["    " + line for line in lines[1:]]
            formatted = "\n".join(indented)
        else:
            formatted = ""

        return f"let {formatted}\nin {self.exp}"

@dataclass
class NestedLet:
    name: str
    let: Let
    lst: List

    def __repr__(self):
        return f"NestedLet({repr(self.name)}, {repr(self.let)}, {repr(self.lst)})"

    def __str__(self):
        l_str = str(self.let).rstrip()
        lines = l_str.splitlines()
        if lines:
            indent = " " * (3 + len(self.name))
            indented = [lines[0]] + [indent + line for line in lines[1:]]
            formatted_let = "\n".join(indented)
        else:
            formatted_let = ""

        lst_str = str(self.lst)
        if lst_str:
            return f"{self.name} = {formatted_let}\n{lst_str}"
        else:
            return f"{self.name} = {formatted_let}"

@dataclass
class Assign:
    name: str
    exp: Exp
    lst: List

    def __repr__(self):
        return f"Assign({repr(self.name)}, {repr(self.exp)}, {repr(self.lst)})"

    def __str__(self):
        lst_str = str(self.lst)
        if lst_str:
            return f"{self.name} = {self.exp}\n{self.lst}"
        else: 
            return f"{self.name} = {self.exp}"

@dataclass
class Empty:
    pass

    def __repr__(self):
        return "Empty()"

    def __str__(self):
        return ""

@dataclass
class Add:
    x: Exp
    y: Exp

    def __repr__(self):
        return f"Add({repr(self.x)}, {repr(self.y)})"

    def __str__(self):
        return f"{self.x} + {self.y}"

@dataclass
class Sub:
    x: Exp
    y: Exp

    def __repr__(self):
        return f"Sub({repr(self.x)}, {repr(self.y)})"

    def __str__(self):
        return f"{self.x} - {self.y}"

@dataclass
class Mul:
    x: Exp
    y: Exp

    def __repr__(self):
        return f"Mul({repr(self.x)}, {repr(self.y)})"

    def __str__(self):
        return f"{self.x} * {self.y}"

@dataclass
class Neg:
    x: Exp

    def __repr__(self):
        return f"Neg({repr(self.x)})"

    def __str__(self):
        return f"-{self.x}"

@dataclass
class Var:
    name: str

    def __repr__(self):
        return f"Var({repr(self.name)})"

    def __str__(self):
        return self.name

@dataclass
class Const:
    value: int

    def __repr__(self):
        return f"Const({self.value})"

    def __str__(self):
        return str(self.value)
            

ex1 = Let(Assign("a", Add(Const(1), Const(0)),
          Assign("b", Add(Const(0), Const(1)),
          Empty())),
          Add(Var("a"), Var("b")))

ex2 = Let(Assign("a", Add(Var("b"), Const(-16)),
          Assign("c", Const(8),
          NestedLet("w",
                    Let(Assign("z", Add(Var("a"), Var("b")), Empty()),
                    Add(Var("z"), Var("b"))),
          Assign("b",Sub(Add(Var("c"), Const(3)), Var("c")),
          Empty())))),
          Sub(Add(Var("c"), Var("a")), Var("w")))

ex3 = Let(Assign("a", Add(Var("b"), Const(0)),
          Assign("c", Const(2),
          Assign("b", Sub((Add(Var("c"), Const(3))), Var("c")),
          Empty()))),
          Sub(Add(Var("a"), Const(7)), Var("c")))

ex4 = Let(Assign("a", Add(Add(Const(1), Const(0)), Const(0)),
          Assign("b", Add(Const(0), Const(1)),
          Empty())),
          Add(Var("a"), Var("b")))

print(ex1)

example = Let(Assign("a",Sub(Var("b"), Const(16)),
              Assign("c",Const(8),
              NestedLet("w",Let(NestedLet("y",Let(Assign("q",Add(Const(3), Const(4)),
                                Empty()),
                            Var("q")),
                        Assign("z",Add(Add(Const(0), Var("a")),Const(0)),
                        Empty())),
                    Add(Var("z"), Var("b"))),
                Assign("b",Sub(Add(Var("c"), Const(3)),Var("c")),
                Empty())))),
        Sub(Add(Var("c"), Var("a")),Var("w")))


print(example)
