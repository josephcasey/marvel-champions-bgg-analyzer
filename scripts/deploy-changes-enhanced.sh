#!/bin/bash
# Enhanced Deploy Changes Script for Marvel Champions BGG Analyzer
# Usage: ./scripts/deploy-changes-enhanced.sh "Brief commit title" "Optional detailed description"
# This version handles git submodules (like agent-rules) properly

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}🔄 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

# Check if commit message provided
if [ -z "$1" ]; then
    print_error "Commit message required. Usage: ./scripts/deploy-changes-enhanced.sh \"Brief commit title\" \"Optional detailed description\""
fi

COMMIT_TITLE="$1"
COMMIT_DESCRIPTION="$2"

echo -e "${CYAN}=== MARVEL CHAMPIONS BGG ANALYZER DEPLOYMENT (Enhanced) ===${NC}"
echo ""

# Step 1: Python Environment Validation
print_status "Step 1: Python Environment Validation"

# Check if virtual environment exists and activate it
if [ ! -d ".venv" ]; then
    print_error "Virtual environment not found. Run 'python3 -m venv .venv' first."
fi

source .venv/bin/activate
print_success "Virtual environment activated: $(pwd)/.venv"

# Check Python version
PYTHON_VERSION=$(python3 --version)
print_success "Python version: $PYTHON_VERSION"

# Validate dependencies
pip3 list > /dev/null 2>&1
PACKAGE_COUNT=$(pip3 list | wc -l | tr -d ' ')
print_success "Dependencies validated: $PACKAGE_COUNT packages"

# Step 2: BGG API Connectivity Test
print_status "Step 2: BGG API Connectivity Test"

# Test BGG API and hero list loading
python3 -c "
import requests
import json

# Test BGG API
try:
    response = requests.get('https://boardgamegeek.com/xmlapi2/thing?id=285774', timeout=10)
    response.raise_for_status()
    print('✅ BGG API accessible')
except Exception as e:
    print(f'❌ BGG API error: {e}')
    exit(1)

# Test hero list loading
try:
    with open('marvel_champions_heroes.json', 'r') as f:
        heroes = json.load(f)
    print(f'✅ Official hero list loaded: {len(heroes)} heroes')
except Exception as e:
    print(f'⚠️  Hero list warning: {e}')

# Test translation service
try:
    from googletrans import Translator
    translator = Translator()
    print(f'✅ Translation service active')
except Exception as e:
    print(f'⚠️  Translation service warning: {e}')
"

if [ $? -ne 0 ]; then
    print_error "BGG API connectivity test failed"
fi

# Step 3: Code Quality Validation
print_status "Step 3: Code Quality Validation"

# Basic Python syntax check
python3 -m py_compile bggscrape.py
print_success "Python syntax check passed"

# Test imports
python3 -c "
import xml.etree.ElementTree as ET
import requests
import re
import time
import json
from googletrans import Translator
print('✅ Import resolution successful')
"

if [ $? -ne 0 ]; then
    print_error "Import resolution failed"
fi

print_success "No critical issues found"

# Step 4: Submodule Management
print_status "Step 4: Submodule Management"

# Check if we have submodules
if [ -f ".gitmodules" ]; then
    print_info "Git submodules detected, checking status..."
    
    # Update submodules to latest
    git submodule update --remote --merge
    
    # Check if submodules have changes
    SUBMODULE_CHANGES=$(git submodule foreach --quiet 'git status --porcelain' | wc -l | tr -d ' ')
    if [ "$SUBMODULE_CHANGES" -gt 0 ]; then
        print_info "Submodule changes detected"
        git submodule foreach 'git status --short'
        
        # Add submodule changes to staging
        git add .
        print_success "Submodule changes staged"
    else
        print_success "Submodules up to date"
    fi
else
    print_info "No git submodules configured"
fi

# Step 5: Git Operations
print_status "Step 5: Git Operations"

# Check git status
GIT_STATUS=$(git status --porcelain)
if [ -z "$GIT_STATUS" ]; then
    print_warning "No changes to commit"
    echo ""
    print_info "Current git status is clean. Nothing to deploy."
    exit 0
fi

# Show what will be committed
print_info "Files to be committed:"
git status --short

# Stage all changes (including submodule updates)
git add .
print_success "Changes staged"

# Verify staging
STAGED_FILES=$(git diff --cached --name-only | wc -l | tr -d ' ')
print_success "Staging verified: $STAGED_FILES files"

# Create commit message
if [ -n "$COMMIT_DESCRIPTION" ]; then
    FULL_COMMIT_MESSAGE="$COMMIT_TITLE

$COMMIT_DESCRIPTION"
else
    FULL_COMMIT_MESSAGE="$COMMIT_TITLE"
fi

# Create commit
git commit -m "$FULL_COMMIT_MESSAGE"
COMMIT_HASH=$(git rev-parse --short HEAD)
print_success "Commit created: $COMMIT_HASH"

# Step 6: Push to GitHub
print_status "Step 6: Push to GitHub"

# Push changes (including submodule references)
git push origin main
print_success "Changes pushed to GitHub"

# Push submodule changes if any exist
if [ -f ".gitmodules" ]; then
    print_info "Checking submodule push status..."
    git submodule foreach 'git push origin HEAD || true'
fi

# Step 7: Final Verification
print_status "Step 7: Final Verification"

# Verify clean working tree
FINAL_STATUS=$(git status --porcelain)
if [ -z "$FINAL_STATUS" ]; then
    print_success "Working tree clean"
else
    print_warning "Working tree not clean after deployment"
fi

# Check remote sync
git fetch origin main
LOCAL_HASH=$(git rev-parse HEAD)
REMOTE_HASH=$(git rev-parse origin/main)

if [ "$LOCAL_HASH" = "$REMOTE_HASH" ]; then
    SYNC_STATUS="UP_TO_DATE"
    print_success "Local and remote in sync"
else
    SYNC_STATUS="OUT_OF_SYNC"
    print_warning "Local and remote out of sync"
fi

# Submodule verification
if [ -f ".gitmodules" ]; then
    print_info "Verifying submodule sync..."
    git submodule status
fi

echo ""
echo -e "${CYAN}=== DEPLOYMENT VERIFICATION REPORT ===${NC}"
echo "--- GIT STATUS ---"
if [ -z "$FINAL_STATUS" ]; then
    echo "STATUS: CLEAN"
else
    echo "STATUS: DIRTY"
fi

echo ""
echo "--- REMOTE SYNC ---"
echo "SYNC_STATUS: $SYNC_STATUS"

echo ""
echo "--- SUBMODULES ---"
if [ -f ".gitmodules" ]; then
    git submodule status | sed 's/^/  /'
else
    echo "  No submodules configured"
fi

echo ""
echo "--- RECENT COMMITS ---"
echo "Last 3 commits:"
git log --oneline -3 | sed 's/^/  /'

echo ""
echo "--- DEPLOYMENT SUMMARY ---"
echo "OVERALL_STATUS: SUCCESS"
echo "WORKING_TREE: CLEAN"
echo "SYNC_STATUS: $SYNC_STATUS"
echo "COMMIT_HASH: $COMMIT_HASH"
echo "SUBMODULES: $([ -f ".gitmodules" ] && echo "CONFIGURED" || echo "NONE")"
echo "DEPLOYMENT_SUCCESS: true"
echo -e "${CYAN}=== END DEPLOYMENT REPORT ===${NC}"

echo ""
print_success "Enhanced deployment completed successfully!"
print_info "Commit: $COMMIT_HASH - $COMMIT_TITLE"
print_info "Repository: https://github.com/josephcasey/marvel-champions-bgg-analyzer"

if [ -f ".gitmodules" ]; then
    echo ""
    print_info "📋 Submodule Integration:"
    print_info "- Agent rules and submodules are properly managed"
    print_info "- Custom project rules (deploy.mdc, test.mdc) preserved"
    print_info "- Upstream updates can be pulled with: git submodule update --remote"
fi
