# Catálogo de code smells da SDVM-Lang e respetivos refactorings

Este catálogo define os *code smells* que a ferramenta deteta em programas SDVM-Lang
e o refactoring que elimina cada um. Os smells foram escolhidos a partir das aulas
(*Source Code Smells* e *Program Refactoring*, 2026/2027): os smells "não OO"
(função longa, lista de parâmetros longa, código duplicado, aninhamento profundo,
números mágicos, estado global mutável, identificadores curtos, condições complexas)
e os smells ao nível das expressões e instruções que se eliminam com refactorings
automáticos (código morto, expressões redundantes, ifs desnecessários, ...).

Há dois grupos:

| Grupo | Smells | Deteção | Refactoring |
|---|---|---|---|
| **A**: automáticos | S01–S16 | automática | automático, preserva o comportamento |
| **D**: só deteção | S17–S25 | automática | precisa de decisões de desenho (nomes, partir funções...), fica para o programador |

## Como está implementado

* **Uma regra por smell.** Cada smell do grupo A é uma função
  `regra(no, ctx) -> (no_novo, excerto)` que levanta `NaoAplica` quando o smell não
  está naquele nó (`python/sdvm/smells.py`). A **mesma regra** é usada para:
  * **detetar**: estratégia *Type-Unifying* `full_tdTU` que percorre a AST e recolhe
    todos os nós onde a regra se aplica;
  * **refatorar**: estratégia *Type-Preserving* `innermost` que substitui cada nó pelo
    `no_novo`, de baixo para cima, até nenhuma regra se aplicar (ponto fixo).

  Assim, tudo o que é detetado no grupo A é eliminado pelo refactoring (os testes
  verificam isto).
* **Regras sobre listas de instruções** (S05 forma 2, S08, S12, S13, S14, S15) aplicam-se
  aos nós que têm listas de instruções: `Block` e `Function` (função `em_lista`).
* **Combinação de refactorings.** Como o `innermost` repete até ao ponto fixo, os
  refactorings combinam-se: `if (x == true) {} else { return !!y; }` passa a
  `if (!x) return y;` (S01 + S10 + S02). Alguns só ficam possíveis depois de outros
  (ex.: uma variável só usada numa variável que foi removida), por isso o processo
  completo repete-se até o programa não mudar (`sdvm/refactor.py`, função `refatora`).
* **Segurança (não mudar o comportamento).** Um refactoring não pode alterar o
  comportamento externo do programa. Para isso:
  * há uma pequena **inferência de tipos** (`sdvm/analise.py`, função `tipo`): por exemplo,
    `x == true` só passa a `x` se `x` for `bool` (com `int x = 2`, `x == true` é falso
    mas `x` é verdadeiro);
  * uma expressão só se pode apagar ou deixar de avaliar se for **pura** (não chama
    funções, porque uma função pode fazer `print`/`read`);
  * blocos com **declarações** nunca são juntos ao bloco de fora (mudaria o âmbito
    das variáveis).

  Assume-se que expressões sem chamadas não têm erros de execução (divisão por zero,
  índice fora do array), que em C são comportamento indefinido.

---

## Grupo A: smells com refactoring automático

### S01: Comparação redundante com booleano
Comparar uma expressão booleana com `true`/`false` é ruído: a expressão já é o booleano.

* **Deteção:** `b == true`, `b != false`, `b == false`, `b != true` (literal de qualquer lado), com `b` do tipo `bool`.
* **Refactoring:** *Simplify boolean expression*: `b == true` → `b`; `b == false` → `!b`.

```c
if (is_even(n) == true) ...          if (is_even(n)) ...
if (flag != true) ...          →     if (!flag) ...
```

### S02: Operador unário redundante
Dupla negação ou `+` unário não mudam o valor e dificultam a leitura.

* **Deteção:** `!!b` (com `b` bool), `- -x` e `+x` (com `x` int/double).
* **Refactoring:** remover os operadores. (`!!x` com `x` int **não** é simplificado: converte para bool.)

```c
bool flag = !!positive(3);     →     bool flag = positive(3);
print(- -total);               →     print(total);
```

### S03: Operação com elemento neutro
* **Deteção:** `x + 0`, `0 + x`, `x - 0`, `x * 1`, `1 * x`, `x / 1`, `0 - x`, com `x` numérico.
* **Refactoring:** remover a operação; `0 - x` → `-x`.
* **Cuidados:** com `char`, `c + 0` é um `int` (escreve 65 em vez de `A`), por isso não se aplica.
  Com `double`, `x + 0` e `0 - x` não se aplicam (mudam o sinal de `-0.0`); `x * 1`, `x / 1` e `x - 0` sim.

```c
total = total + i * 1;         →     total = total + i;
return total + 0;              →     return total;
```

### S04: Cast redundante
* **Deteção:** `(t) e` em que `e` já é do tipo `t`.
* **Refactoring:** remover o cast.

```c
return (int) count;            →     return count;      // count é int
```

### S05: If que devolve um booleano
* **Deteção:** `if (c) return true; else return false;` (ou com `true`/`false` trocados), e a
  forma sem else `if (c) return true; return false;`, com `c` bool.
* **Refactoring:** *Return the condition*: `return c;` (ou `return !c;`).

```c
bool is_even(int n) {                       bool is_even(int n) {
    if (n % 2 == 0) {                           return n % 2 == 0;
        return true;                  →     }
    } else {
        return false;
    }
}
```

### S06: If que atribui um booleano
* **Deteção:** `if (c) x = true; else x = false;` (ou trocados), com `c` bool.
* **Refactoring:** `x = c;` (ou `x = !c;`).

```c
if (n > 0) { result = true; } else { result = false; }    →    result = n > 0;
```

### S07: Condição constante
Uma condição sempre verdadeira ou sempre falsa deixa código que nunca corre (código morto).

* **Deteção:** `if (true)`, `if (false)`, `while (false)`.
* **Refactoring:** ficar só com o ramo que corre; `while (false)` é removido.
  (`while (true)` não é smell, é a forma normal de um ciclo com `break`.)

```c
if (true) { print(sum_to(v)); } else { print(0); }     →     print(sum_to(v));
while (false) { print("loop"); }                        →     (removido)
```

### S08: Código inalcançável
* **Deteção:** instruções depois de `return`, `break` ou `continue` no mesmo bloco
  (ou depois de um `if`/`else` em que os dois ramos terminam).
* **Refactoring:** *Remove dead code*.

```c
return total;                  →     return total;
print("unreachable");
```

### S09: Ramos idênticos
* **Deteção:** `if (c) S else S`, com `c` sem chamadas de funções.
* **Refactoring:** *Consolidate duplicate conditional fragments*: trocar o `if` por `S`.

```c
if (value > 5) { bump(); } else { bump(); }     →     bump();
```

### S10: Ramo vazio
* **Deteção:** `if (c) {} else S`, `if (c) S else {}`, `if (c) {}`.
* **Refactoring:** `if (!c) S`; remover o `else {}`; remover o `if` vazio (se `c` não tiver
  chamadas; se `c` for uma chamada `f()`, fica só `f();`).

```c
if (flag == false) {} else { print("positive"); }     →     if (flag) { print("positive"); }
```
(aqui também entra o S01: `!(flag == false)` → `flag`.)

### S11: Ifs aninhados que podem ser juntos
* **Deteção:** `if (a) { if (b) S }`, sem `else` em nenhum dos dois.
* **Refactoring:** *Consolidate conditional expression*: `if (a && b) S` (o `&&` só avalia `b`
  se `a` for verdadeiro, como antes).

```c
if (is_even(i)) {                          if (is_even(i) && positive(i)) {
    if (positive(i)) {             →           count = count + 1;
        count = count + 1;                 }
    }
}
```

### S12: Else desnecessário depois de return
* **Deteção:** `if (c) { ... return x; } else { R }` (o ramo `then` acaba sempre com
  `return`, `break` ou `continue`).
* **Refactoring:** *Replace nested conditional with guard clauses*: tirar o `else` e pôr `R`
  a seguir ao `if`. Reduz o aninhamento. Se `R` tiver declarações, fica dentro de `{ }`.

```c
if (n < 0) {                               if (n < 0) {
    return -1;                                 return -1;
} else {                                   }
    if (n == 0) {                  →       if (n == 0) {
        return 0;                              return 0;
    } else {                               }
        return 1;                          return 1;
    }
}
```

### S13: Auto-atribuição
* **Deteção:** `x = x;` ou `a[i] = a[i];` (com `i` sem chamadas).
* **Refactoring:** remover a instrução.

### S14: Bloco vazio ou redundante
* **Deteção:** `{ }` solto numa lista de instruções, ou `{ ... }` sem declarações dentro de outro bloco.
* **Refactoring:** remover o bloco vazio / juntar as instruções ao bloco de fora.

```c
{                                  →     print(sign(-5));
    print(sign(-5));                     print(sign(0));
    print(sign(0));
}
{}
```

### S15: Variável local não usada
* **Deteção:** variável local declarada e nunca usada na função.
* **Refactoring:** remover a declaração (só se o valor inicial não chamar funções).

```c
int unused = 5;                →     (removido)
```

### S16: Código morto (função ou variável global não usada)
* **Deteção:** funções que não são alcançáveis a partir de `main` (grafo de chamadas: uma função
  só chamada por outra função morta também está morta) e variáveis globais que nunca são usadas.
  Só se aplica a programas com `main`.
* **Refactoring:** remover a declaração.

---

## Grupo D: smells só detetados

| Código | Smell | Deteção | Refactoring sugerido |
|---|---|---|---|
| S17 | Função longa | mais de 20 instruções | *Extract Function* |
| S18 | Lista de parâmetros longa | 4 ou mais parâmetros | reduzir parâmetros / partir a função |
| S19 | Aninhamento profundo | mais de 3 níveis de `if`/`while`/`for` (um `else if` conta como o mesmo nível) | *Guard clauses*, *Extract Function* |
| S20 | Número mágico | literal numérico fora de {0, 1, 2} dentro de uma função | dar nome ao número (variável global com nome claro) |
| S21 | Código duplicado | `if`/`while`/`for`/bloco com 12 ou mais nós que aparece 2+ vezes (só se reporta a maior cópia) | *Extract Function* |
| S22 | Estado global mutável | função que altera uma variável global | passar por parâmetro / devolver o resultado |
| S23 | Identificador demasiado curto | nome com 1 letra (exceto `i`, `j`, `k`) | *Rename* |
| S24 | Parâmetro não usado | parâmetro que a função nunca usa | *Remove Parameter* (e os argumentos nas chamadas) |
| S25 | Condição complexa | condição com 3 ou mais `&&`/`\|\|` | *Decompose Conditional* (partes em variáveis `bool` com nome) |

Os limites estão no início de `python/sdvm/smells.py` e podem ser ajustados.

---

## Como se testa (`python/tests/test_smells.py`)

1. Um exemplo por smell: é detetado e o refactoring dá o código esperado.
2. Casos em que o refactoring **não** se pode aplicar (tipos errados, chamadas com efeitos, declarações).
3. Nos 15 exemplos da linguagem, em `programas/parser/extra_ok` e nos programas de `programas/smells/`:
   o programa refatorado é aceite pelo parser, já não tem smells S01–S16, refatorar outra
   vez não muda nada, e **faz exatamente o mesmo**: corremos o original e o refatorado com o
   interpretador `sdvm/interp.py` (com vários inputs) e comparamos o output e o valor de retorno.
4. Teste aleatório: geramos 300 programas cheios de smells e verificamos o mesmo.
