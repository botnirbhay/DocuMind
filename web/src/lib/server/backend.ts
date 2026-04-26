const DEFAULT_BACKEND_URL = "http://127.0.0.1:8000";

export function resolveBackendBaseUrl() {
  const value = process.env.DOCUMIND_API_URL || process.env.NEXT_PUBLIC_DOCUMIND_API_URL || DEFAULT_BACKEND_URL;
  return value.replace(/\/+$/, "");
}
