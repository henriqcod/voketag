$factoryPath = Resolve-Path "$PSScriptRoot\..\frontend\factory"

Write-Host "=== Iniciando VokeTag Factory Frontend (Porta 3001) ===" -ForegroundColor Cyan
Write-Host "📂 Diretório: $factoryPath"

Set-Location $factoryPath

if (-not (Test-Path "node_modules")) {
    Write-Host "📦 Instalando dependências (primeira execução)..." -ForegroundColor Yellow
    npm install
}

Write-Host "🚀 Subindo servidor Next.js na porta 3001..." -ForegroundColor Green
Write-Host "Acesse: http://localhost:3001" -ForegroundColor Cyan

# Inicia o Next.js forçando a porta 3001
npm run dev -- -p 3001

if ($LASTEXITCODE -ne 0) {
    Read-Host "❌ Ocorreu um erro. Pressione Enter para sair..."
}
