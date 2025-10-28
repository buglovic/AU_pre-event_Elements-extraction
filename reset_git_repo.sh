#!/bin/bash
# Script to reset Git repository and remove large files from history

cd /Users/romanbuegler/dev/hail_damage/AU_pre-event_Elements-extraction

echo "Step 1: Removing old git history..."
rm -rf .git

echo "Step 2: Initializing new git repository..."
git init

echo "Step 3: Adding all files (large files will be ignored by .gitignore)..."
git add .

echo "Step 4: Creating initial commit..."
git commit -m "Initial commit: AU Pre-Event Elements Extraction v2.1

- Configurable data paths via config.py
- Property integration with MFD deduplication
- Building footprint regularization (required)
- 75-column pre-event schema
- Multi-state support for Australia
- Documentation for external users"

echo "Step 5: Adding remote and pushing to GitHub..."
git remote add origin https://github.com/buglovic/AU_pre-event_Elements-extraction.git
git branch -M main
git push -u origin main --force

echo ""
echo "✓ Repository successfully reset and pushed to GitHub!"
echo "✓ Large files are now excluded via .gitignore"
