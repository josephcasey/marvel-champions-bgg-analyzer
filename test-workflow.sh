#!/bin/bash
# Test Workflow Script for Marvel Champions BGG Analyzer
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
echo "=================================================="

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Check if we're in the right directory
if [ ! -f "bggscrape.py" ]; then
    print_status $RED "❌ Error: bggscrape.py not found"
    print_status $YELLOW "   Please run this from the Marvel Champions BGG project root"
    exit 1
fi

# Check if .venv directory exists
if [ ! -d ".venv" ]; then
    print_status $RED "❌ Virtual environment not found"
    print_status $YELLOW "   Creating virtual environment..."
    python3 -m venv .venv
    print_status $GREEN "✅ Virtual environment created"
fi

# Activate virtual environment
print_status $CYAN "🔄 Activating virtual environment..."
source .venv/bin/activate

# Verify activation
if [ -z "$VIRTUAL_ENV" ]; then
    print_status $RED "❌ Failed to activate virtual environment"
    exit 1
fi

print_status $GREEN "✅ Virtual environment activated: $(basename $VIRTUAL_ENV)"

# Check Python version
PYTHON_VERSION=$(python3 --version)
print_status $CYAN "🐍 $PYTHON_VERSION"
print_status $CYAN "📍 Using Python: $(which python3)"

# Check if requirements are installed
print_status $CYAN "📦 Checking dependencies..."
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
            except Exception:
                missing.append(req.strip())
                print(f'❌ {req.strip()} - MISSING')
    
    if missing:
        print(f'\\\\n⚠️  Installing missing packages...')
        sys.exit(2)  # Special exit code for missing packages
    else:
        print('\\\\n🎉 All dependencies satisfied!')
except FileNotFoundError:
    print('⚠️  requirements.txt not found')
"
fi

# Handle missing packages
if [ $? -eq 2 ]; then
    print_status $YELLOW "📥 Installing missing packages..."
    pip install -r requirements.txt
    print_status $GREEN "✅ Dependencies installed"
fi

# Parse command line arguments
SCRIPT_TO_RUN="bggscrape.py"
VERBOSE=false
COVERAGE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --coverage|-c)
            COVERAGE=true
            shift
            ;;
        *.py)
            SCRIPT_TO_RUN=$1
            shift
            ;;
        *)
            print_status $YELLOW "Unknown option: $1"
            shift
            ;;
    esac
done

# Run the appropriate test
print_status $BLUE "🚀 Running tests..."
echo ""

if [ -d "tests" ] && python3 -c "import pytest" 2>/dev/null; then
    print_status $CYAN "🧪 Running pytest..."
    if [ "$COVERAGE" = true ]; then
        python3 -m pytest tests/ --cov=. --cov-report=term-missing -v
    elif [ "$VERBOSE" = true ]; then
        python3 -m pytest tests/ -v
    else
        python3 -m pytest tests/
    fi
elif [ -f "$SCRIPT_TO_RUN" ]; then
    print_status $CYAN "🔍 Running $SCRIPT_TO_RUN..."
    if [ "$VERBOSE" = true ]; then
        python3 "$SCRIPT_TO_RUN" --verbose 2>&1 | tee test_output.log
    else
        python3 "$SCRIPT_TO_RUN"
    fi
else
    print_status $RED "❌ No tests found and $SCRIPT_TO_RUN doesn't exist"
    exit 1
fi

# Check exit code
if [ $? -eq 0 ]; then
    print_status $GREEN "✅ Tests completed successfully!"
else
    print_status $RED "❌ Tests failed"
    exit 1
fi

# Optional: Run code quality checks
if python3 -c "import flake8" 2>/dev/null; then
    echo ""
    print_status $CYAN "🔍 Running code quality checks..."
    python3 -m flake8 --max-line-length=88 --extend-ignore=E203,W503 *.py || true
fi

print_status $GREEN "🎉 Test workflow completed!"
