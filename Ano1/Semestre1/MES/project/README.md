# Parser para a SDVM-Lang

Parser escrito em Haskell com a biblioteca de *parser combinators* das aulas
(`Parser.hs` + apontamentos "Parser Combinators" do prof. João Saraiva).

## Como correr

É preciso o GHC (instalar com o GHCup: https://www.haskell.org/ghcup/).

```
runghc SDVMParser.hs exemplos/factorial          # mostra o programa reconstruído a partir da AST
runghc SDVMParser.hs --ast exemplos/factorial    # mostra a AST
runghc SDVMParser.hs --test exemplos/* testes/*  # testa todos os ficheiros
```

No `ghci`:

```
:load SDVMParser.hs
pExp "1 + 2 * 3"
parseSDVM "int main() { return 0; }"
```

## Organização do ficheiro

1. **Biblioteca de combinators**: `symbol`, `satisfy`, `token`, `succeed`, `<|>`, `<*>`, `<$>`,
   `<*`, `*>`, `<$`, `zeroOrMore`, `oneOrMore`, `optional`, `separatedBy`, `enclosedBy` e `left`.
   Mais dois extra: `check` e `notFollowedBy`.
2. **AST**: tipos `Decl`, `VarDecl`, `Stmt`, `Exp`, `Type`.
3. **Léxico**: espaços, comentários `//` e `/* */`, palavras reservadas, identificadores e literais.
4. **Programa, declarações e funções.**
5. **Instruções**: `if`, `while`, `for`, `return`, `print`, `read`, `break`, `continue`, atribuições e chamadas.
6. **Expressões**: um parser por nível de prioridade, usando o combinador `left` (associatividade à esquerda).
7. **`parseSDVM`**: devolve a AST ou uma mensagem de erro com a linha.
8. **Pretty printer**: reescreve o programa a partir da AST, com parênteses explícitos para se ver a prioridade.
9. **`main`**.

## Testes

- Os 15 exemplos do repositório passam todos.
- O teste faz *round-trip*: parse, depois imprimir, depois parse outra vez, e confirma que a AST é igual.
- A pasta `testes/` tem um programa com casos difíceis e três programas com erros.

## Decisões / problemas encontrados na gramática

1. **Update do `for`.** A gramática diz `[ expression ]`, mas os exemplos usam `i = i + 1`,
   que é uma atribuição, e as expressões da gramática não incluem atribuições.
   Aceitamos atribuição ou expressão.
2. **Cast.** A gramática diz `"(" type ")" expression`. Isso faria
   `(double) a / (double) b` ser lido como `(double)(a / (double) b)`.
   Seguimos o C: o cast aplica-se só ao operando seguinte (`unary`).
3. **`assignment`.** Na gramática, uma alternativa tem `";"` e a outra não.
   Tirámos o `";"` da regra e pomo-lo na instrução, para a atribuição poder ser usada no `for`.
4. **Operadores unários.** A tabela diz que são associativos à direita, por isso aceitamos `- -x` e `!!b`.
5. **Palavras reservadas.** São reconhecidas antes dos identificadores, como pede a especificação.
   `notFollowedBy` garante que `integer` é um identificador e não `int` + `eger`.
6. **Dangling else.** O `else` fica com o `if` mais próximo, como em C.
   Isto acontece porque o `opt` tenta primeiro a alternativa mais longa.
