#!/usr/bin/env python3
"""
Script to automatically update all dashboard HTML files with consistent top bar
"""

import os
import re
from pathlib import Path

# Top Bar HTML Template
TOPBAR_HTML = '''    <!-- Top Bar -->
    <div class="topbar">
        <div class="topbar-brand">
            <i data-lucide="trending-up" style="width: 24px; height: 24px;"></i>
            <span>Scalping Bot</span>
        </div>

        <nav class="topbar-nav">
            <a href="/" class="nav-link">Dashboard</a>
            <a href="/portfolio" class="nav-link">Portfolio</a>
            <a href="/strategies" class="nav-link">Strategies</a>
            <a href="/analytics" class="nav-link">Analytics</a>
            <a href="/settings" class="nav-link">Settings</a>
        </nav>

        <div class="topbar-actions">
            <select id="topbar-account-selector" class="topbar-select" onchange="switchPortfolio(this.value)">
                <option value="1">Zerodha Main</option>
                <option value="2">Groww Main</option>
            </select>

            <div class="topbar-funds">
                <span class="funds-label">Available</span>
                <span class="funds-value" id="topbar-funds">₹0</span>
            </div>

            <div class="topbar-status">
                <span class="status-dot status-active"></span>
                <span>Active</span>
            </div>

            <button class="topbar-user" onclick="window.location.href='/profile'">
                <i data-lucide="user" style="width: 18px; height: 18px;"></i>
            </button>
        </div>
    </div>

'''

# Top Bar CSS
TOPBAR_CSS = '''
        /* ==================== TOP BAR STYLES ==================== */
        .topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 24px;
            background: var(--color-bg-secondary);
            border-bottom: 1px solid var(--color-border);
            margin-bottom: 24px;
            height: 60px;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .topbar-brand {
            display: flex;
            align-items: center;
            gap: 10px;
            font-weight: 600;
            font-size: 1.1rem;
            color: var(--color-accent-primary);
        }

        .topbar-nav {
            display: flex;
            gap: 4px;
            flex: 1;
            justify-content: center;
        }

        .nav-link {
            padding: 8px 16px;
            text-decoration: none;
            color: var(--color-text-secondary);
            border-radius: 6px;
            transition: all 0.2s;
            font-size: 0.9rem;
        }

        .nav-link:hover {
            background: rgba(0, 201, 167, 0.1);
            color: var(--color-accent-primary);
        }

        .nav-link.active {
            background: rgba(0, 201, 167, 0.15);
            color: var(--color-accent-primary);
            font-weight: 500;
        }

        .topbar-actions {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .topbar-select {
            padding: 6px 12px;
            background: var(--color-bg-tertiary);
            border: 1px solid var(--color-border);
            border-radius: 6px;
            color: var(--color-text-primary);
            font-size: 0.85rem;
            cursor: pointer;
        }

        .topbar-funds {
            display: flex;
            flex-direction: column;
            align-items: flex-end;
        }

        .funds-label {
            font-size: 0.7rem;
            color: var(--color-text-secondary);
            text-transform: uppercase;
        }

        .funds-value {
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--color-success);
        }

        .topbar-status {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 0.85rem;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }

        .status-active { background: var(--color-success); }
        .status-paused { background: #f59e0b; }
        .status-stopped { background: var(--color-error); }

        .topbar-user {
            width: 36px;
            height: 36px;
            background: var(--color-bg-tertiary);
            border: 1px solid var(--color-border);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            color: var(--color-text-primary);
            transition: all 0.2s;
        }

        .topbar-user:hover {
            background: var(--color-accent-primary);
            border-color: var(--color-accent-primary);
            color: var(--color-bg-primary);
        }

        /* Mobile Responsive */
        @media (max-width: 768px) {
            .topbar {
                flex-wrap: wrap;
                height: auto;
                padding: 12px;
            }

            .topbar-nav {
                order: 3;
                width: 100%;
                margin-top: 12px;
                justify-content: flex-start;
                overflow-x: auto;
            }

            .topbar-actions {
                gap: 8px;
            }

            .funds-label,
            .topbar-status {
                display: none;
            }
        }
'''

# Top Bar JavaScript
TOPBAR_JS = '''
        // ==================== TOP BAR FUNCTIONS ====================
        function switchPortfolio(portfolioId) {
            localStorage.setItem('selectedPortfolio', portfolioId);
            if (typeof loadPortfolioData === 'function') {
                loadPortfolioData(portfolioId);
            } else if (typeof loadDashboardData === 'function') {
                loadDashboardData();
            } else {
                window.location.reload();
            }
        }

        async function loadTopBarFunds() {
            try {
                const portfolioId = localStorage.getItem('selectedPortfolio') || '1';
                const response = await fetch(`/api/portfolios/${portfolioId}`);
                const data = await response.json();

                if (data.success && data.portfolio) {
                    const fundsElement = document.getElementById('topbar-funds');
                    if (fundsElement) {
                        const available = data.portfolio.current_value || 0;
                        fundsElement.textContent = `₹${available.toLocaleString('en-IN')}`;
                    }
                }
            } catch (error) {
                console.error('Error loading funds:', error);
            }
        }

        // Initialize top bar on page load
        document.addEventListener('DOMContentLoaded', function() {
            // Restore saved portfolio
            const savedPortfolio = localStorage.getItem('selectedPortfolio') || '1';
            const selector = document.getElementById('topbar-account-selector');
            if (selector) {
                selector.value = savedPortfolio;
            }

            // Mark current page as active
            const currentPath = window.location.pathname;
            document.querySelectorAll('.nav-link').forEach(link => {
                const href = link.getAttribute('href');
                if (href === currentPath || (currentPath === '/' && href === '/')) {
                    link.classList.add('active');
                }
            });

            // Load funds
            loadTopBarFunds();

            // Initialize Lucide icons
            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
        });
'''


def ensure_lucide_script(content):
    """Ensure Lucide icons script is included in head"""
    lucide_script = '<script src="https://unpkg.com/lucide@latest"></script>'

    if lucide_script not in content:
        # Add before </head>
        content = content.replace('</head>', f'    {lucide_script}\n</head>')

    return content


def add_topbar_html(content):
    """Add top bar HTML after <body> tag"""
    # Check if topbar already exists
    if 'class="topbar"' in content:
        print("    ⚠️  Top bar already exists, skipping HTML insertion")
        return content

    # Find <body> tag and insert topbar after it
    body_pattern = r'(<body[^>]*>)'
    replacement = r'\1\n' + TOPBAR_HTML
    content = re.sub(body_pattern, replacement, content, count=1)

    return content


def add_topbar_css(content):
    """Add top bar CSS to style section"""
    # Check if top bar CSS already exists
    if '/* ==================== TOP BAR STYLES ====================' in content:
        print("    ⚠️  Top bar CSS already exists, skipping")
        return content

    # Find </style> tag and insert CSS before it
    style_pattern = r'(</style>)'
    replacement = TOPBAR_CSS + r'\n    \1'
    content = re.sub(style_pattern, replacement, content, count=1)

    return content


def add_topbar_js(content):
    """Add top bar JavaScript before </script> or </body>"""
    # Check if top bar JS already exists
    if 'function switchPortfolio' in content:
        print("    ⚠️  Top bar JS already exists, skipping")
        return content

    # Try to find existing <script> section, or add before </body>
    if '<script>' in content and '</script>' in content:
        # Add to existing script section
        pattern = r'(</script>)'
        replacement = TOPBAR_JS + r'\n    \1'
        content = re.sub(pattern, replacement, content, count=1)
    else:
        # Add new script section before </body>
        pattern = r'(</body>)'
        replacement = f'    <script>{TOPBAR_JS}\n    </script>\n\1'
        content = re.sub(pattern, replacement, content, count=1)

    return content


def update_file(file_path):
    """Update a single HTML file with top bar"""
    print(f"\n📄 Processing: {file_path.name}")

    try:
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Apply updates
        content = ensure_lucide_script(content)
        content = add_topbar_html(content)
        content = add_topbar_css(content)
        content = add_topbar_js(content)

        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"    ✅ Updated successfully")
        return True

    except Exception as e:
        print(f"    ❌ Error: {e}")
        return False


def main():
    """Main function to update all HTML files"""
    print("🚀 Starting Top Bar Update Script")
    print("=" * 60)

    # Get templates directory
    templates_dir = Path(__file__).parent / 'src' / 'dashboard' / 'templates'

    if not templates_dir.exists():
        print(f"❌ Templates directory not found: {templates_dir}")
        return

    # Files to update
    html_files = [
        'portfolio.html',
        'dashboard.html',
        'strategies.html',
        'analytics.html',
        'accounts.html',
        'settings.html',
        'notifications.html',
        'help.html',
        'history.html',
        'profile.html',
        'achievements.html',
        'implementation-log.html',
    ]

    # Track results
    success_count = 0
    fail_count = 0

    # Update each file
    for filename in html_files:
        file_path = templates_dir / filename

        if not file_path.exists():
            print(f"\n⚠️  File not found: {filename}")
            fail_count += 1
            continue

        if update_file(file_path):
            success_count += 1
        else:
            fail_count += 1

    # Summary
    print("\n" + "=" * 60)
    print("📊 Update Summary:")
    print(f"   ✅ Successfully updated: {success_count} files")
    print(f"   ❌ Failed: {fail_count} files")
    print(f"   📁 Total processed: {success_count + fail_count} files")
    print("=" * 60)

    if success_count > 0:
        print("\n✨ Top bar successfully added to all pages!")
        print("🔄 Restart the server to see changes:")
        print("   pkill -f 'python.*run_dashboard.py' && python3 run_dashboard.py")


if __name__ == '__main__':
    main()
