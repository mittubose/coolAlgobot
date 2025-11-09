#!/usr/bin/env python3
"""
Script to remove top bar from pages that already have sidebar navigation.
This fixes the layout conflict where both top bar and sidebar were present.
"""

import os
import re
from pathlib import Path

def remove_topbar_html(content):
    """Remove top bar HTML section"""
    # Pattern to match the entire top bar div
    pattern = r'    <!-- Top Bar -->\s*\n\s*<div class="topbar">.*?</div>\s*\n\s*\n'
    content = re.sub(pattern, '', content, flags=re.DOTALL)
    return content

def remove_topbar_css(content):
    """Remove top bar CSS section"""
    # Pattern to match top bar styles
    pattern = r'\s*/\* ={20} TOP BAR STYLES ={20} \*/.*?(?=\n\s*(?:/\*|</style>))'
    content = re.sub(pattern, '', content, flags=re.DOTALL)
    return content

def remove_topbar_js(content):
    """Remove top bar JavaScript section"""
    # Pattern to match top bar functions
    pattern = r'\s*// ={20} TOP BAR FUNCTIONS ={20}.*?(?=\n\s*(?://|</script>|$))'
    content = re.sub(pattern, '', content, flags=re.DOTALL)
    return content

def remove_lucide_if_unused(content):
    """Remove Lucide script if it's only used for top bar"""
    # Check if there are any other Lucide icons besides topbar
    if 'data-lucide=' in content:
        # Still has Lucide icons elsewhere, keep the script
        return content

    # Remove Lucide script
    pattern = r'\s*<script src="https://unpkg\.com/lucide@latest"></script>\s*\n'
    content = re.sub(pattern, '', content)
    return content

def clean_file(file_path):
    """Remove top bar from a single HTML file"""
    print(f"\n📄 Cleaning: {file_path.name}")

    try:
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if top bar exists
        if 'class="topbar"' not in content:
            print(f"    ⚠️  No top bar found, skipping")
            return True

        # Remove top bar components
        original_length = len(content)
        content = remove_topbar_html(content)
        content = remove_topbar_css(content)
        content = remove_topbar_js(content)
        content = remove_lucide_if_unused(content)

        # Write back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        chars_removed = original_length - len(content)
        print(f"    ✅ Removed top bar ({chars_removed:,} characters)")
        return True

    except Exception as e:
        print(f"    ❌ Error: {e}")
        return False

def main():
    """Main function to clean all sidebar pages"""
    print("🚀 Removing Top Bar from Sidebar Pages")
    print("=" * 60)

    # Get templates directory
    templates_dir = Path(__file__).parent / 'src' / 'dashboard' / 'templates'

    if not templates_dir.exists():
        print(f"❌ Templates directory not found: {templates_dir}")
        return

    # Files that HAVE sidebars (remove top bar from these)
    sidebar_pages = [
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
    ]

    # Track results
    success_count = 0
    fail_count = 0

    # Clean each file
    for filename in sidebar_pages:
        file_path = templates_dir / filename

        if not file_path.exists():
            print(f"\n⚠️  File not found: {filename}")
            fail_count += 1
            continue

        if clean_file(file_path):
            success_count += 1
        else:
            fail_count += 1

    # Summary
    print("\n" + "=" * 60)
    print("📊 Cleanup Summary:")
    print(f"   ✅ Successfully cleaned: {success_count} files")
    print(f"   ❌ Failed: {fail_count} files")
    print(f"   📁 Total processed: {success_count + fail_count} files")
    print("=" * 60)

    # Files that KEEP top bar
    print("\n📌 Files that still have top bar (by design):")
    print("   - portfolio.html (uses top bar)")
    print("   - implementation-log.html (uses top bar)")
    print("=" * 60)

    if success_count > 0:
        print("\n✨ Top bar removed from sidebar pages!")
        print("🔄 Restart the server to see changes:")
        print("   pkill -f 'python.*run_dashboard.py' && DATABASE_URL=\"postgresql://mittuharibose@localhost:5432/scalping_bot\" python3 run_dashboard.py")

if __name__ == '__main__':
    main()
