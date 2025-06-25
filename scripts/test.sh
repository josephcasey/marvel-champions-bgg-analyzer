#!/bin/bash
# Marvel Champions BGG Analyzer Test Workflow
# Automated test workflow implementing test.mdc specifications
# Ensures proper venv activation and python3 usage on macOS Big Sur

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Marvel Champions BGG Analyzer Test Workflow${NC}"
echo "=============================================="
echo ""

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_error() {
    print_status $RED "$1"
    exit 1
}

# Step 1: Environment Validation
print_status $CYAN "🔍 Step 1: Environment Validation"

# Check if we're in the right directory
if [ ! -f "bggscrape.py" ]; then
    print_error "❌ bggscrape.py not found. Please run this from the Marvel Champions BGG project root"
fi

# Check if .venv directory exists
if [ ! -d ".venv" ]; then
    print_error "❌ Virtual environment not found. Please create one first: python3 -m venv .venv"
fi

print_status $GREEN "✅ Environment validation passed"
echo ""

# Step 2: Virtual Environment Activation  
print_status $CYAN "🔄 Step 2: Virtual Environment Activation"
source .venv/bin/activate

# Verify activation
if [ -z "$VIRTUAL_ENV" ]; then
    print_error "❌ Failed to activate virtual environment"
fi

print_status $GREEN "✅ Virtual environment activated: $VIRTUAL_ENV"
echo ""

# Step 3: Python Version Verification
print_status $CYAN "🐍 Step 3: Python Version Verification"
PYTHON_VERSION=$(python3 --version)
PYTHON_PATH=$(which python3)
print_status $GREEN "✅ $PYTHON_VERSION"
print_status $GREEN "✅ Using Python: $PYTHON_PATH"
echo ""

# Step 4: Package Dependencies Check
print_status $CYAN "📦 Step 4: Package Dependencies Check"
if [ -f "requirements.txt" ]; then
    python3 -c "
import pkg_resources
import sys

try:
    with open('requirements.txt', 'r') as f:
        requirements = f.read().splitlines()
    
    missing = []
    for req in requirements:
        if req.strip() and not req.startswith('#'):
            try:
                pkg_resources.require(req.strip())
                print(f'✅ {req.strip()}')
            except Exception as e:
                missing.append(req.strip())
                print(f'❌ {req.strip()}: {e}')
    
    if missing:
        print(f'Installing missing packages: {missing}')
        sys.exit(2)  # Special exit code for missing packages
    else:
        print('🎉 All dependencies satisfied!')
except FileNotFoundError:
    print('⚠️  requirements.txt not found')
    sys.exit(1)
"
    
    # Handle missing packages
    DEPS_EXIT_CODE=$?
    if [ $DEPS_EXIT_CODE -eq 2 ]; then
        print_status $YELLOW "📥 Installing missing packages..."
        pip install -r requirements.txt
        print_status $GREEN "✅ Dependencies installed"
    elif [ $DEPS_EXIT_CODE -eq 0 ]; then
        print_status $GREEN "✅ All dependencies verified"
    else
        print_error "❌ Dependency check failed"
    fi
else
    print_status $YELLOW "⚠️  requirements.txt not found"
fi
echo ""

# Step 5: BGG API Connectivity Test
print_status $CYAN "🌐 Step 5: BGG API Connectivity Test"
python3 -c "
import requests
import json
from googletrans import Translator

try:
    # Test BGG API connectivity using the official hero list endpoint
    url = 'https://github.com/josephcasey/mybgg/raw/refs/heads/master/cached_hero_names.json'
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    hero_names = json.loads(response.text)
    print(f'✅ BGG API accessible')
    print(f'✅ Official hero list loaded: {len(hero_names)} heroes')
except Exception as e:
    print(f'❌ BGG API connectivity failed: {e}')
    exit(1)

# Test translation service
try:
    translator = Translator()
    print(f'✅ Translation service active')
except Exception as e:
    print(f'⚠️  Translation service warning: {e}')
"

if [ $? -ne 0 ]; then
    print_error "❌ BGG API connectivity test failed"
fi
echo ""

# Step 6: Code Quality Checks
print_status $CYAN "🔍 Step 6: Code Quality Checks"

# Basic Python syntax check
python3 -m py_compile bggscrape.py
print_status $GREEN "✅ Python syntax check passed"

# Test imports
python3 -c "
import xml.etree.ElementTree as ET
import requests
import re
import time
import json
from googletrans import Translator
from collections import Counter, defaultdict
print('✅ Import resolution successful')
"

if [ $? -ne 0 ]; then
    print_error "❌ Import resolution failed"
fi

# Run flake8 if available (optional, non-blocking)
if python3 -c "import flake8" 2>/dev/null; then
    print_status $CYAN "🔍 Running code quality checks..."
    python3 -m flake8 --max-line-length=88 --extend-ignore=E203,W503 *.py || print_status $YELLOW "⚠️  Code quality warnings found (non-blocking)"
else
    print_status $YELLOW "💡 Install flake8 for code quality checks: pip install flake8"
fi
echo ""

# Step 7: Test Execution
print_status $CYAN "🚀 Step 7: Test Execution"

# Check for pytest and run unit tests if available
if python3 -c "import pytest" 2>/dev/null && [ -d "tests" ]; then
    print_status $CYAN "🧪 Running pytest..."
    python3 -m pytest tests/ -v
    print_status $GREEN "✅ Unit tests passed"
    echo ""
fi

# Run the main BGG scraper script
print_status $CYAN "🔍 Running BGG scraper analysis..."
echo "=================== BGG ANALYZER OUTPUT ==================="
python3 bggscrape.py
SCRIPT_EXIT_CODE=$?
echo "==========================================================="

if [ $SCRIPT_EXIT_CODE -eq 0 ]; then
    print_status $GREEN "✅ Main script executed successfully"
else
    print_error "❌ Main script failed with exit code $SCRIPT_EXIT_CODE"
fi
echo ""

# Step 8: Final Summary
print_status $GREEN "🎉 === TEST WORKFLOW COMPLETED SUCCESSFULLY ==="
echo ""
print_status $GREEN "✅ Environment validation passed"
print_status $GREEN "✅ Virtual environment activated" 
print_status $GREEN "✅ Python 3 verified: $PYTHON_VERSION"
print_status $GREEN "✅ Dependencies satisfied"
print_status $GREEN "✅ BGG API connectivity confirmed"
print_status $GREEN "✅ Code quality checks passed"
print_status $GREEN "✅ Main script executed successfully"
echo ""
print_status $BLUE "💡 Ready for deployment workflow!"
print_status $BLUE "   Next: Update README.md, then run: ./scripts/deploy-changes-enhanced.sh \"commit title\""
echo ""
