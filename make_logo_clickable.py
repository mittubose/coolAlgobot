#!/usr/bin/env python3
"""
Script to make the "Scalping Bot" logo clickable to navigate to dashboard
"""

import os
import re
from pathlib import Path

def make_logo_clickable(content):
    """
    Make the topbar logo clickable by wrapping it in a link or adding onclick
    """
    # Pattern to match the logo div
    logo_pattern = r'<div class="topbar__logo">\s*<div class="topbar__logo-icon">S</div>\s*<span>Scalping Bot</span>\s*</div>'

    # Replacement with clickable link
    logo_replacement = '''<a href="/" class="topbar__logo" style="text-decoration: none; color: inherit; cursor: pointer;">
                        <div class="topbar__logo-icon">S</div>
                        <span>Scalping Bot</span>
                    </a>'''

    # Check if already clickable
    if '<a href="/" class="topbar__logo"' in content:
        return content, False

    # Apply replacement
    content = re.sub(logo_pattern, logo_replacement, content, flags=re.DOTALL)

    return content, True

def update_file(file_path):
    """Update a single HTML file with clickable logo"""
    print(f"\n📄 Processing: {file_path.name}")

    try:
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Make logo clickable
        content, changed = make_logo_clickable(content)

        if not changed:
            print(f"    ⚠️  Logo already clickable, skipping")
            return True

        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"    ✅ Logo made clickable")
        return True

    except Exception as e:
        print(f"    ❌ Error: {e}")
        return False

def main():
    """Main function to update all HTML files"""
    print("🚀 Making Logo Clickable Across All Pages")
    print("=" * 60)

    # Get templates directory
    templates_dir = Path(__file__).parent / 'src' / 'dashboard' / 'templates'

    if not templates_dir.exists():
        print(f"❌ Templates directory not found: {templates_dir}")
        return

    # Get all HTML files
    html_files = list(templates_dir.glob('*.html'))

    # Track results
    success_count = 0
    fail_count = 0

    # Update each file
    for file_path in html_files:
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
        print("\n✨ Logo is now clickable!")
        print("   Click 'Scalping Bot' logo to navigate to dashboard")
        print("\n🔄 Restart the server to see changes:")
        print("   pkill -f 'python.*run_dashboard.py' && DATABASE_URL=\"postgresql://mittuharibose@localhost:5432/scalping_bot\" python3 run_dashboard.py")

if __name__ == '__main__':
    main()
