"use client";

export default function OfflinePage() {
  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "2rem",
        fontFamily: "system-ui, -apple-system, sans-serif",
        background: "linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
        color: "#f8fafc",
      }}
    >
      <div
        style={{
          width: 80,
          height: 80,
          borderRadius: "50%",
          background: "rgba(148, 163, 184, 0.2)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          marginBottom: "1.5rem",
        }}
      >
        <svg
          width="40"
          height="40"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path d="M1 1l22 22M9 9a3 3 0 104.24 4.24M15 9a3 3 0 00-4.24-4.24M21 12a9 9 0 00-9-9 9.75 9.75 0 00-6.74 2.74L3 14" />
        </svg>
      </div>
      <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.5rem" }}>
        Você está offline
      </h1>
      <p
        style={{
          fontSize: "0.9375rem",
          color: "#94a3b8",
          textAlign: "center",
          maxWidth: 320,
          lineHeight: 1.6,
        }}
      >
        Verifique sua conexão com a internet e tente novamente para verificar a
        autenticidade de produtos.
      </p>
      <button
        type="button"
        onClick={() => window.location.reload()}
        style={{
          marginTop: "2rem",
          padding: "0.75rem 1.5rem",
          background: "#3b82f6",
          color: "#fff",
          border: "none",
          borderRadius: "0.5rem",
          fontSize: "0.9375rem",
          fontWeight: 600,
          cursor: "pointer",
        }}
      >
        Tentar novamente
      </button>
    </div>
  );
}
