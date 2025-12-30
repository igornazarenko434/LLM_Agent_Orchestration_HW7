#!/usr/bin/env bash
#
# build_release_packages.sh - Build SDK wheel and full system archive for release
#
# This script builds both distribution packages:
# 1. SDK wheel (league_sdk-1.0.0-py3-none-any.whl)
# 2. Full system archive (even-odd-league-v1.0.0.tar.gz)
#
# Usage:
#   ./scripts/build_release_packages.sh [--dry-run] [--skip-sdk] [--skip-archive]
#
# Options:
#   --dry-run       Show what would be built without actually building
#   --skip-sdk      Skip building the SDK wheel
#   --skip-archive  Skip building the full system archive
#   --help          Show this help message
#

set -e  # Exit on error

# Load common library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Flags
DRY_RUN=0
SKIP_SDK=0
SKIP_ARCHIVE=0

# ============================================================================
# FUNCTIONS
# ============================================================================

show_help() {
    cat << EOF
Build Release Packages

This script builds both distribution packages for the Even/Odd League system:
1. SDK wheel (~50KB) for developers building custom agents
2. Full system archive (~2MB) for running/evaluating the system

Usage:
  ./scripts/build_release_packages.sh [options]

Options:
  --dry-run       Show what would be built without actually building
  --skip-sdk      Skip building the SDK wheel
  --skip-archive  Skip building the full system archive
  --help, -h      Show this help message

Examples:
  # Build both packages
  ./scripts/build_release_packages.sh

  # Dry run to see what would be built
  ./scripts/build_release_packages.sh --dry-run

  # Build only the SDK wheel
  ./scripts/build_release_packages.sh --skip-archive

  # Build only the full system archive
  ./scripts/build_release_packages.sh --skip-sdk

Output:
  - SDK wheel: SHARED/league_sdk/dist/league_sdk-1.0.0-py3-none-any.whl
  - Full archive: even-odd-league-v1.0.0.tar.gz

Next Steps:
  1. Test both packages (see doc/deployment_guide.md)
  2. Upload to GitHub Releases
EOF
}

log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✅${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}❌${NC} $1"
}

# ============================================================================
# ARGUMENT PARSING
# ============================================================================

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        --skip-sdk)
            SKIP_SDK=1
            shift
            ;;
        --skip-archive)
            SKIP_ARCHIVE=1
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            echo "Run with --help for usage information"
            exit 1
            ;;
    esac
done

# ============================================================================
# MAIN SCRIPT
# ============================================================================

log_info "Even/Odd League - Release Package Builder"
echo ""

# Change to project root
cd "$PROJECT_ROOT"

if [[ $DRY_RUN -eq 1 ]]; then
    log_warning "DRY RUN MODE - No files will be created"
    echo ""
fi

# ============================================================================
# BUILD SDK WHEEL
# ============================================================================

if [[ $SKIP_SDK -eq 0 ]]; then
    log_info "Building SDK wheel..."

    if [[ $DRY_RUN -eq 1 ]]; then
        echo "Would run: cd SHARED/league_sdk && python3 -m build"
        echo "Would create: SHARED/league_sdk/dist/league_sdk-1.0.0-py3-none-any.whl"
    else
        # Check if build tool is installed
        if ! python3 -c "import build" 2>/dev/null; then
            log_warning "Build tool not installed, installing..."
            pip install build
        fi

        # Build wheel
        cd SHARED/league_sdk
        python3 -m build --wheel
        cd "$PROJECT_ROOT"

        # Verify
        if [[ -f "SHARED/league_sdk/dist/league_sdk-1.0.0-py3-none-any.whl" ]]; then
            SIZE=$(du -h "SHARED/league_sdk/dist/league_sdk-1.0.0-py3-none-any.whl" | cut -f1)
            log_success "SDK wheel built: $SIZE"
            log_info "Location: SHARED/league_sdk/dist/league_sdk-1.0.0-py3-none-any.whl"
        else
            log_error "SDK wheel build failed"
            exit 1
        fi
    fi
    echo ""
else
    log_info "Skipping SDK wheel build"
    echo ""
fi

# ============================================================================
# BUILD FULL SYSTEM ARCHIVE
# ============================================================================

if [[ $SKIP_ARCHIVE -eq 0 ]]; then
    log_info "Building full system archive..."

    ARCHIVE_NAME="even-odd-league-v1.0.0.tar.gz"

    if [[ $DRY_RUN -eq 1 ]]; then
        echo "Would create: $ARCHIVE_NAME"
        echo "Would include:"
        echo "  - SHARED/ (SDK + configs + scripts)"
        echo "  - agents/ (7 agents)"
        echo "  - tests/ (588 tests)"
        echo "  - doc/ (documentation)"
        echo "  - scripts/ (12 operational scripts)"
        echo "  - Root files (README, requirements, etc.)"
        echo ""
        echo "Would exclude:"
        echo "  - Cache files (.mypy_cache, .ruff_cache, __pycache__)"
        echo "  - Virtual environments (venv, .venv)"
        echo "  - Git directory (.git)"
        echo "  - Runtime data (SHARED/data, SHARED/logs, SHARED/archive)"
        echo "  - IDE files (.idea)"
    else
        # Remove old archive if exists
        if [[ -f "$ARCHIVE_NAME" ]]; then
            log_warning "Removing old archive: $ARCHIVE_NAME"
            rm "$ARCHIVE_NAME"
        fi

        # Create archive with proper exclusions
        log_info "Creating archive (this may take a moment)..."
        tar -czf "$ARCHIVE_NAME" \
          --exclude='venv' \
          --exclude='.venv' \
          --exclude='.git' \
          --exclude='__pycache__' \
          --exclude='*.pyc' \
          --exclude='.pytest_cache' \
          --exclude='htmlcov' \
          --exclude='.coverage' \
          --exclude='.mypy_cache' \
          --exclude='.ruff_cache' \
          --exclude='.DS_Store' \
          --exclude='dist' \
          --exclude='build' \
          --exclude='*.egg-info' \
          --exclude='SHARED/data' \
          --exclude='SHARED/logs' \
          --exclude='SHARED/archive' \
          --exclude='.idea' \
          --exclude='.quality_check_venv' \
          --exclude='backups' \
          SHARED/ agents/ tests/ doc/ scripts/ \
          README.md requirements.txt pyproject.toml \
          PRD_EvenOddLeague.md Missions_EvenOddLeague.md \
          CONTRIBUTING.md .env.example \
          .gitignore .flake8 .pre-commit-config.yaml \
          mypy.ini verify_installation.py

        # Verify
        if [[ -f "$ARCHIVE_NAME" ]]; then
            SIZE=$(du -h "$ARCHIVE_NAME" | cut -f1)
            FILE_COUNT=$(tar -tzf "$ARCHIVE_NAME" | wc -l | tr -d ' ')
            log_success "Full system archive built: $SIZE ($FILE_COUNT files)"
            log_info "Location: $ARCHIVE_NAME"

            # Check for unwanted cache files
            CACHE_COUNT=$(tar -tzf "$ARCHIVE_NAME" | grep -E '\.mypy_cache|\.ruff_cache|__pycache__|\.DS_Store' | wc -l | tr -d ' ')
            if [[ $CACHE_COUNT -gt 0 ]]; then
                log_warning "Found $CACHE_COUNT cache files in archive (should be 0)"
            else
                log_success "No cache files found in archive"
            fi
        else
            log_error "Full system archive build failed"
            exit 1
        fi
    fi
    echo ""
else
    log_info "Skipping full system archive build"
    echo ""
fi

# ============================================================================
# SUMMARY
# ============================================================================

log_success "Build complete!"
echo ""

if [[ $DRY_RUN -eq 0 ]]; then
    echo "Built packages:"
    if [[ $SKIP_SDK -eq 0 ]]; then
        echo "  1. SDK wheel: SHARED/league_sdk/dist/league_sdk-1.0.0-py3-none-any.whl"
    fi
    if [[ $SKIP_ARCHIVE -eq 0 ]]; then
        echo "  2. Full archive: even-odd-league-v1.0.0.tar.gz"
    fi
    echo ""
    echo "Next steps:"
    echo "  1. Test both packages (see doc/deployment_guide.md § Testing)"
    echo "  2. Create GitHub release: gh release create v1.0.0 ..."
    echo "  3. Upload both files as release assets"
    echo ""
    echo "For detailed instructions, see: doc/deployment_guide.md"
else
    log_info "Dry run complete. No files were created."
fi
