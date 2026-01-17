# ============================================================
# AI VIDEO CLIPPER - Agente Orquestrador Autônomo (Windows)
# ============================================================
# Este script automatiza todo o setup e execução no Windows.

$ErrorActionPreference = "Stop"

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  AI VIDEO CLIPPER - Orquestrador de IA Autônomo" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

# 1. Verificar Requisitos e Configurar Sistema
Write-Host "[1/5] Verificando requisitos e orquestrando sistema..." -ForegroundColor Yellow

# Verificar privilégios de administrador
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "   ⚠️ Executando sem privilégios de Administrador. Algumas otimizações de sistema podem ser limitadas." -ForegroundColor Gray
}

# Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "   ✅ Python encontrado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Python não encontrado! Por favor, instale Python 3.10+." -ForegroundColor Red
    exit
}

# FFmpeg
$ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
if ($ffmpeg) {
    Write-Host "   ✅ FFmpeg encontrado no sistema." -ForegroundColor Green
} else {
    Write-Host "   ⚠️ FFmpeg não encontrado no PATH. O sistema tentará usar a versão injetada no venv." -ForegroundColor Yellow
}

# Otimização de Firewall
try {
    if ($currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        Write-Host "   🛡️ Configurando exceção de Firewall para porta 5000..." -ForegroundColor Gray
        netsh advfirewall firewall add rule name="AI Video Clipper Web" dir=in action=allow protocol=TCP localport=5000 profile=any | Out-Null
    }
} catch {
    Write-Host "   ⚠️ Falha ao configurar firewall." -ForegroundColor Gray
}

# 2. Configurar Ambiente Virtual
Write-Host "`n[2/5] Configurando ambiente virtual..." -ForegroundColor Yellow
if (-not (Test-Path "venv")) {
    Write-Host "   🔨 Criando novo ambiente virtual (venv)..." -ForegroundColor Gray
    python -m venv venv
    Write-Host "   ✅ Ambiente virtual criado." -ForegroundColor Green
} else {
    Write-Host "   ✅ Ambiente virtual já existe." -ForegroundColor Green
}

# 3. Instalar Dependências
Write-Host "`n[3/5] Instalando dependências (isso pode demorar)..." -ForegroundColor Yellow
& ".\venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
& ".\venv\Scripts\pip.exe" install -r requirements.txt --quiet
Write-Host "   ✅ Dependências instaladas." -ForegroundColor Green

# 4. Configurar Variáveis de Ambiente
Write-Host "`n[4/5] Configurando ambiente (.env)..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "   ✅ Arquivo .env criado a partir do exemplo." -ForegroundColor Green
} else {
    Write-Host "   ✅ Arquivo .env já configurado." -ForegroundColor Green
}

# Garantir diretórios
$dirs = @("temp", "exports", "logs", "src/assets/fonts", "src/assets/overlays")
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# 5. Iniciar Interface Web
Write-Host "`n[5/5] Iniciando Servidor Web..." -ForegroundColor Yellow
Write-Host "   🚀 O servidor será aberto em: http://127.0.0.1:5000" -ForegroundColor Cyan
Write-Host "   Pressione CTRL+C para encerrar.`n" -ForegroundColor Gray

# Abrir navegador automaticamente
Start-Process "http://127.0.0.1:5000"

# Executar App
& ".\venv\Scripts\python.exe" app.py
