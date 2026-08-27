/**
 * AI Game Coach - Frontend Configuration
 * Manages API Base URL resolution for Local Development and Production (Vercel & Render).
 */

const CONFIG = (() => {
    // ── Default Production Backend URL ──────────────────────────────
    // Replace with your deployed Render service URL:
    // e.g., "https://<your-service-name>.onrender.com/api"
    const DEFAULT_PROD_API = "https://ai-game-coach-backend.onrender.com/api";

    /**
     * Resolve the active API base URL.
     * Hierarchy:
     * 1. Window override: window.AI_COACH_API_BASE
     * 2. LocalStorage override: AI_COACH_API_BASE
     * 3. Local development detection (localhost / 127.0.0.1) -> http://localhost:5000/api
     * 4. Same origin if running directly alongside Flask backend
     * 5. Production Render backend URL / Vercel API proxy
     */
    function getApiBase() {
        // 1. Explicit window override
        if (window.AI_COACH_API_BASE) {
            return window.AI_COACH_API_BASE.replace(/\/+$/, "");
        }

        // 2. User/Developer localStorage override
        const localOverride = localStorage.getItem("AI_COACH_API_BASE");
        if (localOverride) {
            return localOverride.replace(/\/+$/, "");
        }

        const hostname = window.location.hostname;
        const port = window.location.port;

        // 3. Local development
        if (hostname === "localhost" || hostname === "127.0.0.1") {
            if (port === "5000") {
                return `${window.location.origin}/api`;
            }
            return "http://localhost:5000/api";
        }

        // 4. If served from same host (e.g. Docker / Monolith)
        if (["5000"].includes(port)) {
            return `${window.location.protocol}//${window.location.hostname}:5000/api`;
        }

        // 5. Production (Vercel, Custom Domain, etc.)
        return DEFAULT_PROD_API;
    }

    /**
     * Check backend connectivity / wake up Render instance (handles free-tier cold starts).
     * @param {function} onStatus - Callback receiving { online, database, message, waking }
     */
    async function checkBackendHealth(onStatus) {
        const apiBase = getApiBase();
        const startTime = Date.now();
        let isSlow = false;

        const slowTimer = setTimeout(() => {
            isSlow = true;
            if (onStatus) {
                onStatus({
                    online: false,
                    waking: true,
                    message: "Waking up cloud server (Render free tier may take ~30s)..."
                });
            }
        }, 2500);

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 45000); // 45s timeout for cold starts

            const res = await fetch(`${apiBase}/health`, {
                signal: controller.signal
            });
            clearTimeout(timeoutId);
            clearTimeout(slowTimer);

            if (res.ok) {
                const data = await res.json();
                if (onStatus) {
                    onStatus({
                        online: true,
                        waking: false,
                        database: data.database || "connected",
                        version: data.version || "2.0.0",
                        elapsed: Date.now() - startTime
                    });
                }
                return true;
            } else {
                throw new Error(`Server returned HTTP ${res.status}`);
            }
        } catch (err) {
            clearTimeout(slowTimer);
            if (onStatus) {
                onStatus({
                    online: false,
                    waking: false,
                    error: err.message,
                    message: "Unable to connect to backend. Please check the API configuration."
                });
            }
            return false;
        }
    }

    return {
        getApiBase,
        checkBackendHealth,
        DEFAULT_PROD_API
    };
})();

// Attach globally
window.CONFIG = CONFIG;
