// API configuration
// Auto-detect API base URL based on environment

function getApiBaseUrl(): string {
  // In production, API is served from the same origin
  if (import.meta.env.PROD) {
    return '';
  }
  
  // In development, check for environment variable first
  const envBackendUrl = import.meta.env.VITE_BACKEND_URL;
  if (envBackendUrl) {
    return envBackendUrl;
  }
  
  // Default to localhost:8000 in development
  // This can be overridden by setting VITE_BACKEND_URL environment variable
  return 'http://localhost:8000';
}

export const API_BASE_URL = getApiBaseUrl();

// Helper function to construct full API URLs
export function getApiUrl(path: string): string {
  // Remove leading slash if present to avoid double slashes
  const cleanPath = path.startsWith('/') ? path.slice(1) : path;
  return `${API_BASE_URL}/${cleanPath}`;
}
