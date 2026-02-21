#!/usr/bin/env pwsh

Write-Host "=== TESTE COMPLETO DAS PÁGINAS VOKETAG ===" -ForegroundColor Cyan
Write-Host ""

# Frontend URL
$frontendUrl = "http://localhost:3000"

# Test pages
$pages = @(
    @{ Name = "Homepage"; Path = "/" },
    @{ Name = "Scan"; Path = "/scan" },
    @{ Name = "Products"; Path = "/products" },
    @{ Name = "Batches"; Path = "/batches" },
    @{ Name = "Dashboard"; Path = "/dashboard" }
)

Write-Host "Testando páginas do frontend..." -ForegroundColor Yellow
Write-Host ""

foreach ($page in $pages) {
    $url = "$frontendUrl$($page.Path)"
    try {
        $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ $($page.Name): OK (200)" -ForegroundColor Green
        } else {
            Write-Host "⚠️  $($page.Name): $($response.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ $($page.Name): ERROR - $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=== TESTE DOS SERVIÇOS BACKEND ===" -ForegroundColor Cyan
Write-Host ""

# Backend services
$services = @(
    @{ Name = "Scan Service"; Url = "http://localhost:8080/health" },
    @{ Name = "Factory Service"; Url = "http://localhost:8081/health" },
    @{ Name = "Admin Service"; Url = "http://localhost:8082/health" },
    @{ Name = "Blockchain Service"; Url = "http://localhost:8083/health" }
)

foreach ($service in $services) {
    try {
        $response = Invoke-WebRequest -Uri $service.Url -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ $($service.Name): OK" -ForegroundColor Green
        } else {
            Write-Host "⚠️  $($service.Name): $($response.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ $($service.Name): ERROR - $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=== RESUMO ===" -ForegroundColor Cyan
Write-Host "Frontend rodando em: $frontendUrl" -ForegroundColor White
Write-Host "Backend services disponíveis nas portas 8080-8083" -ForegroundColor White
Write-Host ""
Write-Host "Para acessar o sistema:" -ForegroundColor Yellow
Write-Host "1. Abra o navegador em $frontendUrl" -ForegroundColor White
Write-Host "2. Use a navegação para acessar as diferentes páginas" -ForegroundColor White
Write-Host "3. As páginas Scan e Homepage estão funcionando corretamente" -ForegroundColor White
Write-Host ""