{-# LANGUAGE CPP #-}
{-# LANGUAGE NoRebindableSyntax #-}
{-# OPTIONS_GHC -fno-warn-missing-import-lists #-}
{-# OPTIONS_GHC -w #-}
module Paths_Aula (
    version,
    getBinDir, getLibDir, getDynLibDir, getDataDir, getLibexecDir,
    getDataFileName, getSysconfDir
  ) where


import qualified Control.Exception as Exception
import qualified Data.List as List
import Data.Version (Version(..))
import System.Environment (getEnv)
import Prelude


#if defined(VERSION_base)

#if MIN_VERSION_base(4,0,0)
catchIO :: IO a -> (Exception.IOException -> IO a) -> IO a
#else
catchIO :: IO a -> (Exception.Exception -> IO a) -> IO a
#endif

#else
catchIO :: IO a -> (Exception.IOException -> IO a) -> IO a
#endif
catchIO = Exception.catch

version :: Version
version = Version [1,0] []

getDataFileName :: FilePath -> IO FilePath
getDataFileName name = do
  dir <- getDataDir
  return (dir `joinFileName` name)

getBinDir, getLibDir, getDynLibDir, getDataDir, getLibexecDir, getSysconfDir :: IO FilePath



bindir, libdir, dynlibdir, datadir, libexecdir, sysconfdir :: FilePath
bindir     = "/Users/sousini/Documents/Universidade/MEI/Ano1/Semestre1/MES/strategicProgramming/stack/.stack-work/install/aarch64-osx/acea3def7fe715b99c64e85b90d607a10e59c316f14a2acc021fb1707a86fc80/9.4.5/bin"
libdir     = "/Users/sousini/Documents/Universidade/MEI/Ano1/Semestre1/MES/strategicProgramming/stack/.stack-work/install/aarch64-osx/acea3def7fe715b99c64e85b90d607a10e59c316f14a2acc021fb1707a86fc80/9.4.5/lib/aarch64-osx-ghc-9.4.5/Aula-1.0-15oNCmlxoiq11Zcc8yYXV5"
dynlibdir  = "/Users/sousini/Documents/Universidade/MEI/Ano1/Semestre1/MES/strategicProgramming/stack/.stack-work/install/aarch64-osx/acea3def7fe715b99c64e85b90d607a10e59c316f14a2acc021fb1707a86fc80/9.4.5/lib/aarch64-osx-ghc-9.4.5"
datadir    = "/Users/sousini/Documents/Universidade/MEI/Ano1/Semestre1/MES/strategicProgramming/stack/.stack-work/install/aarch64-osx/acea3def7fe715b99c64e85b90d607a10e59c316f14a2acc021fb1707a86fc80/9.4.5/share/aarch64-osx-ghc-9.4.5/Aula-1.0"
libexecdir = "/Users/sousini/Documents/Universidade/MEI/Ano1/Semestre1/MES/strategicProgramming/stack/.stack-work/install/aarch64-osx/acea3def7fe715b99c64e85b90d607a10e59c316f14a2acc021fb1707a86fc80/9.4.5/libexec/aarch64-osx-ghc-9.4.5/Aula-1.0"
sysconfdir = "/Users/sousini/Documents/Universidade/MEI/Ano1/Semestre1/MES/strategicProgramming/stack/.stack-work/install/aarch64-osx/acea3def7fe715b99c64e85b90d607a10e59c316f14a2acc021fb1707a86fc80/9.4.5/etc"

getBinDir     = catchIO (getEnv "Aula_bindir")     (\_ -> return bindir)
getLibDir     = catchIO (getEnv "Aula_libdir")     (\_ -> return libdir)
getDynLibDir  = catchIO (getEnv "Aula_dynlibdir")  (\_ -> return dynlibdir)
getDataDir    = catchIO (getEnv "Aula_datadir")    (\_ -> return datadir)
getLibexecDir = catchIO (getEnv "Aula_libexecdir") (\_ -> return libexecdir)
getSysconfDir = catchIO (getEnv "Aula_sysconfdir") (\_ -> return sysconfdir)




joinFileName :: String -> String -> FilePath
joinFileName ""  fname = fname
joinFileName "." fname = fname
joinFileName dir ""    = dir
joinFileName dir fname
  | isPathSeparator (List.last dir) = dir ++ fname
  | otherwise                       = dir ++ pathSeparator : fname

pathSeparator :: Char
pathSeparator = '/'

isPathSeparator :: Char -> Bool
isPathSeparator c = c == '/'
