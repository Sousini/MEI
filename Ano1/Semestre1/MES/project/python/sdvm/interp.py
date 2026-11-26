"""
Interpretador simples da SDVM-Lang (semantica parecida com a de C).

Serve para TESTAR os refactorings: um refactoring nao pode mudar o
comportamento do programa, por isso corremos o programa original e o
refatorado com o mesmo input e comparamos o output.

Uso:
    python -m sdvm run programa [inputs...]

    from sdvm.interp import executa
    saida, retorno = executa(ast, inputs=[5, 3])
"""


from .parser import (Array, Assign, AssignIndex, Binary, Block, BoolLit,
                         Break, Call, Cast, CharLit, Continue, ExpStmt,
                         FloatLit, For, Function, GlobalVar, Ident, If, Index,
                         IntLit, LocalVar, Print, ReadVar, Return, StringLit,
                         Unary, Var, While)

LIMITE_PASSOS = 1_000_000


class ErroExecucao(Exception):
    pass


class Char(int):
    """um char e um inteiro (como em C) que se escreve como caracter"""


class _Break(Exception):
    pass


class _Continue(Exception):
    pass


class _Return(Exception):
    def __init__(self, valor):
        self.valor = valor


ESCAPES = {"n": "\n", "t": "\t", "r": "\r", "0": "\0", "\\": "\\", "'": "'", '"': '"'}


def desescapa(s):
    out, i = [], 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            out.append(ESCAPES.get(s[i + 1], s[i + 1]))
            i += 2
        else:
            out.append(s[i])
            i += 1
    return "".join(out)


def converte(v, t):
    """conversao implicita/explicita para o tipo t (como em C)"""
    if t == "int":
        return int(v) if not isinstance(v, float) else int(v)   # trunca
    if t == "double":
        return float(v)
    if t == "char":
        return Char(int(v) % 256)
    if t == "bool":
        return v != 0
    if t == "void":
        return None
    raise ErroExecucao("tipo desconhecido " + str(t))


def mostra(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, Char):
        return chr(v)
    if isinstance(v, float):
        return repr(v)
    return str(v)


def div_c(a, b):
    if b == 0:
        raise ErroExecucao("divisao por zero")
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b >= 0) else -q


class Variavel:
    def __init__(self, tipo, valor, array=False):
        self.tipo, self.valor, self.array = tipo, valor, array


class Interpretador:
    def __init__(self, prog, inputs=()):
        self.funcoes = {d.name: d for d in prog if isinstance(d, Function)}
        self.globais = {}
        self.inputs = list(inputs)
        self.saida = []
        self.passos = 0
        self.escopos = []             # pilha de dicionarios (variaveis locais)
        for d in prog:
            if isinstance(d, GlobalVar):
                self.declara(d.decl, self.globais)

    # ---------- variaveis ----------
    def declara(self, d, tabela):
        if isinstance(d, Var):
            v = converte(self.exp(d.init), d.type) if d.init is not None else converte(0, d.type)
            tabela[d.name] = Variavel(d.type, v)
        elif isinstance(d, Array):
            valores = [converte(self.exp(e), d.type) for e in (d.init or [])]
            valores += [converte(0, d.type)] * (d.size - len(valores))
            tabela[d.name] = Variavel(d.type, valores[:d.size], array=True)

    def procura(self, nome):
        for tabela in reversed(self.escopos[-1] if self.escopos else []):
            if nome in tabela:
                return tabela[nome]
        if nome in self.globais:
            return self.globais[nome]
        raise ErroExecucao("variavel nao declarada: " + nome)

    # ---------- expressoes ----------
    def exp(self, e):
        if isinstance(e, IntLit):
            return e.value
        if isinstance(e, FloatLit):
            return float(e.value)
        if isinstance(e, CharLit):
            return Char(ord(desescapa(e.value[1:-1])))
        if isinstance(e, StringLit):
            return desescapa(e.value[1:-1])
        if isinstance(e, BoolLit):
            return e.value
        if isinstance(e, Ident):
            v = self.procura(e.name)
            return v.valor
        if isinstance(e, Index):
            arr = self.exp(e.array)
            i = self.exp(e.index)
            if not isinstance(arr, list) or not (0 <= i < len(arr)):
                raise ErroExecucao("indice fora do array")
            return arr[i]
        if isinstance(e, Call):
            return self.chama(e.function.name, [self.exp(a) for a in e.args])
        if isinstance(e, Cast):
            return converte(self.exp(e.exp), e.type)
        if isinstance(e, Unary):
            v = self.exp(e.exp)
            if e.op == "!":
                return not v
            if e.op == "-":
                return -v if not isinstance(v, bool) else -int(v)
            return +v if not isinstance(v, bool) else int(v)
        if isinstance(e, Binary):
            if e.op == "&&":
                return bool(self.exp(e.left)) and bool(self.exp(e.right))
            if e.op == "||":
                return bool(self.exp(e.left)) or bool(self.exp(e.right))
            a, b = self.exp(e.left), self.exp(e.right)
            if isinstance(a, bool):
                a = int(a)
            if isinstance(b, bool):
                b = int(b)
            op = e.op
            if op == "+":
                return a + b
            if op == "-":
                return a - b
            if op == "*":
                return a * b
            if op == "/":
                if isinstance(a, float) or isinstance(b, float):
                    if b == 0:
                        raise ErroExecucao("divisao por zero")
                    return a / b
                return div_c(int(a), int(b))
            if op == "%":
                return int(a) - int(b) * div_c(int(a), int(b))
            if op == "==":
                return a == b
            if op == "!=":
                return a != b
            if op == "<":
                return a < b
            if op == "<=":
                return a <= b
            if op == ">":
                return a > b
            if op == ">=":
                return a >= b
        raise ErroExecucao("expressao desconhecida " + repr(e))

    def chama(self, nome, args):
        if nome not in self.funcoes:
            raise ErroExecucao("funcao nao existe: " + nome)
        f = self.funcoes[nome]
        if len(args) != len(f.params):
            raise ErroExecucao("numero de argumentos errado em " + nome)
        tabela = {}
        for ((t, n), v) in zip(f.params, args):
            tabela[n] = Variavel(t, converte(v, t))
        self.escopos.append([tabela])
        if len(self.escopos) > 500:
            raise ErroExecucao("recursao demasiado profunda")
        try:
            self.lista(f.body, novo_escopo=False)
            resultado = None
        except _Return as r:
            resultado = r.valor
        finally:
            self.escopos.pop()
        if f.ret_type == "void" or resultado is None:
            return None
        return converte(resultado, f.ret_type)

    # ---------- instrucoes ----------
    def lista(self, stmts, novo_escopo=True):
        if novo_escopo:
            self.escopos[-1].append({})
        try:
            for s in stmts:
                self.stmt(s)
        finally:
            if novo_escopo:
                self.escopos[-1].pop()

    def atribui(self, nome, valor):
        v = self.procura(nome)
        v.valor = converte(valor, v.tipo)

    def stmt(self, s):
        self.passos += 1
        if self.passos > LIMITE_PASSOS:
            raise ErroExecucao("demasiados passos (ciclo infinito?)")
        if isinstance(s, Block):
            self.lista(s.stmts)
        elif isinstance(s, LocalVar):
            self.declara(s.decl, self.escopos[-1][-1])
        elif isinstance(s, Assign):
            self.atribui(s.name, self.exp(s.exp))
        elif isinstance(s, AssignIndex):
            v = self.procura(s.name)
            i = self.exp(s.index)
            if not (0 <= i < len(v.valor)):
                raise ErroExecucao("indice fora do array")
            v.valor[i] = converte(self.exp(s.exp), v.tipo)
        elif isinstance(s, If):
            if self.exp(s.cond):
                self.lista([s.then])
            elif s.else_ is not None:
                self.lista([s.else_])
        elif isinstance(s, While):
            while self.exp(s.cond):
                try:
                    self.lista([s.body])
                except _Break:
                    break
                except _Continue:
                    pass
        elif isinstance(s, For):
            self.escopos[-1].append({})
            try:
                if s.init is not None:
                    self.stmt(s.init)
                while s.cond is None or self.exp(s.cond):
                    try:
                        self.lista([s.body])
                    except _Break:
                        break
                    except _Continue:
                        pass
                    if s.update is not None:
                        self.stmt(s.update)
            finally:
                self.escopos[-1].pop()
        elif isinstance(s, Return):
            raise _Return(None if s.exp is None else self.exp(s.exp))
        elif isinstance(s, Print):
            self.saida.append(mostra(self.exp(s.exp)))
        elif isinstance(s, ReadVar):
            if not self.inputs:
                raise ErroExecucao("read sem input")
            self.atribui(s.name, self.inputs.pop(0))
        elif isinstance(s, Break):
            raise _Break()
        elif isinstance(s, Continue):
            raise _Continue()
        elif isinstance(s, ExpStmt):
            self.exp(s.exp)
        else:
            raise ErroExecucao("instrucao desconhecida " + repr(s))


def executa(prog, inputs=()):
    """corre main(); devolve (lista de linhas escritas, valor de retorno)
    ou (linhas escritas ate ao erro, 'ERRO: ...')"""
    it = Interpretador.__new__(Interpretador)
    try:
        it.__init__(prog, inputs)
        r = it.chama("main", [])
    except ErroExecucao as e:
        return it.saida if hasattr(it, "saida") else [], "ERRO: " + str(e)
    return it.saida, r

