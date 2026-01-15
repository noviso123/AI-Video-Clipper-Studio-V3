@echo off
title AI Video Clipper Launcher
color 0A
cls
echo ========================================================
echo          AJAX AI VIDEO CLIPPER - INICIAR
echo ========================================================
echo.
echo Este e um sistema de linha de comando de alta performance.
echo.
echo Escolha uma opcao:
echo [1] Baixar video do YouTube
echo [2] Usar video do meu PC (Local)
echo.
set /p mode=">> Digite 1 ou 2 e aperte ENTER: "

if "%mode%"=="1" goto YOUTUBE
if "%mode%"=="2" goto LOCAL
goto ERROR

:YOUTUBE
echo.
echo COLE A URL DO YOUTUBE ABAIXO:
set /p url=">> URL: "
echo.
echo --------------------------------------------------------
echo [SISTEMA] Iniciando a IA... (Isso pode demorar um pouco)
echo --------------------------------------------------------
call venv\Scripts\python main.py --url "%url%" --clips 3 --captions --whisper-model tiny --broll --variants --critic
goto END

:LOCAL
echo.
echo ARRASTE O ARQUIVO DE VIDEO PARA CA E APERTE ENTER:
set /p filepath=">> Caminho: "
REM Remover aspas se o usuario colar com aspas
set filepath=%filepath:"=%
echo.
echo --------------------------------------------------------
echo [SISTEMA] Iniciando a IA... (Isso pode demorar um pouco)
echo --------------------------------------------------------
call venv\Scripts\python main.py --file "%filepath%" --clips 3 --captions --whisper-model tiny --broll --variants --critic
goto END

:ERROR
echo.
echo [ERRO] Opcao invalida! Tente novamente.
goto END

:END
echo.
echo ========================================================
echo       PROCESSO FINALIZADO - VERIFIQUE A PASTA 'EXPORTS'
echo ========================================================
pause
