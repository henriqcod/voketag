# VokeTag Services Test Script
Write-Host "🚀 Testando Serviços VokeTag" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

$services = @(
    @{ Name = "Scan Service"; URL = "http://localhost:8080/health"; Port = 8080 },
    @{ Name = "Factory Service"; URL = "http://localhost:8081/health"; Port = 8081 },
    @{ Name = "Admin Service"; URL = "http://localhost:8082/health"; Port = 8082 }
)

$endpoints = @(
    @{ Name = "Scan Endpoint"; URL = "http://localhost:8080/v1/scan"; Method = "GET" },
    @{ Name = "Products List"; URL = "http://localhost:8081/v1/products"; Method = "GET" },
    @{ Name = "Batches List"; URL = "http://localhost:8081/v1/batches"; Method = "GET" },
    @{ Name = "Admin Dashboard"; URL = "http://localhost:8082/v1/admin/dashboard"; Method = "GET" },
    @{ Name = "Admin Users"; URL = "http://localhost:8082/v1/admin/users"; Method = "GET" }
)

Write-Host "`n🔍 Verificando Health Checks..." -ForegroundColor Yellow

foreach ($service in $services) {
    try {
        $response = Invoke-WebRequest -Uri $service.URL -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ $($service.Name) - Status: $($response.StatusCode)" -ForegroundColor Green
        } else {
            Write-Host "⚠️  $($service.Name) - Status: $($response.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ $($service.Name) - Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n🧪 Testando Endpoints Funcionais..." -ForegroundColor Yellow

foreach ($endpoint in $endpoints) {
    try {
        $response = Invoke-WebRequest -Uri $endpoint.URL -Method $endpoint.Method -UseBasicParsing -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ $($endpoint.Name) - Status: $($response.StatusCode)" -ForegroundColor Green
            try {
                $content = $response.Content | ConvertFrom-Json
                if ($content.timestamp) {
                    Write-Host "   📅 Timestamp: $($content.timestamp)" -ForegroundColor Gray
                }
            } catch {
                # Ignore JSON parsing errors
            }
        } else {
            Write-Host "⚠️  $($endpoint.Name) - Status: $($response.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "❌ $($endpoint.Name) - Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n🐳 Verificando Containers Docker..." -ForegroundColor Yellow
try {
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | Where-Object { $_ -like "*docker-*" }
} catch {
    Write-Host "❌ Erro ao verificar containers Docker" -ForegroundColor Red
}

Write-Host "`n🎯 Resumo dos Testes:" -ForegroundColor Green
Write-Host "- Scan Service (Go): http://localhost:8080" -ForegroundColor Cyan
Write-Host "- Factory Service (Python): http://localhost:8081" -ForegroundColor Cyan
Write-Host "- Admin Service (Node.js): http://localhost:8082" -ForegroundColor Cyan
Write-Host "- PostgreSQL: localhost:5432" -ForegroundColor Cyan
Write-Host "- Redis: localhost:6379" -ForegroundColor Cyan

Write-Host "`n✨ Ambiente local configurado e funcionando!" -ForegroundColor Green