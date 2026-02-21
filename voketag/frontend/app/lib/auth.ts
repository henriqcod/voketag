/**
 * DEPRECATED: Tokens are now stored in httpOnly cookies by the backend.
 * 
 * CRITICAL SECURITY FIX:
 * - This function is deprecated and should NOT be used
 * - Tokens should NEVER be stored in localStorage (XSS vulnerability)
 * - Use httpOnly cookies managed by the backend instead
 * 
 * @deprecated Use httpOnly cookies instead. Tokens are automatically sent with credentials: 'include'.
 */
export function getToken(): string | null {
  console.warn("DEPRECATED: getToken() should not be used. Tokens are stored in httpOnly cookies.");
  return null;
}
