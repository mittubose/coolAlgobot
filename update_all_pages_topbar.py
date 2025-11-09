#!/usr/bin/env python3
"""
Update ALL dashboard pages to topbar-only design
Removes sidebar and adds topbar with dropdowns for all HTML templates
"""

import os
import re
from pathlib import Path

# Template directory
TEMPLATE_DIR = '/Users/mittuharibose/Documents/Mittu/Others/Learn/Algo_learning/scalping-bot/src/dashboard/templates'

# Files to update (excluding dashboard.html which is already done)
FILES_TO_UPDATE = [
    'strategies.html',
    'analytics.html',
    'accounts.html',
    'settings.html',
    'notifications.html',
    'help.html',
    'implementation-log.html',
    'history.html',
    'profile.html',
    'achievements.html'
]

def update_file(filepath):
    """Update a single HTML file to topbar-only design"""
    print(f"\n{'='*60}")
    print(f"Processing: {os.path.basename(filepath)}")
    print(f"{'='*60}")

    with open(filepath, 'r') as f:
        content = f.read()

    original_content = content
    changes_made = []

    # 1. Hide sidebar in CSS (if <style> tag exists)
    if '<style>' in content:
        # Check if sidebar hiding already exists
        if '.sidebar {' in content and 'display: none' not in content:
            content = re.sub(
                r'(\.sidebar\s*\{[^}]*)\}',
                r'\1\n            display: none !important;\n        }',
                content,
                flags=re.DOTALL
            )
            changes_made.append("✓ Hidden sidebar in CSS")

        # Update main content margin
        if '.main {' in content:
            content = re.sub(
                r'(\.main\s*\{[^}]*?)margin-left:\s*\d+px;',
                r'\1margin-left: 0;',
                content,
                flags=re.DOTALL
            )
            changes_made.append("✓ Updated .main margin-left to 0")

    # 2. Remove sidebar HTML
    sidebar_patterns = [
        r'<aside[^>]*class="sidebar"[^>]*>.*?</aside>',
        r'<!-- Sidebar -->.*?</aside>',
        r'<div[^>]*class="sidebar"[^>]*>.*?</div>',
    ]

    for pattern in sidebar_patterns:
        if re.search(pattern, content, re.DOTALL):
            content = re.sub(pattern, '', content, flags=re.DOTALL)
            changes_made.append("✓ Removed sidebar HTML")
            break

    # 3. Check if topbar already has dropdown menus
    has_profile_dropdown = 'id="profileDropdown"' in content
    has_notification_dropdown = 'id="notificationDropdown"' in content

    if not has_profile_dropdown:
        # Replace simple profile button with dropdown
        # Find the topbar__right section
        topbar_right_pattern = r'(<div class="topbar__right">)(.*?)(</div>\s*</header>)'

        new_topbar_right = r'''\1
                    <!-- Notification Dropdown -->
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

                    <!-- Profile Dropdown -->
                    <div class="dropdown">
                        <button class="topbar__icon-btn" onclick="toggleDropdown('profileDropdown')" aria-label="User Profile">
                            <i data-lucide="user" class="icon-18"></i>
                        </button>
                        <div class="dropdown__menu" id="profileDropdown">
                            <a href="/" class="dropdown__item">
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
                \3'''

        if re.search(topbar_right_pattern, content, re.DOTALL):
            content = re.sub(topbar_right_pattern, new_topbar_right, content, flags=re.DOTALL)
            changes_made.append("✓ Added notification and profile dropdowns")

    # 4. Add logo to topbar if not present
    if 'topbar__logo' not in content and '<header' in content:
        # Find topbar__left and add logo
        content = re.sub(
            r'(<div class="topbar__left">)',
            r'''\1
                    <!-- Logo -->
                    <div class="topbar__logo">
                        <div class="topbar__logo-icon">S</div>
                        <span>Scalping Bot</span>
                    </div>''',
            content
        )
        changes_made.append("✓ Added logo to topbar")

    # 5. Add dropdown CSS if not present
    if 'dropdown__menu' not in content and '<style>' in content:
        dropdown_css = '''
        /* Logo on Topbar */
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

        /* Dropdown Menu System */
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
        }

        .dropdown__item:hover {
            background: var(--color-bg-tertiary);
            color: var(--color-text-primary);
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
        }

        .notification-dropdown {
            min-width: 360px;
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
'''
        # Insert before closing </style>
        content = re.sub(r'(    </style>)', dropdown_css + r'\1', content)
        changes_made.append("✓ Added dropdown CSS")

    # 6. Add dropdown JavaScript if not present
    if 'toggleDropdown' not in content and '</script>' in content:
        dropdown_js = '''
        // Dropdown Menu System
        function toggleDropdown(dropdownId) {
            const dropdown = document.getElementById(dropdownId);
            const allDropdowns = document.querySelectorAll('.dropdown__menu');

            allDropdowns.forEach(d => {
                if (d.id !== dropdownId) {
                    d.classList.remove('show');
                }
            });

            dropdown.classList.toggle('show');
        }

        document.addEventListener('click', function(event) {
            if (!event.target.closest('.dropdown')) {
                document.querySelectorAll('.dropdown__menu').forEach(dropdown => {
                    dropdown.classList.remove('show');
                });
            }
        });

        document.addEventListener('DOMContentLoaded', function() {
            // Set active menu item
            const currentPath = window.location.pathname;
            document.querySelectorAll('.dropdown__item').forEach(item => {
                if (item.getAttribute('href') === currentPath) {
                    item.classList.add('active');
                }
            });
        });

'''
        # Insert before last closing </script>
        content = re.sub(r'(    </script>\s*</body>)', dropdown_js + r'\1', content, count=1)
        changes_made.append("✓ Added dropdown JavaScript")

    # Write updated content
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)

        print(f"\n✅ Updated: {os.path.basename(filepath)}")
        for change in changes_made:
            print(f"   {change}")
        return True
    else:
        print(f"\n⏭️  Skipped: {os.path.basename(filepath)} (already updated)")
        return False

def main():
    """Update all HTML files"""
    print("\n" + "="*60)
    print("UPDATING ALL PAGES TO TOPBAR-ONLY DESIGN")
    print("="*60)

    updated_count = 0
    skipped_count = 0

    for filename in FILES_TO_UPDATE:
        filepath = os.path.join(TEMPLATE_DIR, filename)

        if not os.path.exists(filepath):
            print(f"\n⚠️  File not found: {filename}")
            continue

        # Backup file
        backup_path = f"{filepath}.backup"
        if not os.path.exists(backup_path):
            import shutil
            shutil.copy(filepath, backup_path)
            print(f"📋 Backup created: {filename}.backup")

        if update_file(filepath):
            updated_count += 1
        else:
            skipped_count += 1

    print(f"\n" + "="*60)
    print(f"SUMMARY")
    print(f"="*60)
    print(f"✅ Updated: {updated_count} files")
    print(f"⏭️  Skipped: {skipped_count} files")
    print(f"📁 Total:   {updated_count + skipped_count} files processed")
    print(f"\n🚀 All pages now use topbar-only design!")

if __name__ == '__main__':
    main()
