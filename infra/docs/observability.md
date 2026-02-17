# Observabilidade – OpenTelemetry, Cloud Trace, Cloud Monitoring

## Configuração GCP

Para exportar traces para Cloud Trace e métricas para Cloud Monitoring:

1. **OTLP Collector** (recomendado): Rode o OpenTelemetry Collector com exporters GCP.
2. **Variáveis de ambiente em produção:**

```
OTEL_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=otelcol:4318
OTEL_SERVICE_NAME=scan-service
```

3. **Cloud Run**: O ambiente gen2 suporta trace automático. Configure o sidecar OTLP ou use o endpoint do Cloud Trace.

## Estrutura de logs (obrigatória)

Todos os serviços devem emitir logs estruturados com:

- `service_name`
- `region`
- `request_id`
- `correlation_id`
- `latency_ms`
