#!/bin/bash

# Navigate to templates directory
cd src/dashboard/templates

# Create placeholder pages (we'll enhance them individually)
for page in strategies analytics accounts settings notifications help history profile; do
    if [ ! -f "${page}.html" ]; then
        echo "Creating ${page}.html..."
        cp dashboard.html "${page}.html"
    fi
done

echo "All pages created!"
ls -la *.html
