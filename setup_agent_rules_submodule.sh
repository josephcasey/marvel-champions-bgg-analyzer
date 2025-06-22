#!/bin/bash

# Agent Rules Integration Setup Script
# Converts current agent-rules setup to proper submodule integration

set -e

echo "🔧 Setting up proper agent-rules integration..."

# Check if we're in the right directory
if [[ ! -f "bggscrape.py" ]]; then
    echo "❌ Error: This script must be run from the globalbggchamps project root"
    exit 1
fi

# Backup custom agent rule files
echo "📋 Backing up custom agent rule files..."
mkdir -p agent-rules-backup
cp agent-rules/project-rules/deploy.mdc agent-rules-backup/ 2>/dev/null || echo "No deploy.mdc to backup"
cp agent-rules/project-rules/test.mdc agent-rules-backup/ 2>/dev/null || echo "No test.mdc to backup"

# Remove current agent-rules directory
echo "🗑️  Removing current agent-rules directory..."
rm -rf agent-rules

# Add agent-rules as proper git submodule
echo "📦 Adding agent-rules as git submodule..."
git submodule add https://github.com/steipete/agent-rules.git agent-rules

# Initialize and update submodule
echo "🔄 Initializing submodule..."
git submodule init
git submodule update

# Copy back custom files
echo "📁 Restoring custom agent rule files..."
if [[ -f "agent-rules-backup/deploy.mdc" ]]; then
    cp agent-rules-backup/deploy.mdc agent-rules/project-rules/
    echo "✅ Restored deploy.mdc"
fi

if [[ -f "agent-rules-backup/test.mdc" ]]; then
    cp agent-rules-backup/test.mdc agent-rules/project-rules/
    echo "✅ Restored test.mdc"
fi

# Create .gitignore entries for custom files in agent-rules
echo "📝 Adding custom files to agent-rules .gitignore..."
cd agent-rules
echo "" >> .gitignore
echo "# Custom project-specific rules" >> .gitignore
echo "project-rules/deploy.mdc" >> .gitignore
echo "project-rules/test.mdc" >> .gitignore
cd ..

# Commit the submodule addition
echo "💾 Committing submodule setup..."
git add .gitmodules agent-rules
git commit -m "🔧 Convert agent-rules to proper git submodule

- Removed standalone agent-rules directory
- Added agent-rules as git submodule from steipete/agent-rules
- Restored custom deploy.mdc and test.mdc files
- Updated .gitignore to exclude custom project rules"

echo "✅ Agent rules integration complete!"
echo ""
echo "📋 Summary:"
echo "- agent-rules is now a proper git submodule"
echo "- Custom deploy.mdc and test.mdc preserved"
echo "- Changes to standard agent rules will sync with upstream"
echo "- Custom rules are ignored by submodule git"
echo ""
echo "🎯 Next steps:"
echo "1. Test deployment workflow: ./scripts/deploy-changes.sh"
echo "2. Update GITHUB_PAGES_DEPLOYMENT.md with new submodule info"
echo "3. Consider updating deploy script to handle submodule updates"

# Clean up backup directory
rm -rf agent-rules-backup
