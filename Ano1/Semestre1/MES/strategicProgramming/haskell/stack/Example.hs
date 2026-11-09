{-# LANGUAGE DeriveDataTypeable #-}
module Example where 

-- Para o uso de Zippers
import Data.Data 
import Data.Generics.Zipper 
-- Para o uso de programação estratégica
import Language.Ztrategic
import Language.StrategicData (StrategicData)

instance StrategicData Int
instance StrategicData a => StrategicData [a]


alteraListaS :: [Int] -> [Int]
alteraListaS lista = 
    let listaZipper = toZipper lista 
        Just listaNova = applyTP (full_tdTP step) listaZipper 
              where step = idTP `adhocTP` alteraDois 
    in 
    fromZipper listaNova

alteraDois :: Int -> Maybe Int 
alteraDois 2 = Just 12
alteraDois x = Just x



