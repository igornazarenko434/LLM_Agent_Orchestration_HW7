#!/usr/bin/env bash
#
# verify_configs.sh - Verify all configuration files for Even/Odd League
#
# Usage:
#   ./scripts/verify_configs.sh [options]
#
# Options:
#   --verbose, -v    Show detailed validation results
#   --json           Output results as JSON
#   --plain          Plain text output (no emojis)
#   --help, -h       Show this help message
#
# Exit Codes:
#   0 - All configs valid
#   1 - One or more configs invalid or missing
#

# Load common library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

# ============================================================================
# CONFIGURATION
# ============================================================================

VERBOSE=0
OUTPUT_JSON=0

# Config files to check (name:path format)
CONFIG_FILES=(
    "system:SHARED/config/system.json"
    "agents:SHARED/config/agents/agents_config.json"
    "referee_defaults:SHARED/config/defaults/referee.json"
    "player_defaults:SHARED/config/defaults/player.json"
    "league:SHARED/config/leagues/league_2025_even_odd.json"
)

# ============================================================================
# FUNCTIONS
# ============================================================================

show_help() {
    print_usage \
        "verify_configs.sh" \
        "Verify all configuration files for Even/Odd League" \
        "./scripts/verify_configs.sh [options]" \
        "./scripts/verify_configs.sh" \
        "./scripts/verify_configs.sh --verbose" \
        "./scripts/verify_configs.sh --json"

    cat << EOF
Options:
  --verbose, -v    Show detailed validation results for each config
  --json           Output validation results as JSON
  --plain          Plain text output (no emojis)
  --help, -h       Show this help message

Validated Configs:
  - System configuration (system.json)
  - Agents configuration (agents_config.json)
  - Referee defaults (defaults/referee.json)
  - Player defaults (defaults/player.json)
  - League configuration (leagues/*.json)

Exit Codes:
  0 - All configurations valid
  1 - One or more configurations invalid or missing

Examples:
  # Basic validation
  ./scripts/verify_configs.sh

  # Verbose output with details
  ./scripts/verify_configs.sh --verbose

  # JSON output for automation
  ./scripts/verify_configs.sh --json

EOF
}

# Validate a single JSON config file
validate_config() {
    local name="$1"
    local path="$2"
    local full_path="${PROJECT_ROOT}/$path"

    # Check if file exists
    if [[ ! -f "$full_path" ]]; then
        if [[ $OUTPUT_JSON -eq 0 ]]; then
            log_error "$name config not found: $path"
        fi
        echo "missing"
        return 1
    fi

    # Check if file is valid JSON
    if ! python3 -m json.tool "$full_path" > /dev/null 2>&1; then
        if [[ $OUTPUT_JSON -eq 0 ]]; then
            log_error "$name config is invalid JSON: $path"
        fi
        echo "invalid"
        return 1
    fi

    # File is valid
    if [[ $VERBOSE -eq 1 ]] && [[ $OUTPUT_JSON -eq 0 ]]; then
        log_success "$name config is valid: $path" >&2
    fi
    echo "valid"
    return 0
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --verbose|-v)
                VERBOSE=1
                shift
                ;;
            --json)
                OUTPUT_JSON=1
                set_output_mode json
                shift
                ;;
            --plain)
                set_output_mode plain
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                log_plain ""
                log_plain "Use --help for usage information"
                exit "$EXIT_CONFIG_ERROR"
                ;;
        esac
    done

    if [[ $OUTPUT_JSON -eq 0 ]]; then
        log_header "Configuration Verification"
    fi

    # Validate each config file
    local -a results
    local all_valid=1

    for config_spec in "${CONFIG_FILES[@]}"; do
        # Split on first colon only
        name="${config_spec%%:*}"
        path="${config_spec#*:}"

        status=$(validate_config "$name" "$path")
        results+=("$name:$path:$status")

        if [[ "$status" != "valid" ]]; then
            all_valid=0
        fi
    done

    # Output results
    if [[ $OUTPUT_JSON -eq 1 ]]; then
        echo "{"
        echo "  \"timestamp\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\","
        echo "  \"configs\": ["

        local first=1
        for result in "${results[@]}"; do
            name="${result%%:*}"
            rest="${result#*:}"
            path="${rest%%:*}"
            status="${rest#*:}"

            if [[ $first -eq 0 ]]; then
                echo ","
            fi
            first=0

            echo -n "    {\"name\": \"$name\", \"path\": \"$path\", \"status\": \"$status\"}"
        done

        echo ""
        echo "  ],"
        echo "  \"summary\": {"
        echo "    \"all_valid\": $([[ $all_valid -eq 1 ]] && echo "true" || echo "false"),"
        echo "    \"total\": ${#results[@]}"
        echo "  }"
        echo "}"
    else
        log_plain ""
        if [[ $all_valid -eq 1 ]]; then
            log_success "All ${#results[@]} configuration files are valid"
            exit 0
        else
            log_error "Some configuration files are invalid or missing"
            log_info "Fix configuration errors before starting the league"
            exit 1
        fi
    fi

    if [[ $all_valid -eq 0 ]]; then
        exit 1
    fi
}

# Run main function
main "$@"
