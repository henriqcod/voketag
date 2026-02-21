$adminPath = Resolve-Path "$PSScriptRoot\..\frontend\admin"

Write-Host "=== Iniciando VokeTag Admin Frontend (Porta 3003) ===" -ForegroundColor Cyan
Write-Host "📂 Diretório: $adminPath"

Set-Location $adminPath

if (-not (Test-Path "node_modules")) {
    Write-Host "📦 Instalando dependências (primeira execução)..." -ForegroundColor Yellow
    npm install
}

Write-Host "🚀 Subindo servidor Next.js na porta 3003..." -ForegroundColor Green
Write-Host "Acesse: http://localhost:3003" -ForegroundColor Cyan

# Inicia o Next.js forçando a porta 3003
npm run dev -- -p 3003

if ($LASTEXITCODE -ne 0) {
    Read-Host "❌ Ocorreu um erro. Pressione Enter para sair..."
}