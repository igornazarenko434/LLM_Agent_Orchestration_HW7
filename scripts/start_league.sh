#!/usr/bin/env bash
#
# Start all agents for Even/Odd League
#
# Usage:
#   ./scripts/start_league.sh [league_id]
#
# Arguments:
#   league_id    League ID to start (default: auto-detected or league_2025_even_odd)
#
# Options:
#   --help       Show this help message
#
# Examples:
#   ./scripts/start_league.sh
#   ./scripts/start_league.sh league_1
#   ./scripts/start_league.sh --help
#

# Load common library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

# ============================================================================
# CONFIGURATION
# ============================================================================

LEAGUE_ID="league_2025_even_odd"
PID_FILE="/tmp/league_pids.txt"
OUTPUT_MODE="normal"  # normal, plain, json, verbose, quiet
DRY_RUN=0
AGENT_FLAGS=""  # Flags to pass to agents

# ============================================================================
# FUNCTIONS
# ============================================================================

show_help() {
    print_usage \
        "start_league.sh" \
        "Start all agents for Even/Odd League multi-agent system" \
        "./scripts/start_league.sh [options] [league_id]" \
        "./scripts/start_league.sh" \
        "./scripts/start_league.sh --verbose league_1" \
        "./scripts/start_league.sh --plain --dry-run"

    cat << EOF
Arguments:
  league_id         League ID to start (default: league_2025_even_odd)

Options:
  --verbose, -v     Verbose output (passes --verbose to all agents)
  --quiet, -q       Quiet mode - only show errors (passes --quiet to all agents)
  --plain           Plain text output - no emojis, screen reader compatible
                    (passes --plain to all agents)
  --json            JSON output for automation (passes --json to all agents)
  --dry-run         Show what would be started without actually starting
  --help, -h        Show this help message

Output Modes:
  The output mode flags (--verbose, --quiet, --plain) are passed to all
  agents when they start, so they'll use the same output format.

Started Agents:
  - League Manager (port 8000)
  - Referee REF01 (port 8001)
  - Referee REF02 (port 8002)
  - Player P01 (port 8101)
  - Player P02 (port 8102)
  - Player P03 (port 8103)
  - Player P04 (port 8104)

Logs:
  - SHARED/logs/agents/league_manager.log
  - SHARED/logs/agents/referee_REF01.log
  - SHARED/logs/agents/referee_REF02.log
  - SHARED/logs/agents/player_P01.log
  - SHARED/logs/agents/player_P02.log
  - SHARED/logs/agents/player_P03.log
  - SHARED/logs/agents/player_P04.log

Examples:
  # Start league with verbose output
  ./scripts/start_league.sh --verbose

  # Start in screen reader mode (accessibility)
  ./scripts/start_league.sh --plain

  # Dry run - see what would be started
  ./scripts/start_league.sh --dry-run

  # Start specific league with quiet mode
  ./scripts/start_league.sh --quiet league_custom_2025

To Stop:
  ./scripts/stop_league.sh

To Check Health:
  ./scripts/check_health.sh

EOF
}

# Start an agent in background
start_agent() {
    local agent_type="$1"
    local agent_id="$2"
    local port="$3"
    local module="$4"
    local log_file="${LOGS_AGENT_DIR}/${agent_id}.log"

    log_info "Starting $agent_type $agent_id on port $port..." >&2

    # Create log file directory if needed
    mkdir -p "$LOGS_AGENT_DIR"

    # Dry run mode - just show what would be executed
    if [[ $DRY_RUN -eq 1 ]]; then
        log_plain "  [DRY RUN] Would execute: python3 -m $module --league-id $LEAGUE_ID --port $port $AGENT_FLAGS" >&2
        echo "0"  # Return fake PID for dry run
        return 0
    fi

    # Start agent in background with CLI flags
    python3 -m "$module" --league-id "$LEAGUE_ID" --port "$port" $AGENT_FLAGS > "$log_file" 2>&1 &
    local pid=$!

    echo "$pid"
    log_success "Started $agent_id (PID: $pid)" >&2
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --verbose|-v)
                OUTPUT_MODE="verbose"
                AGENT_FLAGS="$AGENT_FLAGS --verbose"
                shift
                ;;
            --quiet|-q)
                OUTPUT_MODE="quiet"
                AGENT_FLAGS="$AGENT_FLAGS --quiet"
                shift
                ;;
            --plain)
                OUTPUT_MODE="plain"
                AGENT_FLAGS="$AGENT_FLAGS --plain"
                set_output_mode plain
                shift
                ;;
            --json)
                OUTPUT_MODE="json"
                AGENT_FLAGS="$AGENT_FLAGS --json"
                set_output_mode json
                shift
                ;;
            --dry-run)
                DRY_RUN=1
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            -*)
                log_error "Unknown option: $1"
                log_plain ""
                log_plain "Use --help for usage information"
                exit "$EXIT_CONFIG_ERROR"
                ;;
            *)
                # Assume this is the league ID
                LEAGUE_ID="$1"
                shift
                ;;
        esac
    done

    # Validate mutually exclusive flags
    if [[ "$OUTPUT_MODE" == "verbose" ]] && [[ "$AGENT_FLAGS" == *"--quiet"* ]]; then
        log_error "--verbose and --quiet are mutually exclusive"
        exit "$EXIT_CONFIG_ERROR"
    fi
    if [[ "$AGENT_FLAGS" == *"--plain"* ]] && [[ "$AGENT_FLAGS" == *"--json"* ]]; then
        log_error "--plain and --json are mutually exclusive"
        exit "$EXIT_CONFIG_ERROR"
    fi

    log_header "Starting Even/Odd League: $LEAGUE_ID"

    if [[ $DRY_RUN -eq 1 ]]; then
        log_warn "DRY RUN MODE - No agents will actually be started"
        log_plain ""
    fi

    # Pre-flight checks
    require_command "python3" "Install Python 3.x"
    require_dir "$CONFIG_DIR" "Config directory"

    # Activate virtual environment
    activate_venv

    # Export PYTHONPATH
    export PYTHONPATH="${PROJECT_ROOT}/SHARED:${PYTHONPATH:-}"

    # Check if agents are already running
    if is_process_running "agents.league_manager.main"; then
        log_warn "League Manager is already running"
        if ! confirm "Stop existing agents and restart?"; then
            log_info "Startup cancelled"
            exit 0
        fi
        log_info "Stopping existing agents..."
        "${SCRIPT_DIR}/stop_league.sh"
        sleep 2
    fi

    # Start League Manager
    HOST=$(get_system_host)
    LM_PORT=$(get_league_manager_port)
    LM_PID=$(start_agent "League Manager" "league_manager" "$LM_PORT" "agents.league_manager.main")
    sleep 2

    # Wait for League Manager to be ready (skip in dry-run)
    if [[ $DRY_RUN -eq 0 ]]; then
        wait_for_service "http://${HOST}:${LM_PORT}/health" "League Manager" 10 || \
            die_network "League Manager failed to start"
    fi

    # Start Referees
    ref_pids=()
    for ref_id in $(get_all_referees); do
        ref_port=$(get_referee_port "$ref_id")
        ref_pid=$(start_agent "Referee" "referee_${ref_id}" "$ref_port" "agents.referee_${ref_id}.main")
        ref_pids+=("$ref_pid")
    done
    if [[ $DRY_RUN -eq 0 ]]; then
        sleep 2
    fi

    # Wait for Referees to be ready (skip in dry-run)
    if [[ $DRY_RUN -eq 0 ]]; then
        for ref_id in $(get_all_referees); do
            ref_port=$(get_referee_port "$ref_id")
            wait_for_service "http://${HOST}:${ref_port}/health" "Referee ${ref_id}" 10 || \
                log_warn "Referee ${ref_id} health check failed (may still be starting)"
        done
    fi

    # Start Players
    player_pids=()
    for player_id in $(get_all_players); do
        player_port=$(get_player_port "$player_id")
        player_pid=$(start_agent "Player" "player_${player_id}" "$player_port" "agents.player_${player_id}.main")
        player_pids+=("$player_pid")
    done
    if [[ $DRY_RUN -eq 0 ]]; then
        sleep 3
    fi

    # Wait for Players to be ready (skip in dry-run)
    if [[ $DRY_RUN -eq 0 ]]; then
        for player_id in $(get_all_players); do
            player_port=$(get_player_port "$player_id")
            wait_for_service "http://${HOST}:${player_port}/health" "Player ${player_id}" 10 || \
                log_warn "Player ${player_id} health check failed (may still be starting)"
        done
    fi

    # Save PIDs for later cleanup (skip in dry-run)
    if [[ $DRY_RUN -eq 0 ]]; then
        echo "$LM_PID ${ref_pids[*]} ${player_pids[*]}" > "$PID_FILE"
    fi

    log_header "All Agents Started Successfully"

    # Display agent endpoints
    log_plain ""
    log_success "League Manager: http://${HOST}:${LM_PORT}  (PID: $LM_PID)"
    for idx in "${!ref_pids[@]}"; do
        ref_id=$(echo "$(get_all_referees)" | awk -v i=$((idx + 1)) '{print $i}')
        ref_port=$(get_referee_port "$ref_id")
        log_success "Referee ${ref_id}:  http://${HOST}:${ref_port}  (PID: ${ref_pids[$idx]})"
    done
    for idx in "${!player_pids[@]}"; do
        player_id=$(echo "$(get_all_players)" | awk -v i=$((idx + 1)) '{print $i}')
        player_port=$(get_player_port "$player_id")
        log_success "Player ${player_id}:     http://${HOST}:${player_port}  (PID: ${player_pids[$idx]})"
    done
    log_plain ""

    # Display next steps
    log_info "Next steps:"
    log_plain "  To stop all agents:  ./scripts/stop_league.sh"
    log_plain "  To check health:     ./scripts/check_health.sh"
    log_plain "  To view logs:        tail -f SHARED/logs/agents/*.log"
    log_plain ""
}

# Run main function
main "$@"
