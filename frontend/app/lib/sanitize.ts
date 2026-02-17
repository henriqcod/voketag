/**
 * XSS Protection - Input Sanitization
 * 
 * IMPORTANT: Never use dangerouslySetInnerHTML
 * All user input should be sanitized before rendering
 */

/**
 * Sanitize HTML string - remove all HTML tags
 */
export function sanitizeHTML(input: string): string {
  return input.replace(/<[^>]*>/g, "");
}

/**
 * Escape HTML special characters
 */
export function escapeHTML(input: string): string {
  const map: Record<string, string> = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#x27;",
    "/": "&#x2F;",
  };
  
  return input.replace(/[&<>"'/]/g, (char) => map[char] || char);
}

/**
 * Validate and sanitize URL to prevent javascript: URLs
 */
export function sanitizeURL(url: string): string {
  const trimmed = url.trim().toLowerCase();
  
  // Block dangerous protocols
  const dangerousProtocols = ["javascript:", "data:", "vbscript:"];
  if (dangerousProtocols.some((protocol) => trimmed.startsWith(protocol))) {
    return "#";
  }
  
  return url;
}

/**
 * Validate email format
 */
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Validate UUID format
 */
export function isValidUUID(uuid: string): boolean {
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  return uuidRegex.test(uuid);
}

/**
 * Type-safe JSON parse with validation
 */
export function safeJSONParse<T>(json: string, validator: (data: unknown) => data is T): T | null {
  try {
    const parsed = JSON.parse(json);
    if (validator(parsed)) {
      return parsed;
    }
    return null;
  } catch {
    return null;
  }
}

/**
 * Validate API response structure
 * Prevents prototype pollution and ensures expected shape
 */
export function validateAPIResponse<T extends Record<string, unknown>>(
  data: unknown,
  expectedKeys: (keyof T)[]
): data is T {
  if (typeof data !== "object" || data === null) {
    return false;
  }
  
  const obj = data as Record<string, unknown>;
  
  // Check for prototype pollution attempts
  if ("__proto__" in obj || "constructor" in obj || "prototype" in obj) {
    return false;
  }
  
  // Validate expected keys exist
  return expectedKeys.every((key) => key in obj);
}
