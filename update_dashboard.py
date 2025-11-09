#!/usr/bin/env python3
"""
Dashboard Redesign Script
Removes sidebar and adds topbar-only navigation with dropdowns
"""

import re

# Read the current dashboard
with open('/Users/mittuharibose/Documents/Mittu/Others/Learn/Algo_learning/scalping-bot/src/dashboard/templates/dashboard.html', 'r') as f:
    content = f.read()

print("✅ Read dashboard.html")

# 1. Add dropdown CSS after topbar__badge section
dropdown_css = """
        /* Logo on Topbar (NEW) */
        .topbar__logo {
            display: flex;
            align-items: center;
            gap: var(--space-3);
            font-weight: 600;
            font-size: var(--text-base);
            color: var(--color-text-primary);
            margin-right: var(--space-6);
        }

        .topbar__logo-icon {
            width: 32px;
            height: 32px;
            background: var(--color-accent-primary);
            color: var(--color-bg-primary);
            border-radius: var(--radius-md);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: var(--text-base);
        }

        /* Dropdown Menu System (NEW) */
        .dropdown {
            position: relative;
            display: inline-block;
        }

        .dropdown__menu {
            position: absolute;
            top: calc(100% + 8px);
            right: 0;
            min-width: 240px;
            background: var(--color-bg-secondary);
            border: 1px solid var(--color-border);
            border-radius: var(--radius-lg);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
            padding: var(--space-2);
            z-index: 1000;
            opacity: 0;
            visibility: hidden;
            transform: translateY(-8px);
            transition: all 200ms cubic-bezier(0.4, 0, 0.2, 1);
        }

        .dropdown__menu.show {
            opacity: 1;
            visibility: visible;
            transform: translateY(0);
        }

        .dropdown__item {
            display: flex;
            align-items: center;
            gap: var(--space-3);
            padding: var(--space-3) var(--space-4);
            color: var(--color-text-secondary);
            text-decoration: none;
            border-radius: var(--radius-md);
            font-size: var(--text-sm);
            transition: all 150ms;
            cursor: pointer;
            border: none;
            background: transparent;
            width: 100%;
            text-align: left;
        }

        .dropdown__item:hover {
            background: var(--color-bg-tertiary);
            color: var(--color-text-primary);
        }

        .dropdown__item.active {
            background: rgba(0, 201, 167, 0.1);
            color: var(--color-accent-primary);
        }

        .dropdown__divider {
            height: 1px;
            background: var(--color-border);
            margin: var(--space-2) 0;
        }

        .dropdown__header {
            padding: var(--space-3) var(--space-4);
            font-size: var(--text-xs);
            font-weight: 600;
            color: var(--color-text-tertiary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        /* Notification Dropdown */
        .notification-dropdown {
            min-width: 360px;
            max-height: 480px;
            overflow-y: auto;
        }

        .notification-item {
            display: flex;
            gap: var(--space-3);
            padding: var(--space-4);
            border-radius: var(--radius-md);
            transition: background 150ms;
            cursor: pointer;
        }

        .notification-item:hover {
            background: var(--color-bg-tertiary);
        }

        .notification-item__icon {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }

        .notification-item__icon--success {
            background: rgba(0, 208, 156, 0.1);
            color: var(--color-success);
        }

        .notification-item__icon--error {
            background: rgba(255, 82, 82, 0.1);
            color: var(--color-error);
        }

        .notification-item__icon--info {
            background: rgba(74, 158, 255, 0.1);
            color: var(--color-info);
        }

        .notification-item__content {
            flex: 1;
            min-width: 0;
        }

        .notification-item__title {
            font-size: var(--text-sm);
            font-weight: 500;
            color: var(--color-text-primary);
            margin-bottom: var(--space-1);
        }

        .notification-item__message {
            font-size: var(--text-xs);
            color: var(--color-text-secondary);
            line-height: 1.4;
        }

        .notification-item__time {
            font-size: var(--text-2xs);
            color: var(--color-text-tertiary);
            margin-top: var(--space-1);
        }

        .notification-empty {
            padding: var(--space-8) var(--space-4);
            text-align: center;
            color: var(--color-text-tertiary);
            font-size: var(--text-sm);
        }

        .notification-footer {
            padding: var(--space-3);
            border-top: 1px solid var(--color-border);
            margin-top: var(--space-2);
        }

        .notification-footer__btn {
            width: 100%;
            padding: var(--space-3);
            background: var(--color-bg-tertiary);
            border: none;
            border-radius: var(--radius-md);
            color: var(--color-accent-primary);
            font-size: var(--text-sm);
            font-weight: 500;
            cursor: pointer;
            transition: all 150ms;
        }

        .notification-footer__btn:hover {
            background: rgba(0, 201, 167, 0.1);
        }

"""

# Find and insert after the Content Area comment
content = re.sub(
    r'(        /\* Content Area \*/)',
    dropdown_css + r'\1',
    content,
    count=1
)

print("✅ Added dropdown CSS")

# 2. Remove sidebar HTML (including closing tag)
# Find the sidebar section and remove it
content = re.sub(
    r'        <!-- Sidebar -->.*?        </aside>\n',
    '',
    content,
    flags=re.DOTALL,
    count=1
)

print("✅ Removed sidebar HTML")

# 3. Update topbar HTML - add logo and replace buttons with dropdowns
old_topbar = r'            <header class="topbar" role="banner">\s*<div class="topbar__left">'

new_topbar_start = '''            <header class="topbar" role="banner">
                <div class="topbar__left">
                    <!-- Logo (NEW) -->
                    <div class="topbar__logo">
                        <div class="topbar__logo-icon">S</div>
                        <span>Scalping Bot</span>
                    </div>'''

content = re.sub(old_topbar, new_topbar_start, content, count=1)

print("✅ Added logo to topbar")

# 4. Replace notification and profile buttons with dropdowns
old_topbar_right = r'(<div class="topbar__right">)[\s\S]*?(</div>\s*</header>)'

new_topbar_right = r'''\1
                    <!-- Notification Dropdown (NEW) -->
                    <div class="dropdown">
                        <button class="topbar__icon-btn" onclick="toggleDropdown('notificationDropdown')" aria-label="Notifications">
                            <i data-lucide="bell" class="icon-18"></i>
                            <span class="topbar__badge" id="notification-count">0</span>
                        </button>
                        <div class="dropdown__menu notification-dropdown" id="notificationDropdown">
                            <div class="dropdown__header">Notifications</div>
                            <div class="notification-empty" id="notificationList">
                                No new notifications
                            </div>
                            <div class="notification-footer">
                                <button class="notification-footer__btn" onclick="window.location.href='/notifications'">
                                    View All Notifications
                                </button>
                            </div>
                        </div>
                    </div>

                    <!-- Profile Dropdown (NEW) -->
                    <div class="dropdown">
                        <button class="topbar__icon-btn" onclick="toggleDropdown('profileDropdown')" aria-label="User Profile">
                            <i data-lucide="user" class="icon-18"></i>
                        </button>
                        <div class="dropdown__menu" id="profileDropdown">
                            <a href="/" class="dropdown__item active">
                                <i data-lucide="layout-dashboard" class="icon-16"></i>
                                <span>Dashboard</span>
                            </a>
                            <a href="/accounts" class="dropdown__item">
                                <i data-lucide="wallet" class="icon-16"></i>
                                <span>Accounts</span>
                            </a>
                            <a href="/strategies" class="dropdown__item">
                                <i data-lucide="brain" class="icon-16"></i>
                                <span>Strategies</span>
                            </a>
                            <a href="/analytics" class="dropdown__item">
                                <i data-lucide="bar-chart-3" class="icon-16"></i>
                                <span>Analytics</span>
                            </a>
                            <div class="dropdown__divider"></div>
                            <a href="/settings" class="dropdown__item">
                                <i data-lucide="settings" class="icon-16"></i>
                                <span>Settings</span>
                            </a>
                            <a href="/implementation-log" class="dropdown__item">
                                <i data-lucide="list-checks" class="icon-16"></i>
                                <span>Implementation Log</span>
                            </a>
                            <a href="/help" class="dropdown__item">
                                <i data-lucide="help-circle" class="icon-16"></i>
                                <span>Help</span>
                            </a>
                        </div>
                    </div>
                \2'''

content = re.sub(old_topbar_right, new_topbar_right, content, flags=re.DOTALL, count=1)

print("✅ Added notification and profile dropdowns")

# 5. Hide hamburger menu (not needed without sidebar)
content = re.sub(
    r'\.hamburger \{',
    r'.hamburger {\n            display: none !important; /* Not needed without sidebar */',
    content,
    count=1
)

print("✅ Hidden hamburger menu")

# 6. Add JavaScript for dropdown functionality before closing </script> tag
dropdown_js = """
        // Dropdown Menu System
        function toggleDropdown(dropdownId) {
            const dropdown = document.getElementById(dropdownId);
            const allDropdowns = document.querySelectorAll('.dropdown__menu');

            // Close all other dropdowns
            allDropdowns.forEach(d => {
                if (d.id !== dropdownId) {
                    d.classList.remove('show');
                }
            });

            // Toggle current dropdown
            dropdown.classList.toggle('show');
        }

        // Close dropdowns when clicking outside
        document.addEventListener('click', function(event) {
            if (!event.target.closest('.dropdown')) {
                document.querySelectorAll('.dropdown__menu').forEach(dropdown => {
                    dropdown.classList.remove('show');
                });
            }
        });

        // Set active menu item based on current page
        function setActiveMenuItem() {
            const currentPath = window.location.pathname;
            document.querySelectorAll('.dropdown__item').forEach(item => {
                if (item.getAttribute('href') === currentPath) {
                    item.classList.add('active');
                } else {
                    item.classList.remove('active');
                }
            });
        }

        // Load notifications
        function loadNotifications() {
            // This will be connected to real API later
            const notifications = [
                {
                    type: 'success',
                    title: 'Trade Executed',
                    message: 'Bought 10 shares of RELIANCE at ₹2,450',
                    time: '2 minutes ago'
                },
                {
                    type: 'info',
                    title: 'Pattern Detected',
                    message: 'Hammer pattern detected on NIFTY50 5m chart',
                    time: '15 minutes ago'
                }
            ];

            const notificationList = document.getElementById('notificationList');
            const notificationCount = document.getElementById('notification-count');

            if (notifications.length === 0) {
                notificationList.innerHTML = '<div class="notification-empty">No new notifications</div>';
                notificationCount.textContent = '0';
                return;
            }

            notificationCount.textContent = notifications.length;

            notificationList.innerHTML = notifications.map(notif => `
                <div class="notification-item">
                    <div class="notification-item__icon notification-item__icon--${notif.type}">
                        <i data-lucide="${notif.type === 'success' ? 'check-circle' : 'info'}" class="icon-16"></i>
                    </div>
                    <div class="notification-item__content">
                        <div class="notification-item__title">${notif.title}</div>
                        <div class="notification-item__message">${notif.message}</div>
                        <div class="notification-item__time">${notif.time}</div>
                    </div>
                </div>
            `).join('');

            // Re-initialize Lucide icons
            if (window.lucide) {
                lucide.createIcons();
            }
        }

        // Initialize on page load
        document.addEventListener('DOMContentLoaded', function() {
            setActiveMenuItem();
            loadNotifications();
        });

"""

# Find the last </script> tag before </body>
content = re.sub(
    r'(    </script>\s*</body>)',
    dropdown_js + r'\1',
    content,
    count=1
)

print("✅ Added dropdown JavaScript")

# Write the updated content
with open('/Users/mittuharibose/Documents/Mittu/Others/Learn/Algo_learning/scalping-bot/src/dashboard/templates/dashboard.html', 'w') as f:
    f.write(content)

print("\n✅ Dashboard redesign complete!")
print("\n📋 Changes made:")
print("  1. Sidebar completely removed")
print("  2. Main content now full-width")
print("  3. Logo added to topbar")
print("  4. Notification dropdown with 'View All' button")
print("  5. Profile dropdown with all navigation items")
print("  6. Hamburger menu hidden")
print("  7. JavaScript for dropdown interactions")
print("\n🚀 Restart the dashboard to see changes!")
