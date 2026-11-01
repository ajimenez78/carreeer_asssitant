// Next.js substitutes this public value at build time. Keep credentials backend-only.
export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL || "/api"
).replace(/\/+$/, "");
