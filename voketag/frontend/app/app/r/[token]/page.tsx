"use client";

import { useEffect } from "react";
import { useRouter, useParams } from "next/navigation";

/**
 * Short URL redirect handler
 * Redirects from /r/{token} to /verify?token={token}
 * 
 * This enables QR codes to use short URLs like:
 * https://app.voketag.com/r/eyJwcm9kdWN0X2lk...
 * 
 * Which redirect to:
 * https://app.voketag.com/verify?token=eyJwcm9kdWN0X2lk...
 */
export default function ShortURLRedirect() {
  const router = useRouter();
  const params = useParams();
  const token = params.token as string;

  useEffect(() => {
    if (token) {
      // Redirect to verify page with token as query param
      router.replace(`/verify?token=${encodeURIComponent(token)}`);
    } else {
      // No token provided, redirect to home
      router.replace("/");
    }
  }, [token, router]);

  // Show minimal loading state during redirect
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
        <p>Redirecionando...</p>
        <style jsx>{`
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    </div>
  );
}
