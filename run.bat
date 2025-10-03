@echo off
setlocal enabledelayedexpansion

:: Configuration
set SOURCE_DIR=source
set EXECUTABLE=lanceur.py
set VENV_DIR=.venv

:: Vérifier si le dossier de l'environnement virtuel existe
if exist "%VENV_DIR%\Scripts\python.exe" (
    echo Activation de l'environnement Python...
    call %VENV_DIR%\Scripts\activate.bat
    if %errorlevel% equ 0 (
        echo Environnement activé avec succès.
        echo Démarrage du logiciel...
        cd %SOURCE_DIR% || (echo Erreur: Impossible de changer de répertoire vers %SOURCE_DIR% & exit /b 1)
        py %EXECUTABLE%
        if %errorlevel% equ 0 (
            echo Le logiciel s'est arrêté correctement.
        ) else (
            echo Erreur lors du démarrage du logiciel.
        )
    ) else (
        echo Échec de l'activation de l'environnement Python.
    )
) else (
    echo Pas d'environnement virtuel existant. Installation des dépendances...
    if exist "dependence.txt" (
        pip install -r dependence.txt
    ) else (
        echo Le fichier 'dependence.txt' n'existe pas. Aucune dépendance installée.
    )
    echo Démarrage du logiciel sans environnement virtuel...
    cd %SOURCE_DIR% || (echo Erreur: Impossible de changer de répertoire vers %SOURCE_DIR% & exit /b 1)
    py %EXECUTABLE%
    if %errorlevel% equ 0 (
        echo Le logiciel s'est arrêté correctement.
    ) else (
        echo Erreur lors du démarrage du logiciel.
    )
)

echo Fermeture Lanceur