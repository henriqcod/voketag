$mainPath = Resolve-Path "$PSScriptRoot\..\frontend\app"

Write-Host "=== Iniciando VokeTag Main Frontend (Porta 3000) ===" -ForegroundColor Cyan
Write-Host "📂 Diretório: $mainPath"

Set-Location $mainPath

if (-not (Test-Path "node_modules")) {
    Write-Host "📦 Instalando dependências (primeira execução)..." -ForegroundColor Yellow
    npm install
}

Write-Host "🚀 Subindo servidor Next.js na porta 3000..." -ForegroundColor Green
Write-Host "Acesse: http://localhost:3000" -ForegroundColor Cyan

# Inicia o Next.js na porta padrão 3000
npm run dev

if ($LASTEXITCODE -ne 0) {
    Read-Host "❌ Ocorreu um erro. Pressione Enter para sair..."
}