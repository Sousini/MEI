-- 1

data Expr = Lit Int
         | Var String
         | Add Expr Expr
         | Sub Expr Expr
         | Mul Expr Expr
         | Let [(String, Expr)] Expr
         deriving (Show, Eq)

-- 2

ex1 :: Expr
ex1 = Let [("a", Add (Lit 3) (Mul (Lit 4) (Lit 5))),
           ("b", Sub (Var "a") (Lit 4))
           ]
           (Add (Var "a") (Mul (Var "b")(Lit 2)))


ex2 :: Expr
ex2 = Let [("a", Add (Lit 3) (Mul (Lit 4) (Lit 5))),
           ("b", Let [("c", Add (Var "b")(Lit 2))]
           (Var "c"))
           ]
           (Add (Var "a") (Mul (Var "b")(Lit 2)))


-- 3

pPrint :: Expr -> String
pPrint (Lit n) = show n
pPrint (Var x) = x
pPrint (Add e1 e2) = pPrint e1 ++ " + " ++ pPrint e2
pPrint (Sub e1 e2) = pPrint e1 ++ " - " ++ pPrint e2
pPrint (Mul e1 e2) = pPrint e1 ++ " * " ++ pPrint e2
pPrint (Let bs body) = "let " ++ formatBindings bs ++ "in " ++ pPrint body
                     where formatBindings [] = ""
                           formatBindings ((name, expr) : rest) =  name ++ " = " ++ pPrint expr ++ "\n" ++ formatBindings rest


-- 4

