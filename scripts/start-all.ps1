<#
.SYNOPSIS
    Inicia todo o ambiente de desenvolvimento VokeTag (Backends + Frontends).
#>

$scriptsDir = $PSScriptRoot

Write-Host "=== 🚀 VokeTag: Iniciando Ambiente Completo ===" -ForegroundColor Cyan

# 1. Iniciar Backends (Docker)
# Executa no processo atual para garantir que o Docker subiu antes de abrir os frontends
Write-Host "`n👉 Passo 1: Iniciando Serviços Backend (Docker)..." -ForegroundColor Yellow
& "$scriptsDir\start-dev.ps1"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erro ao iniciar backends. Verifique o Docker e tente novamente." -ForegroundColor Red
    exit
}

# 2. Iniciar Frontend Principal (Nova Janela)
Write-Host "`n👉 Passo 2: Abrindo Frontend Principal (Porta 3000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-File", "$scriptsDir\start-main-frontend.ps1"

# 3. Iniciar Frontend Factory (Nova Janela)
Write-Host "`n👉 Passo 3: Abrindo Frontend Factory (Porta 3001)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-File", "$scriptsDir\start-factory-frontend.ps1"

# 4. Iniciar Frontend Landing (Nova Janela)
Write-Host "`n👉 Passo 4: Abrindo Frontend Landing (Porta 3002)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-File", "$scriptsDir\start-landing-frontend.ps1"

# 5. Iniciar Frontend Admin (Nova Janela)
Write-Host "`n👉 Passo 5: Abrindo Frontend Admin (Porta 3003)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-File", "$scriptsDir\start-admin-frontend.ps1"

Write-Host "`n✅ Tudo pronto! Mantenha as novas janelas abertas." -ForegroundColor Green
Write-Host "Pressione Enter para fechar este terminal de controle..."
Read-Host