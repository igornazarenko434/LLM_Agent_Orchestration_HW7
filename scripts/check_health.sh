#!/usr/bin/env bash
#
# Check health of all league agents
#
# Usage:
#   ./scripts/check_health.sh [options]
#
# Options:
#   --json       Output as JSON
#   --plain      Plain text output (no emojis)
#   --quiet      Only show failures
#   --help       Show this help message
#
# Examples:
#   ./scripts/check_health.sh
#   ./scripts/check_health.sh --json
#   ./scripts/check_health.sh --quiet
#   ./scripts/check_health.sh --plain
#

# Load common library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

# ============================================================================
# CONFIGURATION
# ============================================================================

OUTPUT_JSON=0
QUIET_MODE=0

# ============================================================================
# FUNCTIONS
# ============================================================================

show_help() {
    print_usage \
        "check_health.sh" \
        "Check health status of all league agents" \
        "./scripts/check_health.sh [options]" \
        "./scripts/check_health.sh" \
        "./scripts/check_health.sh --json" \
        "./scripts/check_health.sh --quiet"

    cat << EOF
Options:
  --json       Output health status as JSON
  --plain      Plain text output (no emojis)
  --quiet      Only show failures (silent on success)
  --help       Show this help message

Checked Endpoints:
  - League Manager (from agents_config.json)
  - Referees (from agents_config.json)
  - Players (from agents_config.json)

Exit Codes:
  0 - All agents healthy
  1 - One or more agents unhealthy

EOF
}

# Check single endpoint
check_endpoint() {
    local name="$1"
    local url="$2"

    if check_health "$url" 2; then
        if [[ $QUIET_MODE -eq 0 ]]; then
            log_success "$name is healthy"
        fi
        return 0
    else
        log_error "$name is NOT responding"
        return 1
    fi
}

# Output JSON health status
output_json() {
    local -a results=("$@")
    local healthy=0
    local unhealthy=0

    echo "{"
    echo '  "timestamp": "'$(date -u +"%Y-%m-%dT%H:%M:%SZ")'",'
    echo '  "agents": ['

    local first=1
    for result in "${results[@]}"; do
        # Split on first colon only
        name="${result%%:*}"
        status="${result#*:}"
        if [[ $first -eq 0 ]]; then
            echo ","
        fi
        first=0

        if [[ "$status" == "healthy" ]]; then
            ((healthy++))
            echo -n "    {\"name\": \"$name\", \"status\": \"healthy\"}"
        else
            ((unhealthy++))
            echo -n "    {\"name\": \"$name\", \"status\": \"unhealthy\"}"
        fi
    done

    echo ""
    echo "  ],"
    echo "  \"summary\": {"
    echo "    \"total\": $((healthy + unhealthy)),"
    echo "    \"healthy\": $healthy,"
    echo "    \"unhealthy\": $unhealthy"
    echo "  }"
    echo "}"
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --json)
                OUTPUT_JSON=1
                set_output_mode json
                shift
                ;;
            --plain)
                set_output_mode plain
                shift
                ;;
            --quiet|-q)
                QUIET_MODE=1
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
        log_header "League Health Check"
    fi

    local lm_endpoint
    local lm_health
    lm_endpoint=$(get_league_manager_endpoint)
    lm_health=$(endpoint_to_health "$lm_endpoint")

    AGENTS=()
    if [[ -n "$lm_health" ]]; then
        AGENTS+=("League Manager:${lm_health}")
    fi

    for ref_id in $(get_all_referees); do
        ref_endpoint=$(get_referee_endpoint "$ref_id")
        ref_health=$(endpoint_to_health "$ref_endpoint")
        if [[ -n "$ref_health" ]]; then
            AGENTS+=("Referee ${ref_id}:${ref_health}")
        fi
    done

    for player_id in $(get_all_players); do
        player_endpoint=$(get_player_endpoint "$player_id")
        player_health=$(endpoint_to_health "$player_endpoint")
        if [[ -n "$player_health" ]]; then
            AGENTS+=("Player ${player_id}:${player_health}")
        fi
    done

    if [[ ${#AGENTS[@]} -eq 0 ]]; then
        log_error "No agent endpoints found in config"
        exit "$EXIT_CONFIG_ERROR"
    fi

    # Check each agent
    local -a results
    local all_healthy=1

    for agent_spec in "${AGENTS[@]}"; do
        # Split on first colon only to preserve URL structure
        name="${agent_spec%%:*}"
        url="${agent_spec#*:}"

        if check_endpoint "$name" "$url"; then
            results+=("$name:healthy")
        else
            results+=("$name:unhealthy")
            all_healthy=0
        fi
    done

    # Output results
    if [[ $OUTPUT_JSON -eq 1 ]]; then
        output_json "${results[@]}"
    else
        log_plain ""
        if [[ $all_healthy -eq 1 ]]; then
            log_success "All agents are healthy"
            exit 0
        else
            log_error "Some agents are unhealthy"
        log_info "Check individual agent logs in SHARED/logs/agents/ directory"
            exit 1
        fi
    fi

    if [[ $all_healthy -eq 0 ]]; then
        exit 1
    fi
}

# Run main function
main "$@"
