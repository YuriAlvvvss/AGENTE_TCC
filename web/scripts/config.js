// Configuration for the frontend that can be swapped per environment (dev/staging/prod).
// Set `window.ROSITA_API_BASE_URL` to the full origin (scheme://host:port) of the API.
// Example for local development:
//   window.ROSITA_API_BASE_URL = 'http://127.0.0.1:18500';
// In production, your deployment should serve a config.js with the correct value.

window.ROSITA_API_BASE_URL = window.ROSITA_API_BASE_URL || "";

// Default fetch timeout (ms) for non-streaming requests when no signal is provided.
window.ROSITA_FETCH_TIMEOUT_MS = window.ROSITA_FETCH_TIMEOUT_MS || 15000;
