--
-- Software Maintenance and Evolution
-- 2026/2027
-- University fo Minho
--
-- data types produced by Claude on 12/11/2026
--
-- prompt:
-- give me the haskell data types defining the abstract syntax of the linux bc language
--
-- 

module BCast where

type Name = String          -- POSIX: one lowercase letter; GNU: [a-z][a-z0-9_]*

-- A bc program is a sequence of function definitions and statements
newtype Program = Program [Item]
  deriving (Show, Eq)

data Item
  = Def  FunDef
  | Stmt Stmt
  deriving (Show, Eq)

-- define [void] name(params) { auto ...; statements }
data FunDef = FunDef
  { funVoid   :: Bool            -- GNU extension: define void f(...)
  , funName   :: Name
  , funParams :: [Param]
  , funAutos  :: [Local]         -- the auto declarations, at the start of the body
  , funBody   :: [Stmt]
  } deriving (Show, Eq)

data Param = ScalarParam Name    -- x
           | ArrayParam  Name    -- a[]
  deriving (Show, Eq)

data Local = ScalarLocal Name    -- auto x
           | ArrayLocal  Name    -- auto a[]
  deriving (Show, Eq)

data Stmt
  = SAssign Assign               -- a bare assignment: evaluated, not printed
  | SExpr   Exp                  -- any other expression: evaluated and printed
  | SString String               -- a string: printed
  | SPrint  [PrintItem]          -- GNU: print list
  | SBlock  [Stmt]               -- { statement_list }
  | SIf     Exp Stmt (Maybe Stmt)            -- the else branch is a GNU extension
  | SWhile  Exp Stmt
  | SFor    (Maybe Exp) (Maybe Exp) (Maybe Exp) Stmt  -- GNU: the expressions are optional
  | SBreak
  | SContinue                    -- GNU
  | SReturn (Maybe Exp)          -- return / return (E)
  | SQuit                        -- quit: stops bc when it is read
  | SHalt                        -- GNU: stops bc when it is executed
  | SLimits                      -- GNU pseudo statement
  | SWarranty                    -- GNU pseudo statement
  deriving (Show, Eq)

data PrintItem = PrintStr String | PrintExp Exp
  deriving (Show, Eq)

data Assign = Assign (Maybe BinOp) LValue Exp   -- Nothing: =   Just op: +=, -=, *=, /=, %=, ^=
  deriving (Show, Eq)

data LValue
  = LVar     Name                -- x
  | LIndex   Name Exp            -- a[e]
  | LSpecial SpecialVar          -- scale, ibase, obase, last
  deriving (Show, Eq)

data SpecialVar = Scale | IBase | OBase | Last   -- last (also written ".") is a GNU extension
  deriving (Show, Eq)

data Exp
  = Num    String                -- kept as written: its value depends on ibase (digits 0-9 and A-F)
  | LV     LValue                -- variable, array element or special variable
  | AssignE Assign               -- assignment used as an expression, as in (a = 1)
  | PreInc LValue | PreDec LValue | PostInc LValue | PostDec LValue
  | Neg    Exp
  | Not    Exp                   -- GNU
  | Bin    BinOp Exp Exp
  | Rel    RelOp Exp Exp
  | And    Exp Exp               -- GNU: &&
  | Or     Exp Exp               -- GNU: ||
  | Call   Name [Arg]            -- also the functions of the math library, such as s(x) and c(x)
  | Length Exp                   -- length(e)
  | Sqrt   Exp                   -- sqrt(e)
  | ScaleOf Exp                  -- scale(e): the number of digits after the decimal point
  | Read                         -- GNU: read()
  deriving (Show, Eq)

data Arg = ArgExp Exp | ArgArray Name   -- an expression, or a whole array
  deriving (Show, Eq)

data BinOp = Add | Sub | Mul | Div | Mod | Pow
  deriving (Show, Eq)

data RelOp = Lt | Le | Gt | Ge | Eq' | Ne
  deriving (Show, Eq)



{-
 factorial from the bc manual:
 
define f (x) { if (x <= 1) return (1); return (f(x-1) * x); }

-}

factorial :: Program
factorial = Program
  [ Def (FunDef False "f" [ScalarParam "x"] []
          [ SIf (Rel Le (var "x") (Num "1")) (SReturn (Just (Num "1"))) Nothing
          , SReturn (Just (Bin Mul (Call "f" [ArgExp (Bin Sub (var "x") (Num "1"))])
                                   (var "x")))
          ])
  , Stmt (SExpr (Call "f" [ArgExp (Num "10")]))
  ]
  where var n = LV (LVar n)


--
-- give me a more elaborated bc program in concrete and abstract syntax
--

{- 
/* Fibonacci numbers, the Collatz conjecture and Newton's method */
define fib(n) {
    auto a, b, t, i
    if (n < 2) return (n)
    a = 0
    b = 1
    for (i = 2; i <= n; i++) {
        t = a + b
        a = b
        b = t
    }
    return (b)
}

define sum(a[], n) {
    auto i, s
    for (i = 0; i < n; i++) s += a[i]
    return (s)
}

define collatz(n) {
    auto steps
    while (1) {
        if (n == 1) break
        if (n % 2 == 0) {
            n /= 2
        } else {
            n = 3 * n + 1
        }
        steps += 1
    }
    return (steps)
}

define void show(x) {
    print "value: ", x, "\n"
}

for (k = 0; k < 10; k++) v[k] = fib(k)
show(sum(v[], 10))
collatz(27)
scale = 20
x = 1
for (i = 0; i < 6; i++) x = (x + 2 / x) / 2
x
sqrt(2)
-}

{-
Run with GNU bc 1.07.1, it prints:
value: 88
111
1.41421356237309504880
1.41421356237309504880
-}




-- abbreviations used to keep the abstract syntax readable
var :: Name -> Exp
var n = LV (LVar n)

set :: LValue -> Exp -> Stmt                 -- a bare assignment statement
set l e = SAssign (Assign Nothing l e)

upd :: BinOp -> LValue -> Exp -> Stmt        -- a compound assignment: +=, /=, ...
upd op l e = SAssign (Assign (Just op) l e)

setE :: LValue -> Exp -> Exp                 -- an assignment used as an expression
setE l e = AssignE (Assign Nothing l e)

fib :: FunDef
fib = FunDef False "fib" [ScalarParam "n"]
        [ScalarLocal "a", ScalarLocal "b", ScalarLocal "t", ScalarLocal "i"]
        [ SIf (Rel Lt (var "n") (Num "2")) (SReturn (Just (var "n"))) Nothing
        , set (LVar "a") (Num "0")
        , set (LVar "b") (Num "1")
        , SFor (Just (setE (LVar "i") (Num "2")))
               (Just (Rel Le (var "i") (var "n")))
               (Just (PostInc (LVar "i")))
               (SBlock [ set (LVar "t") (Bin Add (var "a") (var "b"))
                       , set (LVar "a") (var "b")
                       , set (LVar "b") (var "t") ])
        , SReturn (Just (var "b")) ]

sumFun :: FunDef
sumFun = FunDef False "sum" [ArrayParam "a", ScalarParam "n"]
          [ScalarLocal "i", ScalarLocal "s"]
          [ SFor (Just (setE (LVar "i") (Num "0")))
                 (Just (Rel Lt (var "i") (var "n")))
                 (Just (PostInc (LVar "i")))
                 (upd Add (LVar "s") (LV (LIndex "a" (var "i"))))
          , SReturn (Just (var "s")) ]

collatz :: FunDef
collatz = FunDef False "collatz" [ScalarParam "n"] [ScalarLocal "steps"]
  [ SWhile (Num "1")
      (SBlock
        [ SIf (Rel Eq' (var "n") (Num "1")) SBreak Nothing
        , SIf (Rel Eq' (Bin Mod (var "n") (Num "2")) (Num "0"))
              (SBlock [ upd Div (LVar "n") (Num "2") ])
              (Just (SBlock [ set (LVar "n")
                                  (Bin Add (Bin Mul (Num "3") (var "n")) (Num "1")) ]))
        , upd Add (LVar "steps") (Num "1") ])
  , SReturn (Just (var "steps")) ]

showFun :: FunDef
showFun = FunDef True "show" [ScalarParam "x"] []
  [ SPrint [PrintStr "value: ", PrintExp (var "x"), PrintStr "\\n"] ]

program :: Program
program = Program
  [ Def fib, Def sumFun, Def collatz, Def showFun
  , Stmt (SFor (Just (setE (LVar "k") (Num "0")))
               (Just (Rel Lt (var "k") (Num "10")))
               (Just (PostInc (LVar "k")))
               (set (LIndex "v" (var "k")) (Call "fib" [ArgExp (var "k")])))
  , Stmt (SExpr (Call "show" [ArgExp (Call "sum" [ArgArray "v", ArgExp (Num "10")])]))
  , Stmt (SExpr (Call "collatz" [ArgExp (Num "27")]))
  , Stmt (set (LSpecial Scale) (Num "20"))
  , Stmt (set (LVar "x") (Num "1"))
  , Stmt (SFor (Just (setE (LVar "i") (Num "0")))
               (Just (Rel Lt (var "i") (Num "6")))
               (Just (PostInc (LVar "i")))
               (set (LVar "x")
                    (Bin Div (Bin Add (var "x") (Bin Div (Num "2") (var "x"))) (Num "2"))))
  , Stmt (SExpr (var "x"))
  , Stmt (SExpr (Sqrt (Num "2"))) ]

