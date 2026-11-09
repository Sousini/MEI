
import Data.Char

import Prelude hiding ((<*>), (<$>))

infixl 2 <|>
infixl 3 <*>


type Parser r = String -> [(r, String)]

symbola :: Parser Char
symbola (h:t) = if h == 'a' then [('a', t)] 
                else []

symbol :: Char -> Parser Char
symbol c [] = []
symbol c (h:t) = if h == c then [(c, t)]
                else []

satisfy :: (Char -> Bool) -> Parser Char
satisfy p [] = []
satisfy p (h:t) = if p h then [(h, t)]
                else []


symbol' :: Char -> Parser Char
symbol' c inp = satisfy (== c) inp


token t [] = []
token t inp =   if (take (length t) inp) == t 
                then [(t, drop (length t) inp)]
                else []


-- Combinators

(<|>) :: Parser r -> Parser r -> Parser r
(p <|> q) inp = p inp ++ q inp

pCLoops = token "for"
        <|> token "while"

{-
(p <*> q) inp = [   ( (r, r'), inp'')
                |   (  r     , inp')  <- p inp
                ,   (     r' , inp'') <- q inp'
                ]


pSeqExample =   symbol 'a' <*> symbol 'b' <*> symbol 'c'
           <|>  symbol 'c' <*> symbol 'a'
           
-}

(<*>) :: Parser (a -> b) -> Parser a -> Parser b
(p <*> q) inp = [   (  f r, inp'')
                |   (  f     , inp')  <- p inp
                ,   (    r , inp'') <- q inp'
                ]


(<$>) :: (a -> b) -> Parser a -> Parser b
(f <$> p) inp = [   ( f r, inp')
                |   ( r     , inp')  <- p inp
                ]


succeed :: a -> Parser a
succeed r inp = [( r , inp )] 



pX =  f <$> pA <*> pB
    where f a b = (a, b)

pA =    succeed []
  <|>   f <$> symbol 'a' <*> pA
    where f a b = a:b

pB =    f <$> symbol 'b'
  <|>   g <$> symbol 'b' <*> pB 
  where f a = [a]
        g a b = a:b


int :: Parser String

int =   f <$> satisfy isDigit 
    <|> g <$> satisfy isDigit <*> int
    where f r = [r]
          g v l = v:l


pListInt = f <$> symbol '[' <*> pList <*> symbol ']'
    where f a b c = b

pList = succeed []
     <|> f <$> pNomEmptyList
    where f a = a

pNomEmptyList :: Parser [Int]
pNomEmptyList = f <$> int
            <|> g <$> int <*> symbol ',' <*> pNomEmptyList
            where f a = [read a]
                  g a b c = (read a) : c


--TPC: negative integers!


oneOrMore :: Parser a -> Parser [a]
oneOrMore p = f <$> p
          <|> g <$> p <*> oneOrMore p
          where f a = [a]
                g a b = a:b


is = oneOrMore (symbol 'i')
--digits = oneOrMore (satisfy isDigit)
spaces = oneOrMore (satisfy (== ' '))


zeroOrMore :: Parser a -> Parser [a]
zeroOrMore p = succeed []
            <|> f <$> p <*> zeroOrMore p
            where f a b = a:b


spaces' = zeroOrMore (satisfy (\ x -> elem x [' ','\t','\n']))

sign :: Parser Char
sign =  symbol '+'
    <|> symbol '-'
    <|> succeed ' '

digits :: Parser String
digits = oneOrMore (satisfy isDigit)


integer :: Parser Integer
integer = f <$> sign <*> digits
        where f '-' b = read ('-':b)
              f _   b = read b

separatedBy p s = f <$> p
               <|> g <$> p <*> s <*> separatedBy p s
               where f a = [a]
                     g a b c = a:c 



listOfIntegers = separatedBy integer (symbol'' ';')

followedBy p s = succeed []
               <|> g <$> p <*> s <*> followedBy p s 
               where g a b c = a:c

enclosedBy o p c = f <$> o <*> p <*> c 
                where f a b c = b 



block o i s c = enclosedBy o (followedBy i s) c 

blockInC = block (symbol'' '{')
                 (symbol'' 'i')
                 (symbol'' ';')
                 (symbol'' '}')

lists o i s c = enclosedBy o (separatedBy i s) c 

listOfInteger = lists (symbol'' '[')
                       integer
                      (symbol'' ',')
                      (symbol'' ']')


symbol'' s = f <$> symbol s <*> spaces' 
          where f a b = a

token' t = f <$> token t <*> spaces' 
          where f a b = a

satisfy' p = f <$> satisfy p <*> spaces'
            where f a b = a

integer'  = (\ x _ -> x) <$> integer <*> spaces

-- Language of Arithmetic Expressions


data Exp = Add Exp Exp
         | Mul Exp Exp
         | Val Integer
         deriving Show


pExp :: Parser Exp

pExp = f <$> pTerm
    <|> g <$> pTerm <*> symbol'' '+' <*> pExp
    where f a = a 
          g a b c = Add a c

pTerm = f <$> pFactor
    <|> g <$> pFactor <*> symbol'' '*' <*> pTerm
    where f a = a 
          g a b c = Mul a c

pFactor = f <$> integer'
        <|> g <$> enclosedBy (symbol'' '(')
                              pExp
                             (symbol'' ')')
        where f a = Val a
              g a = a 