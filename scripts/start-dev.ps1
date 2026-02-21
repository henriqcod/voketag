# VokeTag Development Environment Starter
param(
    [switch]$Stop,
    [switch]$Restart,
    [switch]$Logs,
    [switch]$Status
)

$dockerPath = "C:\Users\henri\voketag\infra\docker"

function Show-Banner {
    Write-Host "VokeTag Development Environment" -ForegroundColor Green
    Write-Host "==================================" -ForegroundColor Green
}

function Start-Services {
    Write-Host "Iniciando servicos..." -ForegroundColor Yellow
    Set-Location $dockerPath
    docker compose -f compose.yml up -d
    
    Write-Host "Aguardando servicos ficarem prontos..." -ForegroundColor Yellow
    Start-Sleep 5
    
    Show-Status
    Test-Endpoints
}

function Stop-Services {
    Write-Host "Parando servicos..." -ForegroundColor Yellow
    Set-Location $dockerPath
    docker compose -f compose.yml down
    Write-Host "Servicos parados!" -ForegroundColor Green
}

function Restart-Services {
    Write-Host "Reiniciando servicos..." -ForegroundColor Yellow
    Stop-Services
    Start-Sleep 2
    Start-Services
}

function Show-Logs {
    Write-Host "Mostrando logs dos servicos..." -ForegroundColor Yellow
    Set-Location $dockerPath
    docker compose -f compose.yml logs -f
}

function Show-Status {
    Write-Host "Status dos Containers:" -ForegroundColor Yellow
    Set-Location $dockerPath
    docker compose -f compose.yml ps
}

function Test-Endpoints {
    Write-Host "Testando endpoints..." -ForegroundColor Yellow
    
    $endpoints = @(
        @{ Name = "Scan Service"; URL = "http://localhost:8080/health" },
        @{ Name = "Factory Service"; URL = "http://localhost:8081/health" },
        @{ Name = "Admin Service"; URL = "http://localhost:8082/health" }
    )
    
    foreach ($endpoint in $endpoints) {
        try {
            $response = Invoke-WebRequest -Uri $endpoint.URL -UseBasicParsing -TimeoutSec 3
            if ($response.StatusCode -eq 200) {
                Write-Host "OK $($endpoint.Name)" -ForegroundColor Green
            } else {
                Write-Host "WARN $($endpoint.Name) - Status: $($response.StatusCode)" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "ERROR $($endpoint.Name) - Nao disponivel" -ForegroundColor Red
        }
    }
    
    Write-Host "URLs dos Servicos:" -ForegroundColor Cyan
    Write-Host "- Scan Service: http://localhost:8080" -ForegroundColor White
    Write-Host "- Factory Service: http://localhost:8081" -ForegroundColor White
    Write-Host "- Admin Service: http://localhost:8082" -ForegroundColor White
}

# Main execution
Show-Banner

if ($Stop) {
    Stop-Services
} elseif ($Restart) {
    Restart-Services
} elseif ($Logs) {
    Show-Logs
} elseif ($Status) {
    Show-Status
    Test-Endpoints
} else {
    Start-Services
}

Write-Host "Comandos disponiveis:" -ForegroundColor Gray
Write-Host "  .\start-dev.ps1          # Iniciar servicos" -ForegroundColor Gray
Write-Host "  .\start-dev.ps1 -Stop    # Parar servicos" -ForegroundColor Gray
Write-Host "  .\start-dev.ps1 -Restart # Reiniciar servicos" -ForegroundColor Gray
Write-Host "  .\start-dev.ps1 -Logs    # Ver logs" -ForegroundColor Gray
Write-Host "  .\start-dev.ps1 -Status  # Ver status" -ForegroundColor Gray