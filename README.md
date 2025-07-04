# Marvel Champions BGG Data Analyzer

A comprehensive Python tool for analyzing Marvel Champions: The Card Game play data from BoardGameGeek (BGG). This script extracts hero usage statistics, handles multi-language translations, and provides detailed debugging information for data quality analysis.

## 🎯 Features

- **Monthly Play Analysis**: Focus on analyzing hero usage for players active in specific months
- **Multi-language Support**: Automatically translates hero names from Spanish and Chinese to English
- **Hero Name Disambiguation**: Uses fuzzy matching and official hero lists for accurate identification
- **Comprehensive Analysis**: Tracks successful matches, translations, and skipped plays with detailed reasons
- **Color-coded Output**: Easy-to-read terminal output with status indicators
- **Data Quality Insights**: Detailed XML debugging information for troubleshooting BGG data issues
- **Villain/Scenario Filtering**: Automatically excludes non-hero entries from statistics
- **Multi-User Aggregation**: Analyzes hero usage across multiple users from recent months

## 📊 What It Analyzes

### Hero Usage Statistics
- **Monthly Focus**: Analyzes players who were active in recent months (default: May 2025)
- Individual hero play counts across multiple users
- User distribution metrics (how many users played each hero)
- Translation success rates
- Official hero list matching rates
- Geographic distribution of play styles (via language detection)
- Aggregated statistics from multiple monthly active users

### Skipped Plays Analysis
- Plays with missing player data
- Players with empty color/team fields
- Meaningless names after cleaning
- Translation errors and their reasons
- Full XML debugging information for each category

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+**: System Python 3 (tested on macOS Big Sur)
- **Node.js 18 LTS**: For MCP server development (installed via Homebrew)
- **Internet connection**: For BGG API and Google Translate
- **macOS**: Optimized for macOS Big Sur environment

### Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd marvel-champions-bgg-analyzer
```

2. Create and activate virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. For MCP server development, ensure Node.js 18 is in PATH:
```bash
# Node.js 18 should be installed via Homebrew and added to PATH
node --version  # Should show v18.20.8
npm --version   # Should show 10.8.2
```

### Usage

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the BGG analyzer
python3 bggscrape.py

# For deployment (uses enhanced deployment workflow)
./scripts/deploy-changes-enhanced.sh
```

## 📈 Sample Output

```
✅ Loaded 61 official hero names
🔍 Fetching recent plays to find active users...
👥 Found 58 users in recent plays

🎯 Hero usage analysis for user 348019:
 1. Phoenix                5 plays [TRANSLATED, OFFICIAL]
 2. Ant Man                3 plays [OFFICIAL]
 3. Spidey                 3 plays [OFFICIAL]

📊 Summary Statistics:
- Total hero plays analyzed: 39
- ✅ Official matches: 39 (100.0%)
- 🔄 Translated plays: 8 (20.5%)
- ❌ Unmatched plays: 0 (0.0%)

🚫 Skipped Plays Analysis (98 total):
   📋 No Players: 37 plays
   📋 Empty Color: 43 plays
   📋 Meaningless Names: 13 plays
   📋 Translation Errors: 5 plays
```

## 🔧 Configuration

### Hero Name Translation
The script includes manual translation mappings for common hero names in:
- **Spanish**: Halcón → Falcon, Soldado de invierno → Winter Soldier
- **Chinese**: 凤凰女 → Phoenix, 钢铁侠 → Iron Man

### Official Hero List
The script automatically loads the official hero list from GitHub:
```
https://github.com/josephcasey/mybgg/raw/refs/heads/master/cached_hero_names.json
```

## 📁 Project Structure

```
marvel-champions-bgg-analyzer/
├── bggscrape.py           # Main analysis script
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── .venv/                # Virtual environment (not committed)
├── .github/              # GitHub configuration
│   └── copilot-instructions.md  # Copilot development guidelines
└── .gitignore            # Git ignore rules
```

## 🤝 Contributing

This project was developed with GitHub Copilot assistance. Feel free to:
- Report issues with BGG data parsing
- Add support for additional languages
- Improve hero name disambiguation
- Enhance data visualization

## 📄 License

This project is open source. Please respect BoardGameGeek's API terms of service when using this tool.

## 🙏 Acknowledgments

- **BoardGameGeek** for providing the game data API
- **GitHub Copilot** for development assistance
- **Marvel Champions community** for maintaining comprehensive hero lists
- **Google Translate API** for multi-language support

## 🔍 Technical Details

### Dependencies
- `requests`: BGG API communication
- `googletrans`: Multi-language translation
- `xml.etree.ElementTree`: XML parsing
- `json`: Official hero list processing
- `re`: Text pattern matching and cleaning

### Data Sources
- BGG XML API v2 for play data
- Official Marvel Champions hero names from community-maintained lists
- Manual translation mappings for common non-English entries

### Analysis Methodology
1. Fetch recent plays from BGG API
2. Extract hero names from player color/team fields
3. Clean and normalize hero names
4. Translate non-English entries
5. Match against official hero lists using fuzzy matching
6. Generate comprehensive statistics and debugging output

## 📈 Recent Improvements

### BGG API Data Integrity Fix (Jun 27, 2025) - `dc023ef` (Latest)
- 🔧 **Fixed "too neat" data issue** - Resolved critical BGG API bug where userid parameter was being ignored
- 📊 **Realistic hero statistics** - Now shows authentic, varied hero play counts instead of uniform artificial data
- 🎯 **Proper user isolation** - Each user's play data is now independently fetched and aggregated
- 🔄 **Client-side data grouping** - Implemented workaround for BGG API limitation by fetching recent plays and grouping by user ID
- ✅ **Data authenticity verified** - Hero usage now shows natural distributions (e.g., Hulk: 11 plays, She-Hulk: 10 plays, etc.)
- 🚫 **Eliminated data sharing** - Fixed bug where all users appeared to have identical play statistics
- 📈 **Improved analysis accuracy** - Marvel Champions hero usage statistics now reflect actual player behavior patterns

### Monthly Focus Analysis Enhancement (Jun 25, 2025) - `126013d`
- 📅 **Monthly User Analysis** - Enhanced script to focus on analyzing hero usage for players active in specific months (default: May 2025)
- 👥 **Multi-User Aggregation** - Implemented comprehensive analysis across multiple users from recent months instead of single-user analysis
- 🔍 **BGG Play Stats Integration** - Added functionality to fetch user lists from BoardGameGeek monthly play statistics pages
- 📊 **Enhanced Reporting** - Improved summary statistics include user distribution metrics and cross-user hero popularity
- 🛡️ **Graceful Fallback** - Falls back to recent plays analysis when monthly data is unavailable
- 🎯 **Targeted Analysis** - Provides more relevant hero usage trends by focusing on recently active community members
- ⚡ **Performance Optimized** - Configurable user limits and play limits per user for efficient large-scale analysis

### Agent Rules Integration & Deployment Automation (Jun 21, 2025) - `43dc7b5`
- 🔧 **Submodule Structure** - Integrated `agent-rules/` as git submodule linked to steipete/agent-rules repository
- 🔗 **Project Rules Access** - Created root-level `project-rules` symlink pointing to `agent-rules/project-rules/` for seamless access
- 📋 **Workflow Rules** - All deployment and testing workflows now defined in agent-rules markdown files for consistency
- 🚀 **Command Pattern** - Implemented `/deploy` and `/test` commands triggering automated workflows via agent rules integration
- 📊 **Enhanced Scripts** - Updated `scripts/deploy-changes-enhanced.sh` and `scripts/test.sh` to work with agent rules coordination
- 📋 **Coordinated Updates** - `/test` and `/deploy` commands now handle both main repository and agent-rules submodule changes
- ⚡ **Upstream Sync Capability** - Can pull improvements from steipete/agent-rules while preserving custom project rules
- 📊 **Comprehensive Reporting** - Enhanced deployment verification includes submodule status and git coordination details

### Deployment Script Syntax Fix (Jun 24, 2025) (Latest)
- 🔧 **Shell Syntax Error Fix** - Removed extra `fi` statement causing syntax error in deployment script line 415
- ✅ **Enhanced Script Reliability** - Fixed bash script structure to prevent deployment interruptions
- 🎯 **Two-Stage Deployment Process** - Applied proper workflow for deployment script modifications per agent rules
- 📋 **Validation Improvement** - Ensures deployment script runs cleanly through completion without syntax errors

### Node.js 18 MCP Server Environment Setup (Jun 24, 2025)
- � **Node.js 18 LTS Installation** - Successfully installed Node.js 18.20.8 and npm 10.8.2 via Homebrew for MCP server compatibility
- � **macOS 11 Compatibility** - Configured Node.js 18 as keg-only installation with proper PATH setup in bash profile
- � **MCP Development Ready** - Environment now supports Model Context Protocol server development and deployment
- ⚙️ **PATH Configuration** - Added `/usr/local/opt/node@18/bin` to PATH for consistent Node.js access across terminal sessions
- 🎯 **Legacy OS Support** - Working solution for Node.js development on macOS Big Sur (Tier 3 Homebrew support)

### Enhanced BGG Analyzer Performance & CLI Features (Jun 25, 2025) - `126013d`
- 🚀 **1000 Play Processing** - Successfully processes up to 1000 plays per user with efficient memory management and progress indicators
- 💻 **Command Line Interface** - Added CLI arguments: `--plays` (play limit), `--delay` (API delay), `--debug` (verbose), `--quiet` (minimal output)
- 📊 **Progress Tracking** - Real-time progress reporting for large datasets with batch intervals and completion percentages
- 🔧 **Performance Optimization** - Dynamic API delay scaling for large datasets, network error handling with automatic retries
- 🎯 **Enhanced User Experience** - Clear configuration display, estimated completion times, and color-coded status indicators
- ✅ **Production Ready** - Robust error handling, memory optimization, and comprehensive analysis with 81.3% play success rate

### Non-Interactive Deployment Automation (Jun 25, 2025) - `645fb99`
- 🔧 **Automated Git Operations** - Enhanced deployment script with completely non-interactive git configuration to prevent editor prompts during submodule merges
- 🚫 **Editor-Free Workflow** - Added global git editor configuration (`GIT_EDITOR=true`) and merge auto-edit settings (`GIT_MERGE_AUTOEDIT=no`) for fully automated deployment
- 🔄 **Submodule Merge Improvements** - Replaced problematic `git submodule update --remote --merge` with individual submodule handling using `--no-edit` flags
- 🧹 **Configuration Cleanup** - Added proper cleanup function with EXIT trap to restore git settings after deployment completion
- ✅ **Zero-Interaction Deployment** - Deployment workflow now runs completely hands-free without requiring terminal interaction for commit messages

### Copilot Instructions Comprehensive Update (Jun 25, 2025) - `645fb99`
- 📋 **Complete Documentation Overhaul** - Fully updated `.github/copilot-instructions.md` with comprehensive project overview, accurate environment setup, and current workflow patterns
- 🔧 **Agent Rules Integration Documentation** - Added detailed explanation of submodule structure, symlink access, and `/deploy`/`/test` command patterns
- 🎯 **Virtual Environment Requirements** - Emphasized mandatory `.venv` usage with clear setup instructions and package installation guidelines
- 📊 **Current Workflow Alignment** - Documented two-step deployment process, consolidated test script automation, and README update requirements
- 🚀 **Environment Accuracy** - Updated Node.js 18 LTS details, macOS Big Sur optimization, and MCP server development setup
- ✅ **Command Reference Added** - Practical quick reference for common operations including testing, deployment, and environment management

### Deployment Consistency Rules & Workflow Standardization (Jun 22, 2025) - `80f13cd`
- 🚀 **Node.js 18 LTS Installation** - Successfully installed Node.js 18.20.8 and npm 10.8.2 via Homebrew for MCP server compatibility
- 🔧 **macOS 11 Compatibility** - Configured Node.js 18 as keg-only installation with proper PATH setup in bash profile
- 📋 **MCP Development Ready** - Environment now supports Model Context Protocol server development and deployment
- ⚙️ **PATH Configuration** - Added `/usr/local/opt/node@18/bin` to PATH for consistent Node.js access across terminal sessions
- 🎯 **Legacy OS Support** - Working solution for Node.js development on macOS Big Sur (Tier 3 Homebrew support)

### Comprehensive Deployment Validation & Agent Rules Workflow (Jun 22, 2025) - `4ce10b5`
- 📊 **Complete Pre-deployment Validation** - Added extensive git status, branch info, and uncommitted changes analysis before deployment
- 🔍 **Detailed File Change Analysis** - Shows exact file modifications with diff summaries for review before commit
- 📋 **Enhanced Agent Rules Workflow** - Updated deploy.mdc with Python environment validation rules, two-stage deployment patterns, and troubleshooting guide
- 🎯 **Self-contained Review Process** - All verification data displayed in terminal, eliminating need for manual confirmation steps
- 🚀 **Automated Workflow Gap Prevention** - Detects deployment script modifications and prevents self-modification issues during deployment
- ✅ **Complete Deployment Transparency** - Every step documented with clear success/failure indicators and actionable guidance

### Enhanced Agent Rules Integration (Jun 22, 2025) - `dc68c6a`
- 🔧 **SwiftGoNC1-style Integration** - Converted agent-rules to proper git submodule following successful SwiftGoNC1 pattern
- 🚀 **Enhanced Deployment Script** - New `deploy-changes-enhanced.sh` with comprehensive submodule management and coordination
- 🔗 **Project Rules Symlink** - Added root-level `project-rules` symlink for better Copilot/Claude accessibility to deployment workflows
- 📋 **Coordinated Updates** - `/test` and `/deploy` commands now handle both main repository and agent-rules submodule changes
- ⚡ **Upstream Sync Capability** - Can pull improvements from steipete/agent-rules while preserving custom project rules
- 📊 **Comprehensive Reporting** - Enhanced deployment verification includes submodule status and git coordination details

### Repository Template Cleanup (Jun 21, 2025) - `eea2d2c`
- 🧹 **Removed template files** - Deleted unnecessary `FUNDING.yml` and `dependabot.yml` files from `.github/` directory
- 🎯 **Simplified project structure** - Focused repository on core BGG analysis functionality without template complexity
- ✅ **Clean starting point** - Eliminated boilerplate files not relevant to this specific project
- 📁 **Streamlined configuration** - Repository now contains only project-specific GitHub configuration

### GitHub Workflow Cleanup (Jun 21, 2025) - `2a7be99`
- 🧹 **Removed failing Algolia workflow** - Eliminated problematic `.github/workflows/index.yml` that was causing hourly GitHub Actions failures
- 🔧 **Repository cleanup** - Removed dependencies on non-existent `scripts/download_and_index.py` and `scripts/requirements.txt`
- ✅ **Improved stability** - No more failed workflow notifications, cleaner repository status
- 🎯 **Focus on core functionality** - Repository now focuses solely on BGG data analysis without external indexing dependencies

### Update Deployment Workflow Automation (Jun 20, 2025) - `8e9a287`
- 🚀 **Agent-driven deployment** - Implemented `/deploy` and `/test` command automation using agent rules
- 🔧 **Streamlined workflows** - Created comprehensive test and deployment scripts with Python environment validation
- 📝 **Documentation integration** - Automated README updates as part of deployment process
- 🐍 **Python-specific checks** - BGG API connectivity testing, dependency validation, and code quality checks
- 🎨 **Enhanced output** - Color-coded terminal output for better development experience on macOS
