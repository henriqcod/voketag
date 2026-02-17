# syntax=docker/dockerfile:1
FROM golang:1.22-alpine AS builder

WORKDIR /app

RUN apk add --no-cache git ca-certificates tzdata

COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /scan-service ./cmd

# distroless/static - read-only root, run: docker run --read-only --tmpfs /tmp ...
FROM gcr.io/distroless/static-debian12:nonroot

COPY --from=builder /scan-service /scan-service
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo

USER nonroot:nonroot

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD ["/scan-service", "-healthcheck"] || exit 1

ENTRYPOINT ["/scan-service"]
