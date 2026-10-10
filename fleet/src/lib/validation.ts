export function normalizeEmail(value: string): string {
  return value.trim().toLowerCase();
}

// Deliberately simple: the real check is that the magic link arrives.
export function isValidEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value) && value.length <= 254;
}

export function normalizeName(value: string): string {
  return value.trim().replace(/\s+/g, " ");
}

export function isValidName(value: string): boolean {
  const n = normalizeName(value);
  return n.length >= 2 && n.length <= 200;
}

/** 6-digit code from the login e-mail; tolerates spaces typed by the user. */
export function normalizeOtp(value: string): string {
  return value.replace(/\s+/g, "");
}

export function isValidOtp(value: string): boolean {
  return /^\d{6}$/.test(value);
}

/**
 * Only allow redirects to a local path, never to another site
 * ("//evil.com", "https://evil.com", "/\\evil.com" are rejected).
 */
export function safeNextPath(next: string | null | undefined, fallback = "/"): string {
  if (!next || !next.startsWith("/") || next.startsWith("//") || next.startsWith("/\\")) {
    return fallback;
  }
  return next;
}
