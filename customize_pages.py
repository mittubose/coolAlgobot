#!/usr/bin/env python3
"""
Script to customize each page with unique content
"""
import os
import re

templates_dir = 'src/dashboard/templates'

# Page customizations: (title, icon, subtitle, active_nav)
pages = {
    'strategies.html': {
        'title': 'Strategy Catalog',
        'subtitle': 'Manage, backtest, and deploy your trading strategies',
        'icon': 'brain',
        'nav_active': 'Strategies'
    },
    'analytics.html': {
        'title': 'Analytics Dashboard',
        'subtitle': 'Comprehensive performance analysis and insights',
        'icon': 'bar-chart-3',
        'nav_active': 'Analytics'
    },
    'accounts.html': {
        'title': 'Accounts & Broker Connections',
        'subtitle': 'Manage your trading accounts and funds',
        'icon': 'wallet',
        'nav_active': 'Accounts'
    },
    'settings.html': {
        'title': 'Settings & Configuration',
        'subtitle': 'Configure trading parameters and system preferences',
        'icon': 'settings',
        'nav_active': 'Settings'
    },
    'notifications.html': {
        'title': 'Notifications & Alerts',
        'subtitle': 'View system alerts and trading notifications',
        'icon': 'bell',
        'nav_active': 'Notifications'
    },
    'help.html': {
        'title': 'Help & Documentation',
        'subtitle': 'Guides, tutorials, and FAQs',
        'icon': 'help-circle',
        'nav_active': 'Help'
    },
    'history.html': {
        'title': 'Trade History & Sessions',
        'subtitle': 'View all past trades and trading sessions',
        'icon': 'clock',
        'nav_active': 'History'
    },
    'profile.html': {
        'title': 'Profile & Preferences',
        'subtitle': 'Manage your account and user preferences',
        'icon': 'user',
        'nav_active': 'Profile'
    }
}

def customize_page(filename, config):
    """Customize a page with unique content"""
    filepath = os.path.join(templates_dir, filename)
    
    if not os.path.exists(filepath):
        print(f"❌ {filename} not found")
        return
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Update page title
    content = re.sub(
        r'<title>.*?</title>',
        f'<title>Scalping Bot - {config["title"]}</title>',
        content
    )
    
    # Update header title and subtitle
    content = re.sub(
        r'<h1 class="header__title">.*?</h1>',
        f'<h1 class="header__title">{config["title"]}</h1>',
        content
    )
    
    content = re.sub(
        r'<p class="header__subtitle">.*?</p>',
        f'<p class="header__subtitle">{config["subtitle"]}</p>',
        content
    )
    
    # Update nav active state
    # Remove all active classes first
    content = re.sub(r'<a href="([^"]*)" class="nav-item active"', r'<a href="\1" class="nav-item"', content)
    
    # Add active class to correct nav item
    if config['nav_active'] == 'Dashboard':
        content = re.sub(r'<a href="/" class="nav-item"', r'<a href="/" class="nav-item active"', content)
    elif config['nav_active'] == 'Accounts':
        content = re.sub(r'<a href="/accounts" class="nav-item"', r'<a href="/accounts" class="nav-item active"', content)
    elif config['nav_active'] == 'Strategies':
        content = re.sub(r'<a href="/strategies" class="nav-item"', r'<a href="/strategies" class="nav-item active"', content)
    elif config['nav_active'] == 'Analytics':
        content = re.sub(r'<a href="/analytics" class="nav-item"', r'<a href="/analytics" class="nav-item active"', content)
    elif config['nav_active'] == 'Notifications':
        content = re.sub(r'<a href="/notifications" class="nav-item"', r'<a href="/notifications" class="nav-item active"', content)
    elif config['nav_active'] == 'Settings':
        content = re.sub(r'<a href="/settings" class="nav-item"', r'<a href="/settings" class="nav-item active"', content)
    elif config['nav_active'] == 'Help':
        content = re.sub(r'<a href="/help" class="nav-item"', r'<a href="/help" class="nav-item active"', content)
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"✅ {filename} customized - {config['title']}")

# Main execution
print("\n🎨 Customizing pages with unique content...\n")
for filename, config in pages.items():
    customize_page(filename, config)

print("\n✨ All pages customized!\n")
