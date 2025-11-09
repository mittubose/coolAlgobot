/**
 * Toast Notification System
 * Provides non-blocking feedback for user actions
 *
 * Usage:
 *   Toast.success('Strategy deployed successfully!');
 *   Toast.error('Failed to connect to Zerodha');
 *   Toast.warning('Market closed - paper trading only');
 *   Toast.info('New update available');
 */

const Toast = {
    success(message, duration = 3000) {
        this.show(message, 'success', duration);
    },

    error(message, duration = 5000) {
        this.show(message, 'error', duration);
    },

    warning(message, duration = 4000) {
        this.show(message, 'warning', duration);
    },

    info(message, duration = 3000) {
        this.show(message, 'info', duration);
    },

    show(message, type, duration) {
        const toast = document.createElement('div');
        toast.className = `toast toast--${type}`;

        const icons = {
            success: 'check-circle',
            error: 'x-circle',
            warning: 'alert-triangle',
            info: 'info'
        };

        toast.innerHTML = `
            <div class="toast__icon">
                <i data-lucide="${icons[type]}" style="width: 20px; height: 20px;"></i>
            </div>
            <div class="toast__content">
                <p class="toast__message">${this.escapeHtml(message)}</p>
            </div>
            <button class="toast__close" onclick="this.parentElement.remove()">
                <i data-lucide="x" style="width: 16px; height: 16px;"></i>
            </button>
        `;

        // Add to container or create one
        let container = document.getElementById('toastContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toastContainer';
            container.className = 'toast-container';
            document.body.appendChild(container);
        }

        container.appendChild(toast);

        // Initialize Lucide icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }

        // Trigger animation
        requestAnimationFrame(() => {
            toast.classList.add('toast--visible');
        });

        // Auto-remove
        const timeoutId = setTimeout(() => {
            toast.classList.remove('toast--visible');
            setTimeout(() => {
                if (toast.parentElement) {
                    toast.remove();
                }
                // Remove container if empty
                if (container.children.length === 0) {
                    container.remove();
                }
            }, 300);
        }, duration);

        // Store timeout ID so we can cancel if user closes manually
        toast.dataset.timeoutId = timeoutId;

        // Clear timeout on manual close
        const closeBtn = toast.querySelector('.toast__close');
        closeBtn.addEventListener('click', () => {
            clearTimeout(timeoutId);
        });
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    // Remove all toasts
    clearAll() {
        const container = document.getElementById('toastContainer');
        if (container) {
            container.remove();
        }
    }
};

// Global CSS for toast system (injected dynamically)
if (typeof document !== 'undefined') {
    const style = document.createElement('style');
    style.textContent = `
        .toast-container {
            position: fixed;
            top: 80px;
            right: 24px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 12px;
            pointer-events: none;
        }

        .toast {
            min-width: 320px;
            max-width: 450px;
            background: var(--color-bg-secondary);
            border: 1px solid var(--color-border);
            border-radius: var(--radius-lg);
            padding: 16px;
            display: flex;
            align-items: center;
            gap: 12px;
            box-shadow:
                0 20px 40px rgba(0, 0, 0, 0.4),
                0 0 0 1px rgba(255, 255, 255, 0.05);
            transform: translateX(calc(100% + 24px));
            opacity: 0;
            transition: all 400ms cubic-bezier(0.4, 0, 0.2, 1);
            pointer-events: auto;
        }

        .toast--visible {
            transform: translateX(0);
            opacity: 1;
        }

        .toast--success {
            border-left: 4px solid var(--color-success);
        }

        .toast--success .toast__icon {
            color: var(--color-success);
        }

        .toast--error {
            border-left: 4px solid var(--color-error);
        }

        .toast--error .toast__icon {
            color: var(--color-error);
        }

        .toast--warning {
            border-left: 4px solid var(--color-warning);
        }

        .toast--warning .toast__icon {
            color: var(--color-warning);
        }

        .toast--info {
            border-left: 4px solid var(--color-info);
        }

        .toast--info .toast__icon {
            color: var(--color-info);
        }

        .toast__icon {
            flex-shrink: 0;
            animation: scaleBounce 500ms cubic-bezier(0.68, -0.55, 0.27, 1.55);
        }

        @keyframes scaleBounce {
            0% { transform: scale(0); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }

        .toast__content {
            flex: 1;
        }

        .toast__message {
            font-size: 14px;
            color: var(--color-text-primary);
            line-height: 1.5;
            margin: 0;
        }

        .toast__close {
            flex-shrink: 0;
            background: none;
            border: none;
            color: var(--color-text-secondary);
            cursor: pointer;
            padding: 4px;
            border-radius: 4px;
            transition: all 150ms;
        }

        .toast__close:hover {
            background: rgba(255, 255, 255, 0.1);
            color: var(--color-text-primary);
        }

        /* Mobile responsive */
        @media (max-width: 768px) {
            .toast-container {
                top: 60px;
                right: 16px;
                left: 16px;
            }

            .toast {
                min-width: auto;
                width: 100%;
            }
        }

        /* Spinner for loading states */
        .spinner {
            width: 14px;
            height: 14px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 0.6s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .btn {
            position: relative;
            overflow: hidden;
        }

        .btn:disabled {
            opacity: 0.7;
            cursor: not-allowed;
        }

        .btn-loading {
            pointer-events: none;
        }
    `;
    document.head.appendChild(style);
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Toast;
}
