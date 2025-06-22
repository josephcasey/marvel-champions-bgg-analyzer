# Agent Rules Integration Plan

## Current Situation
- agent-rules directory exists as a separate git repository (not submodule)
- deploy.mdc changes are not committed by main project deployment
- No coordination between main repo and agent-rules updates

## Option 1: Proper Submodule Integration (Recommended)

### Steps to implement:
1. Remove current agent-rules directory
2. Add it as proper git submodule
3. Update deployment script to handle submodule updates
4. Coordinate documentation updates

```bash
# 1. Remove and re-add as submodule
rm -rf agent-rules
git submodule add https://github.com/steipete/agent-rules.git agent-rules

# 2. Create .gitmodules file with proper configuration
git add .gitmodules agent-rules
git commit -m "Add agent-rules as git submodule"
```

### Benefits:
- Proper version control integration
- Coordinated updates between main repo and agent rules
- Better tracking of agent rule changes
- Follows SwiftGoNC1 best practices

## Option 2: Keep Current Setup (Simpler)

### Accept current behavior:
- agent-rules changes are managed separately
- deploy.mdc updates require separate commits in agent-rules repo
- Main project deployment focuses only on main repo files

### Update deploy script to clarify this:
- Add note that agent-rules changes require separate management
- Document the two-repo workflow

## Option 3: Copy Key Rules to Main Repo

### Move essential rules to main project:
```bash
mkdir -p .cursor/rules
cp agent-rules/project-rules/deploy.mdc .cursor/rules/
cp agent-rules/project-rules/test.mdc .cursor/rules/
```

### Benefits:
- All project rules tracked in main repo
- Single deployment workflow
- No submodule complexity

### Drawbacks:
- Lose connection to upstream agent-rules updates
- Manual sync required for rule improvements

## Recommendation: Option 1 (Proper Submodule)

This follows the SwiftGoNC1 pattern and provides:
- Best version control practices
- Coordinated documentation updates
- Future-proof agent rules integration
- Maintains connection to upstream improvements

## Implementation Steps

1. **Backup current agent-rules customizations**
2. **Convert to proper submodule**
3. **Update deployment workflow**
4. **Test integrated deployment**
5. **Update documentation**
