# syntax=docker/dockerfile:1
# HIGH SECURITY FIX: Use specific version tags instead of floating tags
FROM golang:1.22.0-alpine3.19 AS builder

WORKDIR /app

RUN apk add --no-cache git ca-certificates tzdata

COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /scan-service ./cmd

# HIGH SECURITY FIX: Use specific SHA256 digest for distroless image
# distroless/static - read-only root, run: docker run --read-only --tmpfs /tmp ...
FROM gcr.io/distroless/static-debian12:nonroot-amd64@sha256:26f9b99f2463f55f20db19feb4d96eb88b056e0f1be7016bb9296a464a89d772

COPY --from=builder /scan-service /scan-service
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo

USER nonroot:nonroot

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD ["/scan-service", "-healthcheck"]

ENTRYPOINT ["/scan-service"]
