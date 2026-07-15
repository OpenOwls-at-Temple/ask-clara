// Vite env vars for modules that read import.meta.env (rewritten to
// process.env under Jest by babel-plugin-transform-vite-meta-env).
process.env.VITE_API_BASE_URL = "/api";
process.env.VITE_GOOGLE_CLIENT_ID = "test-client-id";

require("@testing-library/jest-dom");
