{-# LANGUAGE DeriveDataTypeable #-}
module Let where 

-- Para o uso de Zippers
import Data.Data 
import Data.Generics.Zipper 
-- Para o uso de programação estratégica
import Language.Ztrategic
import Language.StrategicData (StrategicData)

instance StrategicData Let

data Let = Let List Exp
          deriving (Data)

data  List  
      = NestedLet  String Let List
      | Assign     String Exp List
      | EmptyList
           deriving (Data)

data Exp = Add   Exp Exp
         | Sub   Exp Exp
         | Mul   Exp Exp -- novo 
         | Neg   Exp
         | Var   String
         | Const Int
       deriving (Data)



instance Show Let where
       show (Let l e) = "let " ++ aaa ++ "in " ++ show e 
              where a = lines (show l)
                    aa = (head a) : (map ("    " ++) $ tail a)
                    aaa = unlines aa

instance Show List where 
       show (NestedLet s l r)    =  s ++ " = " ++ aaa ++ show r
              where a = lines (show l)
                    aa = (head a) : (map ( take (3 + length s) (repeat ' ') ++) $ tail a)
                    aaa = unlines aa
       show (Assign s e l) =  s ++ " = " ++ show e ++ "\n" ++ show l
       show EmptyList          = ""

instance Show Exp where 
       show (Add a b) = show a ++ " + " ++ show b
       show (Sub a b) = show a ++ " - " ++ show b
       show (Mul a b) = show a ++ " * " ++ show b  -- novo
       show (Neg a  ) = " -(" ++ show a ++ ")"
       show (Var a  ) = a
       show (Const a) = show a


ex1_ = let a = 1 + 0
           b = 0 + 1
      in a + b

ex1 = Let ( Assign "a" (Add (Const 1) (Const 0))
        $   Assign "b" (Add (Const 0) (Const 1))
        $  EmptyList)
       $ (Add (Var "a") (Var "b"))  


ex2_ = let a = b - 16
           c = 8
           w = let  z = a + b
               in   z + b   
           b = (c + 3) - c
       in  c + a - w
ex2 = Let ( Assign "a" (Add (Var "b") (Const (-16)))
           $ Assign "c" (Const 8)
           $ NestedLet "w" ( Let (Assign "z" (Add (Var "a") (Var "b")) EmptyList)
                            $ (Add (Var "z") (Var "b")))
           $ Assign "b" (Sub ((Add (Var "c") (Const 3))) (Var "c"))
             EmptyList)
      $ (Sub (Add (Var "c") (Var "a")) (Var "w"))

ex3_ = let a = b + 0     
           c = 2
           b = c + 3 - c
       in (a + 7) - c  

ex3 = Let ( Assign "a" (Add (Var "b") (Const (0)))
           (Assign "c" (Const 2)
           (Assign "b" (Sub ((Add (Var "c") (Const 3))) (Var "c"))
      EmptyList)))
       (Sub (Add (Var "a") (Const 7)) (Var "c"))

ex4_ = let a = (1 +0) + 0
           b = 0 + 1
      in a + b

ex4 = Let ( Assign "a" (Add (Add (Const 1)( Const 0)) (Const 0))
        $   Assign "b" (Add (Const 0) (Const 1))
        $  EmptyList)
       $ (Add (Var "a") (Var "b"))  

-- 2) 

--incorreto! 
etiquetaUmString :: String -> Maybe String 
etiquetaUmString s = Just ("v_" ++ s)



etiqueta :: Let -> Let
etiqueta l = 
    let lZipper = toZipper l 
        Just lNovo = applyTP (full_buTP step) lZipper 
              where step = idTP `adhocTP` etiquetaUm 
                                `adhocTP` etiquetaList
    in 
    fromZipper lNovo

etiquetaUm :: Exp -> Maybe Exp
etiquetaUm (Var s) = Just (Var ("v_" ++ s))
etiquetaUm x = Just x 

etiquetaList :: List -> Maybe List 
etiquetaList (NestedLet s l r) = Just (NestedLet ("v_" ++ s) l r)
etiquetaList (Assign    s l r) = Just (Assign    ("v_" ++ s) l r)
etiquetaList x                 = Just x 


-- 4) 
optimiza :: Let -> Let
optimiza l = 
    let lZipper = toZipper l 
        Just lNovo = applyTP (full_tdTP step) lZipper 
              where step = idTP `adhocTP` opt
                               --  `adhocTP` etiquetaUm
                               --  `adhocTP` etiquetaList
    in 
    fromZipper lNovo


opt :: Exp -> Maybe Exp
opt (Add x (Const 0)) = Just x 
opt (Add (Const 0) x) = Just x 
opt (Mul x (Const 1)) = Just x 
opt (Mul (Const 1) x) = Just x 
opt x                 = Just x 

-- 6) 

optimizaInnermost :: Let -> Let
optimizaInnermost l = 
    let lZipper = toZipper l 
        Just lNovo = applyTP (innermost step) lZipper 
              where step = failTP `adhocTP` optI

    in 
    fromZipper lNovo


optI :: Exp -> Maybe Exp
optI (Add x (Const 0)) = Just x 
optI (Add (Const 0) x) = Just x 
optI (Mul x (Const 1)) = Just x 
optI (Mul (Const 1) x) = Just x 
optI x                 = Nothing 
