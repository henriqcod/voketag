$landingPath = Resolve-Path "$PSScriptRoot\..\frontend\landing"

Write-Host "=== Iniciando VokeTag Landing Frontend (Porta 3002) ===" -ForegroundColor Cyan
Write-Host "📂 Diretório: $landingPath"

Set-Location $landingPath

if (-not (Test-Path "node_modules")) {
    Write-Host "📦 Instalando dependências (primeira execução)..." -ForegroundColor Yellow
    npm install
}

Write-Host "🚀 Subindo servidor Next.js na porta 3002..." -ForegroundColor Green
Write-Host "Acesse: http://localhost:3002" -ForegroundColor Cyan

# Inicia o Next.js forçando a porta 3002
npm run dev -- -p 3002

if ($LASTEXITCODE -ne 0) {
    Read-Host "❌ Ocorreu um erro. Pressione Enter para sair..."
}
