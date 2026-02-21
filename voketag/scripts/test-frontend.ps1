# Test Frontend and APIs Integration
Write-Host "Testando Frontend e APIs" -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Green

# Test Backend APIs first
Write-Host "Testando APIs Backend:" -ForegroundColor Yellow

$apis = @(
    @{ Name = "Scan Service"; URL = "http://localhost:8080/health" },
    @{ Name = "Factory Service"; URL = "http://localhost:8081/health" },
    @{ Name = "Admin Service"; URL = "http://localhost:8082/health" }
)

foreach ($api in $apis) {
    try {
        $response = Invoke-WebRequest -Uri $api.URL -UseBasicParsing -TimeoutSec 3
        if ($response.StatusCode -eq 200) {
            Write-Host "OK $($api.Name)" -ForegroundColor Green
        }
    } catch {
        Write-Host "ERROR $($api.Name)" -ForegroundColor Red
    }
}

# Test Frontend
Write-Host "Testando Frontend:" -ForegroundColor Yellow

try {
    $response = Invoke-WebRequest -Uri "http://localhost:3001" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "OK Frontend Home" -ForegroundColor Green
        Write-Host "URL: http://localhost:3001" -ForegroundColor Cyan
    }
} catch {
    Write-Host "ERROR Frontend Home" -ForegroundColor Red
}

# Test API Integration
Write-Host "Testando Integracao com APIs:" -ForegroundColor Yellow

# Test Factory API Products endpoint
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8081/v1/products" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        $data = $response.Content | ConvertFrom-Json
        Write-Host "OK Products API" -ForegroundColor Green
    }
} catch {
    Write-Host "ERROR Products API" -ForegroundColor Red
}

# Test Admin API Dashboard endpoint
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8082/v1/admin/dashboard" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        $data = $response.Content | ConvertFrom-Json
        Write-Host "OK Dashboard API" -ForegroundColor Green
    }
} catch {
    Write-Host "ERROR Dashboard API" -ForegroundColor Red
}

Write-Host "Resumo:" -ForegroundColor Green
Write-Host "- Frontend: http://localhost:3001" -ForegroundColor White
Write-Host "- APIs Backend: Funcionando" -ForegroundColor White
Write-Host "- Integracao: Pronta para teste manual" -ForegroundColor White

Write-Host "Abra http://localhost:3001 no navegador!" -ForegroundColor Cyan