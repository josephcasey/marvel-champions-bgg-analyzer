# Marvel Champions BGG Project - Copilot Instructions

## 🎯 **Project Overview**
Marvel Champions BGG Statistics Analyser - A comprehensive Python tool for analyzing Marvel Champions: The Card Game play data from BoardGameGeek (BGG) with multi-language support, hero disambiguation, and comprehensive analysis features.

## 💻 **Jo's Development Environment**
- **OS**: macOS Big Sur
- **Python**: Always use Python 3 (`python3`, `pip3`); **MUST use virtual environments** (`.venv`)
- **Node.js**: 18 LTS (18.20.8) for MCP server development - installed via Homebrew
- **Package Installation**: Use virtual environment: `source .venv/bin/activate && pip install ...`
- **Encoding**: UTF-8 encoding and readable print/logging
- **Testing**: pytest, flake8, ruff (automated via scripts)
- **Terminal**: VSCode terminal usage assumed

## 📋 **Development Guidelines**

### **File Management:**
- ✅ Use virtual environment for ALL Python operations (`.venv` directory)
- ✅ Keep test code organized in appropriate directories
- ❌ Do not create new files that supersede existing ones
- ❌ Do not handle git operations directly (use deployment scripts)
- ✅ Before making edits, confirm adherence to these instructions

### **Agent Rules Integration:**
- 🔧 **Submodule Structure**: `agent-rules/` is a git submodule linked to steipete/agent-rules
- 🔗 **Project Rules Access**: Root-level `project-rules` symlink points to `agent-rules/project-rules/`
- 📋 **Workflow Rules**: All deployment and testing workflows are defined in agent-rules markdown files
- 🚀 **Command Pattern**: Use `/deploy` and `/test` commands to trigger automated workflows

### **Required Workflows:**

#### **Testing Workflow (`/test`):**
- **Script**: `scripts/test.sh` (single consolidated test script)
- **Triggers**: Environment validation, dependency checks, BGG API connectivity, code quality, pytest execution
- **Usage**: Always run `/test` before deployment to validate changes
- **Virtual Environment**: Automatically activates `.venv` and validates Python setup

#### **Deployment Workflow (`/deploy`):**
- **Two-Step Process**: Documentation update → Enhanced deployment script
- **Step 1**: AI updates README.md with new improvements entry (reverse chronological)
- **Step 2**: Run `scripts/deploy-changes-enhanced.sh "title" "description"`
- **Validation**: Comprehensive pre-deployment checks, git status analysis, submodule coordination

### **Documentation Updates:**
- 📝 **ALWAYS update `README.md`** when making changes to:
  - Core functionality (`bggscrape.py`)
  - Deployment scripts (`scripts/deploy-changes-enhanced.sh`)
  - Test scripts (`scripts/test.sh`)
  - New features, bug fixes, or configuration changes
  - Any changes that affect user experience

- 📋 **README Structure Requirements**:
  - Recent Improvements section at END of README
  - New entries at TOP of Recent Improvements (reverse chronological)
  - Format: "### [Feature Name] (MMM DD, YYYY)" (no commit hash initially)
  - Previous entries get commit hash retroactively
  - Latest entry marked with "(Latest)" suffix

### **Project Structure:**
- **Core Script**: `bggscrape.py` - Main BGG data analysis tool
- **Virtual Environment**: `.venv/` - Python environment (required)
- **Scripts Directory**: `scripts/` - Deployment and testing automation
- **Agent Rules**: `agent-rules/` (submodule) + `project-rules` (symlink)
- **Dependencies**: `requirements.txt` - Python package dependencies

## 🔧 **Key Components**

### **Core Functionality:**
- **BGG Data Analysis**: Hero usage statistics, multi-language translation support
- **Hero Disambiguation**: Fuzzy matching with official hero lists
- **Aspect/Hero Parsing**: Handles all five aspects (Justice, Aggression, Leadership, Protection, Pool)
- **Data Quality**: Comprehensive debugging and skipped play analysis

### **Deployment Scripts:**
- **Enhanced Script**: `scripts/deploy-changes-enhanced.sh` - Full deployment automation
- **Features**: Git validation, submodule coordination, comprehensive reporting
- **Integration**: Works with agent-rules submodule for workflow consistency

### **Testing Automation:**
- **Consolidated Script**: `scripts/test.sh` - Complete test workflow
- **Coverage**: Environment validation, dependency checks, BGG API connectivity, code quality
- **Automation**: No user confirmation required, proceeds only if previous steps succeed

### **Environment Setup:**
- **Python Virtual Environment**: Required for all operations
- **Node.js 18 LTS**: For MCP server development (PATH configured)
- **Dependencies**: Automated validation and installation
- **macOS Optimization**: Tested and optimized for macOS Big Sur

## 🚨 **Critical Reminders**

1. **Virtual Environment**: Always use `.venv` - never install packages globally
2. **Agent Rules Compliance**: Follow `/deploy` and `/test` command patterns
3. **Documentation**: Update README.md for ALL functional changes
4. **Backward Compatibility**: Maintain compatibility with existing automation
5. **Two-Step Deployment**: Document first, then deploy via enhanced script
6. **Testing First**: Always run `/test` before deployment
7. **Submodule Coordination**: Let deployment script handle agent-rules updates

## 🎯 **Quick Command Reference**

- **Test Everything**: `/test` (runs `scripts/test.sh`)
- **Deploy Changes**: `/deploy` (two-step process via agent-rules)
- **Virtual Environment**: `source .venv/bin/activate`
- **Main Analysis**: `python3 bggscrape.py` (after venv activation)
- **Dependencies**: `pip install -r requirements.txt` (in venv)
