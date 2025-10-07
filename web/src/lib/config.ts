export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ??
  (process.env.NODE_ENV === "production"
    ? "https://jme-api-staging.herokuapp.com"
    : "http://127.0.0.1:8000");