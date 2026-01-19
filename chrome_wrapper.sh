#!/bin/bash
# Wrapper para lançar o Chrome via Flatpak para o Selenium

if [ "$1" == "--version" ]; then
    flatpak run com.google.Chrome --version
    exit 0
fi

# Passa todos os argumentos recebidos para o flatpak
exec flatpak run com.google.Chrome "$@"
