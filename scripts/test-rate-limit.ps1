$url = "http://localhost:8080/v1/scan/test-uuid-load-test"
$limit = 120 # O limite padrão é 100/min, então 120 deve acionar o bloqueio

Write-Host "=== Iniciando Teste de Carga: Rate Limiting ===" -ForegroundColor Cyan
Write-Host "Alvo: $url"
Write-Host "Tentativas: $limit"
Write-Host "------------------------------------------------"

$success = 0
$blocked = 0
$start = Get-Date

for ($i = 1; $i -le $limit; $i++) {
    try {
        $response = Invoke-WebRequest -Uri $url -Method Get -ErrorAction Stop -TimeoutSec 2
        $success++
        Write-Host "[$i/$limit] 200 OK" -ForegroundColor Green
    }
    catch {
        if ($_.Exception.Response.StatusCode -eq 429) {
            $blocked++
            Write-Host "[$i/$limit] 429 TOO MANY REQUESTS (Bloqueado!)" -ForegroundColor Red
        }
        else {
            $code = $_.Exception.Response.StatusCode
            Write-Host "[$i/$limit] $code Erro" -ForegroundColor Yellow
        }
    }
    Start-Sleep -Milliseconds 10 # Rápido o suficiente para estourar o limite
}

Write-Host "`n=== Resultado ===" -ForegroundColor Cyan
Write-Host "Sucessos: $success"
Write-Host "Bloqueios: $blocked"

if ($blocked -gt 0) {
    Write-Host "✅ SUCESSO: Rate Limiting funcionou!" -ForegroundColor Green
} else {
    Write-Host "❌ FALHA: Rate Limiting não ativado (verifique se o Redis está rodando)." -ForegroundColor Red
}