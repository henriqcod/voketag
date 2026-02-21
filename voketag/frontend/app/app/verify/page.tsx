"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { verifyProduct, reportFraud, type VerificationResponse } from "@/lib/antifraud-api";

function VerifyContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  
  const [loading, setLoading] = useState(true);
  const [result, setResult] = useState<VerificationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showReportForm, setShowReportForm] = useState(false);
  const [reportReason, setReportReason] = useState("");
  const [reportDetails, setReportDetails] = useState("");
  const [reportSubmitting, setReportSubmitting] = useState(false);

  useEffect(() => {
    if (!token) {
      setError("No verification token provided");
      setLoading(false);
      return;
    }

    verifyProduct(token)
      .then(setResult)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [token]);

  const handleReportFraud = async () => {
    if (!result || !reportReason.trim()) return;

    setReportSubmitting(true);
    try {
      await reportFraud(result.verification_id, reportReason, reportDetails);
      alert("Thank you for your report. Our team will investigate.");
      setShowReportForm(false);
    } catch (err) {
      alert("Failed to submit report. Please try again.");
    } finally {
      setReportSubmitting(false);
    }
  };

  if (loading) {
    return <LoadingState />;
  }

  if (error) {
    return <ErrorState message={error} />;
  }

  if (!result) {
    return <ErrorState message="Verification failed" />;
  }

  return (
    <div className="verify-page">
      {/* Header */}
      <header className="verify-header">
        <div className="container">
          <div className="logo">
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
              <path d="M16 4L4 12L16 20L28 12L16 4Z" fill="currentColor" />
              <path d="M4 20L16 28L28 20" stroke="currentColor" strokeWidth="2" />
            </svg>
            <span>VokeTag</span>
          </div>
          <div className="header-badge">Verified Platform</div>
        </div>
      </header>

      {/* Main Content */}
      <main className="verify-main">
        <div className="container">
          {/* Verification Card */}
          <div className={`verification-card status-${result.status}`}>
            {/* Status Badge */}
            <StatusBadge status={result.status} score={result.risk_score} />

            {/* Product Info */}
            {result.product && (
              <div className="product-info">
                <h1>{result.product.name}</h1>
                {result.product.manufactured_at && (
                  <p className="meta">
                    <span className="label">Manufactured:</span>
                    <span className="value">
                      {new Date(result.product.manufactured_at).toLocaleDateString()}
                    </span>
                  </p>
                )}
                <p className="meta">
                  <span className="label">Batch ID:</span>
                  <span className="value">{result.product.batch_id}</span>
                </p>
              </div>
            )}

            {/* Verification Details */}
            <div className="verification-details">
              <div className="detail-row">
                <span className="label">Verification ID</span>
                <span className="value mono">{result.verification_id.substring(0, 16)}...</span>
              </div>
              <div className="detail-row">
                <span className="label">Timestamp</span>
                <span className="value">{new Date(result.timestamp).toLocaleString()}</span>
              </div>
              {result.metadata?.country && (
                <div className="detail-row">
                  <span className="label">Location</span>
                  <span className="value">{result.metadata.country}</span>
                </div>
              )}
              {result.metadata?.total_scans && (
                <div className="detail-row">
                  <span className="label">Total Verifications</span>
                  <span className="value">{result.metadata.total_scans}</span>
                </div>
              )}
            </div>

            {/* Risk Factors (if any) */}
            {result.risk_factors && Object.keys(result.risk_factors).length > 0 && (
              <div className="risk-factors">
                <h3>Detection Factors</h3>
                <ul>
                  {Object.entries(result.risk_factors).map(([factor, weight]) => (
                    <li key={factor}>
                      <span className="factor-name">{formatFactorName(factor)}</span>
                      <span className="factor-weight">+{weight}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Actions */}
            {result.status === "high_risk" && (
              <div className="actions">
                {!showReportForm ? (
                  <button
                    className="btn-report"
                    onClick={() => setShowReportForm(true)}
                  >
                    Report Possible Counterfeit
                  </button>
                ) : (
                  <div className="report-form">
                    <h3>Report Suspicious Product</h3>
                    <select
                      value={reportReason}
                      onChange={(e) => setReportReason(e.target.value)}
                      className="input-select"
                    >
                      <option value="">Select reason...</option>
                      <option value="counterfeit">Suspected counterfeit</option>
                      <option value="damaged">Product damaged/tampered</option>
                      <option value="mismatch">Product doesn't match description</option>
                      <option value="stolen">Suspected stolen goods</option>
                      <option value="other">Other</option>
                    </select>
                    <textarea
                      value={reportDetails}
                      onChange={(e) => setReportDetails(e.target.value)}
                      placeholder="Additional details (optional)..."
                      className="input-textarea"
                      rows={3}
                    />
                    <div className="form-actions">
                      <button
                        className="btn-submit"
                        onClick={handleReportFraud}
                        disabled={!reportReason || reportSubmitting}
                      >
                        {reportSubmitting ? "Submitting..." : "Submit Report"}
                      </button>
                      <button
                        className="btn-cancel"
                        onClick={() => setShowReportForm(false)}
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Security Info */}
          <div className="security-info">
            <div className="info-item">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <path d="M10 2L3 6v6c0 4.418 3.134 7.776 7 9 3.866-1.224 7-4.582 7-9V6l-7-4z" />
              </svg>
              <span>Blockchain-verified authenticity</span>
            </div>
            <div className="info-item">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                <path d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
              <span>Advanced fraud detection</span>
            </div>
            <div className="info-item">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z" />
                <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z" />
              </svg>
              <span>Immutable verification logs</span>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="verify-footer">
        <div className="container">
          <p>© 2026 VokeTag. All rights reserved.</p>
          <div className="footer-links">
            <a href="/privacy">Privacy</a>
            <a href="/terms">Terms</a>
            <a href="/security">Security</a>
          </div>
        </div>
      </footer>

      <style jsx>{`
        .verify-page {
          min-height: 100vh;
          background: linear-gradient(135deg, #0A1F44 0%, #111827 100%);
          color: #fff;
        }

        .verify-header {
          background: rgba(255, 255, 255, 0.05);
          backdrop-filter: blur(10px);
          border-bottom: 1px solid rgba(255, 255, 255, 0.1);
          padding: 1rem 0;
        }

        .container {
          max-width: 800px;
          margin: 0 auto;
          padding: 0 1.5rem;
        }

        .logo {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          font-size: 1.25rem;
          font-weight: 700;
          color: #fff;
        }

        .header-badge {
          display: inline-block;
          padding: 0.25rem 0.75rem;
          background: rgba(37, 99, 235, 0.2);
          border: 1px solid rgba(37, 99, 235, 0.4);
          border-radius: 9999px;
          font-size: 0.75rem;
          font-weight: 600;
          color: #60A5FA;
        }

        .verify-main {
          padding: 3rem 0;
        }

        .verification-card {
          background: rgba(255, 255, 255, 0.05);
          backdrop-filter: blur(20px);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 1rem;
          padding: 2.5rem;
          box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
          margin-bottom: 2rem;
        }

        .status-authentic {
          border-color: rgba(34, 197, 94, 0.3);
          background: linear-gradient(135deg, rgba(34, 197, 94, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
        }

        .status-warning {
          border-color: rgba(251, 191, 36, 0.3);
          background: linear-gradient(135deg, rgba(251, 191, 36, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
        }

        .status-high_risk {
          border-color: rgba(239, 68, 68, 0.3);
          background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
        }

        .product-info {
          margin: 2rem 0;
        }

        .product-info h1 {
          font-size: 2rem;
          font-weight: 700;
          margin-bottom: 1rem;
        }

        .meta {
          display: flex;
          gap: 0.5rem;
          margin-bottom: 0.5rem;
          font-size: 0.875rem;
        }

        .label {
          color: rgba(255, 255, 255, 0.6);
        }

        .value {
          color: #fff;
          font-weight: 500;
        }

        .verification-details {
          background: rgba(0, 0, 0, 0.2);
          border-radius: 0.5rem;
          padding: 1.5rem;
          margin: 1.5rem 0;
        }

        .detail-row {
          display: flex;
          justify-content: space-between;
          padding: 0.75rem 0;
          border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .detail-row:last-child {
          border-bottom: none;
        }

        .mono {
          font-family: 'Courier New', monospace;
          font-size: 0.875rem;
        }

        .risk-factors {
          margin: 1.5rem 0;
          padding: 1.5rem;
          background: rgba(239, 68, 68, 0.1);
          border: 1px solid rgba(239, 68, 68, 0.2);
          border-radius: 0.5rem;
        }

        .risk-factors h3 {
          font-size: 1rem;
          font-weight: 600;
          margin-bottom: 1rem;
          color: #FCA5A5;
        }

        .risk-factors ul {
          list-style: none;
          padding: 0;
          margin: 0;
        }

        .risk-factors li {
          display: flex;
          justify-content: space-between;
          padding: 0.5rem 0;
          font-size: 0.875rem;
        }

        .factor-name {
          text-transform: capitalize;
        }

        .factor-weight {
          color: #FCA5A5;
          font-weight: 600;
        }

        .actions {
          margin-top: 2rem;
        }

        .btn-report {
          width: 100%;
          padding: 0.875rem 1.5rem;
          background: #DC2626;
          color: #fff;
          border: none;
          border-radius: 0.5rem;
          font-size: 1rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }

        .btn-report:hover {
          background: #B91C1C;
          transform: translateY(-1px);
          box-shadow: 0 4px 12px rgba(220, 38, 38, 0.4);
        }

        .report-form {
          background: rgba(0, 0, 0, 0.2);
          padding: 1.5rem;
          border-radius: 0.5rem;
        }

        .report-form h3 {
          font-size: 1rem;
          font-weight: 600;
          margin-bottom: 1rem;
        }

        .input-select,
        .input-textarea {
          width: 100%;
          padding: 0.75rem;
          background: rgba(0, 0, 0, 0.3);
          border: 1px solid rgba(255, 255, 255, 0.2);
          border-radius: 0.375rem;
          color: #fff;
          font-size: 0.875rem;
          margin-bottom: 1rem;
        }

        .input-textarea {
          resize: vertical;
        }

        .form-actions {
          display: flex;
          gap: 0.75rem;
        }

        .btn-submit,
        .btn-cancel {
          flex: 1;
          padding: 0.75rem;
          border: none;
          border-radius: 0.375rem;
          font-size: 0.875rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }

        .btn-submit {
          background: #2563EB;
          color: #fff;
        }

        .btn-submit:hover:not(:disabled) {
          background: #1D4ED8;
        }

        .btn-submit:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .btn-cancel {
          background: rgba(255, 255, 255, 0.1);
          color: #fff;
        }

        .btn-cancel:hover {
          background: rgba(255, 255, 255, 0.15);
        }

        .security-info {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 1rem;
        }

        .info-item {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 1rem;
          background: rgba(255, 255, 255, 0.05);
          border-radius: 0.5rem;
          font-size: 0.875rem;
          color: rgba(255, 255, 255, 0.8);
        }

        .verify-footer {
          border-top: 1px solid rgba(255, 255, 255, 0.1);
          padding: 2rem 0;
          margin-top: 4rem;
        }

        .verify-footer .container {
          display: flex;
          justify-content: space-between;
          align-items: center;
          font-size: 0.875rem;
          color: rgba(255, 255, 255, 0.6);
        }

        .footer-links {
          display: flex;
          gap: 1.5rem;
        }

        .footer-links a {
          color: rgba(255, 255, 255, 0.6);
          text-decoration: none;
          transition: color 0.2s;
        }

        .footer-links a:hover {
          color: #fff;
        }
      `}</style>
    </div>
  );
}

// Status Badge Component
function StatusBadge({ status, score }: { status: string; score: number }) {
  const config = {
    authentic: {
      color: "#22C55E",
      icon: "✓",
      title: "Authentic Product",
      subtitle: "Verified successfully",
    },
    warning: {
      color: "#FBB036",
      icon: "⚠",
      title: "Verification Warning",
      subtitle: "Review recommended",
    },
    high_risk: {
      color: "#EF4444",
      icon: "✕",
      title: "High Risk Detected",
      subtitle: "Suspicious activity flagged",
    },
  };

  const cfg = config[status as keyof typeof config] || config.authentic;

  return (
    <div className="status-badge">
      <div className="badge-icon" style={{ background: cfg.color }}>
        {cfg.icon}
      </div>
      <div className="badge-content">
        <h2>{cfg.title}</h2>
        <p>{cfg.subtitle}</p>
        <span className="risk-score">Risk Score: {score}</span>
      </div>
      <style jsx>{`
        .status-badge {
          display: flex;
          align-items: center;
          gap: 1.5rem;
          padding-bottom: 2rem;
          border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .badge-icon {
          width: 64px;
          height: 64px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 50%;
          font-size: 2rem;
          font-weight: 700;
          color: #fff;
          animation: pulse 2s ease-in-out infinite;
        }

        @keyframes pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.8; transform: scale(1.05); }
        }

        .badge-content h2 {
          font-size: 1.5rem;
          font-weight: 700;
          margin-bottom: 0.25rem;
        }

        .badge-content p {
          font-size: 0.875rem;
          color: rgba(255, 255, 255, 0.7);
          margin-bottom: 0.5rem;
        }

        .risk-score {
          display: inline-block;
          padding: 0.25rem 0.75rem;
          background: rgba(0, 0, 0, 0.3);
          border-radius: 9999px;
          font-size: 0.75rem;
          font-weight: 600;
        }
      `}</style>
    </div>
  );
}

// Loading State Component
function LoadingState() {
  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #0A1F44 0%, #111827 100%)',
    }}>
      <div style={{ textAlign: 'center', color: '#fff' }}>
        <div style={{
          width: '48px',
          height: '48px',
          border: '4px solid rgba(255, 255, 255, 0.1)',
          borderTopColor: '#2563EB',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
          margin: '0 auto 1rem',
        }} />
        <p>Verifying product authenticity...</p>
        <style jsx>{`
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    </div>
  );
}

// Error State Component
function ErrorState({ message }: { message: string }) {
  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #0A1F44 0%, #111827 100%)',
      padding: '2rem',
    }}>
      <div style={{
        maxWidth: '500px',
        padding: '2rem',
        background: 'rgba(239, 68, 68, 0.1)',
        border: '1px solid rgba(239, 68, 68, 0.3)',
        borderRadius: '1rem',
        color: '#fff',
        textAlign: 'center',
      }}>
        <div style={{
          width: '64px',
          height: '64px',
          margin: '0 auto 1rem',
          background: '#DC2626',
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '2rem',
        }}>
          ✕
        </div>
        <h2 style={{ fontSize: '1.5rem', fontWeight: '700', marginBottom: '0.5rem' }}>
          Verification Failed
        </h2>
        <p style={{ color: 'rgba(255, 255, 255, 0.8)' }}>{message}</p>
      </div>
    </div>
  );
}

function formatFactorName(name: string): string {
  return name.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase());
}

export default function VerifyPage() {
  return (
    <Suspense fallback={<LoadingState />}>
      <VerifyContent />
    </Suspense>
  );
}
