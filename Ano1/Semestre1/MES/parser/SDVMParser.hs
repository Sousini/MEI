{-
  Parser para a linguagem SDVM-Lang
  Manutencao e Evolucao de Software

  Testar ficheiros (no PowerShell):
     runghc SDVMParser.hs (Get-ChildItem exemplos, testes -File).FullName
  No ghci:
     ghci SDVMParser.hs
     ghci> pExp "1 + 2 * 3"
     ghci> parseFicheiro "exemplos/factorial"
-}

module Main where

import Data.Char
import System.Environment (getArgs)
import Prelude hiding ((<*>), (<$>), (<*), (*>), (<$))

------------------------------------------------------------------------
-- 1. COMBINADORES 
------------------------------------------------------------------------

infixl 3 <|>
infixl 4 <*>, <$>, <*, *>, <$

-- Um parser recebe texto e devolve a lista de resultados possiveis,
-- cada um com o resto do texto por ler. Lista vazia = falhou.
type Parser r = String -> [(r, String)]

-- le um caracter especifico
symbol :: Char -> Parser Char
symbol c []    = []
symbol c (h:t) = if h == c then [(c, t)] else []

-- le um caracter que cumpre uma condicao
satisfy :: (Char -> Bool) -> Parser Char
satisfy p []    = []
satisfy p (h:t) = if p h then [(h, t)] else []

-- le uma palavra exata
token :: String -> Parser String
token t inp = if take (length t) inp == t
              then [(t, drop (length t) inp)]
              else []

-- nao le nada e devolve r
succeed :: a -> Parser a
succeed r inp = [(r, inp)]

-- alternativa: experimenta os dois parsers e junta os resultados
(<|>) :: Parser a -> Parser a -> Parser a
(p <|> q) inp = p inp ++ q inp

-- sequencia: corre p, depois q no resto, e aplica o resultado de p ao de q
(<*>) :: Parser (a -> b) -> Parser a -> Parser b
(p <*> q) inp = [ (f r, inp'') | (f, inp') <- p inp, (r, inp'') <- q inp' ]

-- aplica uma funcao ao resultado do parser
(<$>) :: (a -> b) -> Parser a -> Parser b
(f <$> p) inp = [ (f r, inp') | (r, inp') <- p inp ]

-- sequencia que so guarda o resultado da esquerda
(<*) :: Parser a -> Parser b -> Parser a
p <* q = (\a b -> a) <$> p <*> q

-- sequencia que so guarda o resultado da direita
(*>) :: Parser a -> Parser b -> Parser b
p *> q = (\a b -> b) <$> p <*> q

-- le com p, mas devolve sempre o valor r
(<$) :: r -> Parser a -> Parser r
r <$ p = (\a -> r) <$> p

-- { p }   zero ou mais vezes
zeroOrMore :: Parser a -> Parser [a]
zeroOrMore p = (:) <$> p <*> zeroOrMore p
           <|> succeed []

-- uma ou mais vezes
oneOrMore :: Parser a -> Parser [a]
oneOrMore p = (:) <$> p <*> zeroOrMore p

-- [ p ]   se p falhar, devolve o valor por defeito r
optional :: Parser a -> a -> Parser a
optional p r = p <|> succeed r

-- [ p ]   devolve Just resultado ou Nothing
opt :: Parser a -> Parser (Maybe a)
opt p = Just <$> p <|> succeed Nothing

-- p s p s p ...   (ex: a, b, c)
separatedBy :: Parser a -> Parser b -> Parser [a]
separatedBy p s = (:) <$> p <*> zeroOrMore (s *> p)

-- o p c   e so guarda o p   (ex: ( expressao ))
enclosedBy :: Parser a -> Parser r -> Parser b -> Parser r
enclosedBy o p c = o *> p <* c

-- operadores associativos a esquerda:  a - b - c  =  (a - b) - c
left :: Parser (a -> a -> a) -> Parser a -> Parser a
left op p = junta <$> p <*> zeroOrMore ((,) <$> op <*> p)
  where junta x []            = x
        junta x ((f, y) : rs) = junta (f x y) rs

-- so aceita os resultados de p que cumprem a condicao
check :: (a -> Bool) -> Parser a -> Parser a
check cond p inp = [ (r, rest) | (r, rest) <- p inp, cond r ]

-- sucede (sem ler nada) so se p FALHAR
notFollowedBy :: Parser a -> Parser ()
notFollowedBy p inp = if null (p inp) then [((), inp)] else []

------------------------------------------------------------------------
-- 2. AST (a arvore que o parser constroi)
------------------------------------------------------------------------

type Program = [Decl]

data Decl = GlobalVar VarDecl
          | Function Type String [(Type, String)] [Stmt]
          deriving Show

data Type = TInt | TDouble | TChar | TBool | TVoid
          deriving Show

data VarDecl = Var   Type String (Maybe Exp)              -- int x = 1;
             | Array Type String Integer (Maybe [Exp])    -- int a[3] = {1,2,3};
             deriving Show

data Stmt = Block       [Stmt]
          | LocalVar    VarDecl
          | Assign      String Exp                        -- x = e;
          | AssignIndex String Exp Exp                    -- a[i] = e;
          | If          Exp Stmt (Maybe Stmt)
          | While       Exp Stmt
          | For         (Maybe Stmt) (Maybe Exp) (Maybe Stmt) Stmt
          | Return      (Maybe Exp)
          | Print       Exp
          | ReadVar     String
          | Break
          | Continue
          | ExpStmt     Exp                               -- f(x);
          deriving Show

data Exp = IntLit    Integer
         | FloatLit  String
         | CharLit   String
         | StringLit String
         | BoolLit   Bool
         | Ident     String
         | Index     Exp Exp          -- a[i]
         | Call      Exp [Exp]        -- f(x, y)
         | Unary     String Exp       -- -x   !b
         | Binary    String Exp Exp   -- a + b
         | Cast      Type Exp         -- (double) x
         deriving Show

------------------------------------------------------------------------
-- 3. LEXICO: espacos, comentarios, palavras, numeros, texto
------------------------------------------------------------------------

espaco :: Parser ()
espaco = () <$ satisfy isSpace

comentarioLinha :: Parser ()
comentarioLinha = () <$ (token "//" *> zeroOrMore (satisfy (/= '\n'))
                         <* notFollowedBy (satisfy (/= '\n')))

comentarioBloco :: Parser ()
comentarioBloco = token "/*" *> resto
  where resto = () <$ token "*/"
            <|> notFollowedBy (token "*/") *> satisfy (const True) *> resto

-- salta TODOS os espacos e comentarios
spaces :: Parser ()
spaces = () <$ zeroOrMore lixo <* notFollowedBy lixo
  where lixo = espaco <|> comentarioLinha <|> comentarioBloco

-- le p e salta os espacos que vem a seguir
lexeme :: Parser a -> Parser a
lexeme p = p <* spaces

-- simbolos: ( ) { } ; , + - == ...
sym :: String -> Parser String
sym s = lexeme (token s)

keywords :: [String]
keywords = [ "int", "double", "char", "bool", "void"
           , "if", "else", "while", "for", "break", "continue", "return"
           , "print", "read", "true", "false" ]

letraOuDigito :: Char -> Bool
letraOuDigito c = isAlphaNum c || c == '_'

-- palavra reservada ("int" nao pode ser o inicio de "integer")
kw :: String -> Parser String
kw k = lexeme (token k <* notFollowedBy (satisfy letraOuDigito))

-- IDENTIFIER = [A-Za-z][A-Za-z0-9_]*   e nao pode ser palavra reservada
ident :: Parser String
ident = lexeme (check (`notElem` keywords) nome)
  where nome = (:) <$> satisfy isAlpha <*> zeroOrMore (satisfy letraOuDigito)
               <* notFollowedBy (satisfy letraOuDigito)

digits :: Parser String
digits = oneOrMore (satisfy isDigit) <* notFollowedBy (satisfy isDigit)

-- INTEGER = [0-9]+
pInteger :: Parser Integer
pInteger = lexeme (read <$> digits <* notFollowedBy (symbol '.'))

-- FLOAT = [0-9]+\.[0-9]+([eE][+-]?[0-9]+)?
pFloat :: Parser String
pFloat = lexeme (junta <$> digits <*> token "." <*> digits <*> optional expoente "")
  where junta a b c d    = a ++ b ++ c ++ d
        expoente         = junta3 <$> (token "e" <|> token "E")
                                  <*> optional (token "+" <|> token "-") ""
                                  <*> digits
        junta3 a b c     = a ++ b ++ c

-- um caracter normal ou um escape como \n
caracter :: Char -> Parser String
caracter delim = (\c -> [c])    <$> satisfy (\c -> c /= delim && c /= '\\')
             <|> (\b c -> [b, c]) <$> symbol '\\' <*> satisfy (const True)

-- CHAR = 'a'
pChar :: Parser String
pChar = lexeme (symbol '\'' *> caracter '\'' <* symbol '\'')

-- STRING = "texto"
pString :: Parser String
pString = lexeme (symbol '"' *> (concat <$> zeroOrMore (caracter '"')) <* symbol '"')

------------------------------------------------------------------------
-- 4. PROGRAMA, DECLARACOES E FUNCOES
------------------------------------------------------------------------

-- program ::= { declaration }
pProgram :: Parser Program
pProgram = spaces *> zeroOrMore pDecl

-- declaration ::= variable_declaration | function_definition
pDecl :: Parser Decl
pDecl = GlobalVar <$> pVarDecl
    <|> pFunction

-- type ::= "int" | "double" | "char" | "bool"
pType :: Parser Type
pType = TInt    <$ kw "int"
    <|> TDouble <$ kw "double"
    <|> TChar   <$ kw "char"
    <|> TBool   <$ kw "bool"

-- return_type ::= type | "void"
pRetType :: Parser Type
pRetType = pType
       <|> TVoid <$ kw "void"

-- variable_declaration ::= variable_declaration_core ";"
pVarDecl :: Parser VarDecl
pVarDecl = pVarDeclCore <* sym ";"

-- type IDENTIFIER "[" INTEGER "]" [ "=" array_initializer ]
-- | type IDENTIFIER [ "=" expression ]
pVarDeclCore :: Parser VarDecl
pVarDeclCore = Array <$> pType <*> ident <*> enclosedBy (sym "[") pInteger (sym "]")
                     <*> opt (sym "=" *> pArrayInit)
           <|> Var   <$> pType <*> ident <*> opt (sym "=" *> pExp)

-- array_initializer ::= "{" [ expression { "," expression } ] "}"
pArrayInit :: Parser [Exp]
pArrayInit = enclosedBy (sym "{") (optional (separatedBy pExp (sym ",")) []) (sym "}")

-- function_definition ::= return_type IDENTIFIER "(" [ parameter_list ] ")" block
pFunction :: Parser Decl
pFunction = Function <$> pRetType <*> ident
                     <*> enclosedBy (sym "(") (optional pParams []) (sym ")")
                     <*> pBlock

-- parameter_list ::= parameter { "," parameter }
pParams :: Parser [(Type, String)]
pParams = separatedBy ((,) <$> pType <*> ident) (sym ",")

------------------------------------------------------------------------
-- 5. INSTRUCOES
------------------------------------------------------------------------

-- block ::= "{" { statement } "}"
pBlock :: Parser [Stmt]
pBlock = enclosedBy (sym "{") (zeroOrMore pStmt) (sym "}")

pStmt :: Parser Stmt
pStmt = Block    <$> pBlock
    <|> LocalVar <$> pVarDecl
    <|> pAssign <* sym ";"
    <|> pIf
    <|> pWhile
    <|> pFor
    <|> Return   <$> (kw "return" *> opt pExp <* sym ";")
    <|> Print    <$> (kw "print" *> enclosedBy (sym "(") pExp (sym ")") <* sym ";")
    <|> ReadVar  <$> (kw "read" *> enclosedBy (sym "(") ident (sym ")") <* sym ";")
    <|> Break    <$ kw "break" <* sym ";"
    <|> Continue <$ kw "continue" <* sym ";"
    <|> ExpStmt  <$> pCall <* sym ";"

-- assignment ::= IDENTIFIER "[" expression "]" "=" expression
--              | IDENTIFIER "=" expression
pAssign :: Parser Stmt
pAssign = AssignIndex <$> ident <*> enclosedBy (sym "[") pExp (sym "]") <*> (sym "=" *> pExp)
      <|> Assign      <$> ident <*> (sym "=" *> pExp)

-- if_statement ::= "if" "(" expression ")" statement [ "else" statement ]
pIf :: Parser Stmt
pIf = If <$> (kw "if" *> pCond) <*> pStmt <*> opt (kw "else" *> pStmt)

-- while_statement ::= "while" "(" expression ")" statement
pWhile :: Parser Stmt
pWhile = While <$> (kw "while" *> pCond) <*> pStmt

-- "(" expression ")"
pCond :: Parser Exp
pCond = enclosedBy (sym "(") pExp (sym ")")

-- for_statement ::= "for" "(" [init] ";" [expression] ";" [update] ")" statement
pFor :: Parser Stmt
pFor = For <$> (kw "for" *> sym "(" *> opt pForInit <* sym ";")
           <*> (opt pExp <* sym ";")
           <*> (opt pForUpdate <* sym ")")
           <*> pStmt

-- for_initializer ::= variable_declaration_core | assignment
pForInit :: Parser Stmt
pForInit = LocalVar <$> pVarDeclCore
       <|> pAssign

-- NOTA: a gramatica diz [ expression ], mas os exemplos usam "i = i + 1",
-- que e uma atribuicao. Aceitamos as duas coisas.
pForUpdate :: Parser Stmt
pForUpdate = pAssign
         <|> ExpStmt <$> pExp

------------------------------------------------------------------------
-- 6. EXPRESSOES (da menor para a maior prioridade)
------------------------------------------------------------------------

-- le o operador s e devolve a funcao que constroi o no Binary
op :: String -> Parser (Exp -> Exp -> Exp)
op s = Binary s <$ sym s

-- nivel 1:  ||
pExp :: Parser Exp
pExp = left (op "||") pAnd

-- nivel 2:  &&
pAnd :: Parser Exp
pAnd = left (op "&&") pEquality

-- nivel 3:  ==  !=
pEquality :: Parser Exp
pEquality = left (op "==" <|> op "!=") pComparison

-- nivel 4:  <  <=  >  >=
pComparison :: Parser Exp
pComparison = left (op "<=" <|> op ">=" <|> op "<" <|> op ">") pAdditive

-- nivel 5:  +  -
pAdditive :: Parser Exp
pAdditive = left (op "+" <|> op "-") pMultiplicative

-- nivel 6:  *  /  %
pMultiplicative :: Parser Exp
pMultiplicative = left (op "*" <|> op "/" <|> op "%") pUnary

-- nivel 7:  unary ::= [ "+" | "-" | "!" ] postfix
pUnary :: Parser Exp
pUnary = Unary <$> (sym "+" <|> sym "-" <|> sym "!") <*> pUnary
     <|> pPostfix

-- nivel 8:  postfix ::= primary "[" expression "]" | function_call | primary
pPostfix :: Parser Exp
pPostfix = Index <$> pPrimary <*> enclosedBy (sym "[") pExp (sym "]")
       <|> pCall
       <|> pPrimary

-- function_call ::= primary "(" [ argument_list ] ")"
pCall :: Parser Exp
pCall = Call <$> pPrimary <*> enclosedBy (sym "(") (optional pArgs []) (sym ")")

-- argument_list ::= expression { "," expression }
pArgs :: Parser [Exp]
pArgs = separatedBy pExp (sym ",")

-- primary ::= INTEGER | FLOAT | CHAR | STRING | "true" | "false" | IDENTIFIER
--           | "(" type ")" expression | "(" expression ")"
-- NOTA: no cast usamos pUnary (e nao pExp), como em C, para que
-- (double) a / b  seja  ((double) a) / b
pPrimary :: Parser Exp
pPrimary = FloatLit  <$> pFloat
       <|> IntLit    <$> pInteger
       <|> CharLit   <$> pChar
       <|> StringLit <$> pString
       <|> BoolLit True  <$ kw "true"
       <|> BoolLit False <$ kw "false"
       <|> Ident     <$> ident
       <|> Cast      <$> enclosedBy (sym "(") pType (sym ")") <*> pUnary
       <|> enclosedBy (sym "(") pExp (sym ")")

------------------------------------------------------------------------
-- 7. CORRER O PARSER
------------------------------------------------------------------------

-- fica com a primeira arvore que leu o texto TODO (resto = "")
parseSDVM :: String -> Maybe Program
parseSDVM src = case [ p | (p, "") <- pProgram src ] of
                  (p:_) -> Just p
                  []    -> Nothing

-- para usar no ghci:  parseFicheiro "exemplos/factorial"
parseFicheiro :: FilePath -> IO ()
parseFicheiro f = do
  src <- readFile f
  case parseSDVM src of
    Just p  -> mapM_ print p
    Nothing -> putStrLn "Erro de sintaxe"

-- runghc SDVMParser.hs ficheiro1 ficheiro2 ...   -> diz OK ou ERRO para cada um
main :: IO ()
main = do
  ficheiros <- getArgs
  mapM_ testar ficheiros

testar :: FilePath -> IO ()
testar f = do
  src <- readFile f
  case parseSDVM src of
    Just _  -> putStrLn ("OK     " ++ f)
    Nothing -> putStrLn ("ERRO   " ++ f)