#!/bin/bash
# Release Preparation Checklist for LogGem v1.0.0

echo "🔍 LogGem v1.0.0 Release Checklist"
echo "=================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_mark="${GREEN}✓${NC}"
cross_mark="${RED}✗${NC}"
warn_mark="${YELLOW}⚠${NC}"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check file exists
check_file() {
    if [ -f "$1" ]; then
        echo -e "${check_mark} $2"
        return 0
    else
        echo -e "${cross_mark} $2 - File not found: $1"
        return 1
    fi
}

# Check version consistency
echo "📋 Version Checks:"
VERSION_PYPROJECT=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)
VERSION_INIT=$(grep '__version__ = ' src/loggem/__init__.py | cut -d'"' -f2)

if [ "$VERSION_PYPROJECT" = "1.0.0" ] && [ "$VERSION_INIT" = "1.0.0" ]; then
    echo -e "${check_mark} Version is 1.0.0 in pyproject.toml and __init__.py"
else
    echo -e "${cross_mark} Version mismatch - pyproject.toml: $VERSION_PYPROJECT, __init__.py: $VERSION_INIT"
fi
echo ""

# Check required files
echo "📁 Required Files:"
check_file "README.md" "README.md exists"
check_file "LICENSE" "LICENSE exists"
check_file "CHANGELOG.md" "CHANGELOG.md exists"
check_file "CONTRIBUTING.md" "CONTRIBUTING.md exists"
check_file "CODE_OF_CONDUCT.md" "CODE_OF_CONDUCT.md exists"
check_file "SECURITY.md" "SECURITY.md exists"
check_file "RELEASE.md" "RELEASE.md exists"
check_file "pyproject.toml" "pyproject.toml exists"
check_file "MANIFEST.in" "MANIFEST.in exists"
check_file ".gitignore" ".gitignore exists"
check_file ".gitattributes" ".gitattributes exists"
echo ""

# Check documentation
echo "📚 Documentation:"
check_file "ARCHITECTURE.md" "ARCHITECTURE.md exists"
check_file "TESTING.md" "TESTING.md exists"
check_file "DEPLOYMENT.md" "DEPLOYMENT.md exists"
check_file "EXAMPLES.md" "EXAMPLES.md exists"
check_file "docs/DOCUMENTATION_INDEX.md" "DOCUMENTATION_INDEX.md exists"
check_file "docs/COVERAGE_REPORT.md" "COVERAGE_REPORT.md exists"
echo ""

# Check GitHub files
echo "🐙 GitHub Files:"
check_file ".github/workflows/ci.yml" "CI workflow exists"
check_file ".github/ISSUE_TEMPLATE/bug_report.md" "Bug report template exists"
check_file ".github/ISSUE_TEMPLATE/feature_request.md" "Feature request template exists"
check_file ".github/PULL_REQUEST_TEMPLATE.md" "PR template exists"
echo ""

# Check if git repo is clean
echo "🧹 Repository Status:"
if [ -d ".git" ]; then
    CHANGED_FILES=$(git status --porcelain | wc -l)
    if [ "$CHANGED_FILES" -eq 0 ]; then
        echo -e "${check_mark} Git repository is clean"
    else
        echo -e "${warn_mark} Git repository has $CHANGED_FILES uncommitted changes"
        echo "Run 'git status' to see them"
    fi
else
    echo -e "${warn_mark} Not a git repository"
fi
echo ""

# Check for required tools
echo "🛠️  Development Tools:"
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${check_mark} Python installed: $PYTHON_VERSION"
else
    echo -e "${cross_mark} Python not found"
fi

if command_exists pytest; then
    echo -e "${check_mark} pytest installed"
else
    echo -e "${warn_mark} pytest not found (install with: pip install pytest)"
fi

if command_exists black; then
    echo -e "${check_mark} black installed"
else
    echo -e "${warn_mark} black not found (install with: pip install black)"
fi

if command_exists ruff; then
    echo -e "${check_mark} ruff installed"
else
    echo -e "${warn_mark} ruff not found (install with: pip install ruff)"
fi
echo ""

# Run tests
echo "🧪 Running Tests:"
if command_exists pytest; then
    echo "Running pytest..."
    pytest tests/ -q --tb=no --no-header 2>/dev/null
    if [ $? -eq 0 ]; then
        echo -e "${check_mark} All tests passed"
    else
        echo -e "${cross_mark} Some tests failed - run 'pytest tests/ -v' for details"
    fi
else
    echo -e "${warn_mark} Skipping tests (pytest not installed)"
fi
echo ""

# Check code formatting
echo "🎨 Code Quality:"
if command_exists black; then
    black --check src/ tests/ >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${check_mark} Code formatting is correct (black)"
    else
        echo -e "${warn_mark} Code needs formatting - run 'black src/ tests/'"
    fi
else
    echo -e "${warn_mark} Skipping black check (not installed)"
fi

if command_exists ruff; then
    ruff check src/ tests/ >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${check_mark} No linting issues (ruff)"
    else
        echo -e "${warn_mark} Linting issues found - run 'ruff check src/ tests/'"
    fi
else
    echo -e "${warn_mark} Skipping ruff check (not installed)"
fi
echo ""

# Final checklist
echo "✅ Final Checklist:"
echo "  - [ ] All tests passing"
echo "  - [ ] Code formatted and linted"
echo "  - [ ] Documentation updated"
echo "  - [ ] CHANGELOG.md updated"
echo "  - [ ] Version bumped to 1.0.0"
echo "  - [ ] All changes committed"
echo "  - [ ] Git tag created: git tag -a v1.0.0 -m 'Release v1.0.0'"
echo "  - [ ] Tag pushed: git push origin v1.0.0"
echo "  - [ ] GitHub release created"
echo ""

echo "=================================="
echo "🚀 Ready to release LogGem v1.0.0!"
echo "=================================="
