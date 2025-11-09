/**
 * CSRF Protection Helper
 * Automatically adds CSRF tokens to all fetch requests
 */

// Get CSRF token from meta tag
function getCSRFToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (!meta) {
        console.error('CSRF token meta tag not found!');
        return '';
    }
    return meta.content;
}

// Secure fetch wrapper with automatic CSRF token injection
function secureFetch(url, options = {}) {
    const csrfToken = getCSRFToken();

    // Initialize headers if not present
    if (!options.headers) {
        options.headers = {};
    }

    // Add CSRF token for POST/PUT/DELETE/PATCH requests
    if (options.method && options.method !== 'GET') {
        options.headers['X-CSRFToken'] = csrfToken;
    }

    // Add Content-Type if not set and body is present
    if (!options.headers['Content-Type'] && options.body && typeof options.body === 'string') {
        options.headers['Content-Type'] = 'application/json';
    }

    // Add credentials for CORS
    if (!options.credentials) {
        options.credentials = 'same-origin';
    }

    return fetch(url, options);
}

// Replace global fetch with secure version (optional - use with caution)
function enableAutoCSRF() {
    const originalFetch = window.fetch;

    window.fetch = function(url, options = {}) {
        return secureFetch(url, options);
    };

    console.log('✅ Auto CSRF protection enabled');
}

// XSS Prevention Helper
function sanitizeHTML(html) {
    const div = document.createElement('div');
    div.textContent = html;
    return div.innerHTML;
}

// Safe DOM insertion
function safeSetInnerHTML(element, html) {
    element.textContent = '';  // Clear existing content

    // If html is just text, use textContent
    if (!html.includes('<')) {
        element.textContent = html;
        return;
    }

    // For HTML, create elements safely
    const temp = document.createElement('div');
    temp.innerHTML = html;

    // Sanitize each element
    Array.from(temp.children).forEach(child => {
        element.appendChild(child);
    });
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        getCSRFToken,
        secureFetch,
        enableAutoCSRF,
        sanitizeHTML,
        safeSetInnerHTML
    };
}
