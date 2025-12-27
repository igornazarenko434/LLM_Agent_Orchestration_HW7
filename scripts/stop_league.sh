#!/usr/bin/env bash
#
# Stop all league agents gracefully
#
# Usage:
#   ./scripts/stop_league.sh [options]
#
# Options:
#   --force      Force kill without graceful shutdown
#   --plain      Plain text output (no emojis)
#   --json       JSON output for automation
#   --help       Show this help message
#
# Examples:
#   ./scripts/stop_league.sh
#   ./scripts/stop_league.sh --force
#

# Load common library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

# ============================================================================
# CONFIGURATION
# ============================================================================

PID_FILE="/tmp/league_pids.txt"
FORCE_KILL=0
OUTPUT_JSON=0

# ============================================================================
# FUNCTIONS
# ============================================================================

show_help() {
    print_usage \
        "stop_league.sh" \
        "Stop all league agents gracefully (or forcefully)" \
        "./scripts/stop_league.sh [options]" \
        "./scripts/stop_league.sh" \
        "./scripts/stop_league.sh --force"

    cat << EOF
Options:
  --force      Force kill (SIGKILL) without graceful shutdown
  --plain      Plain text output (no emojis)
  --json       JSON output for automation
  --help       Show this help message

Stopped Agents:
  - League Manager
  - Referee REF01
  - Referee REF02
  - Player P01
  - Player P02
  - Player P03
  - Player P04

Process:
  1. Send SIGTERM (graceful shutdown)
  2. Wait 2 seconds
  3. Send SIGKILL if still running (force kill)

EOF
}

# Stop agents by PID
stop_by_pids() {
    local pids="$1"
    local signal="${2:-TERM}"

    log_info "Found PIDs from startup: $pids"

    for pid in $pids; do
        if ps -p "$pid" > /dev/null 2>&1; then
            log_info "Stopping process $pid..."
            kill -"$signal" "$pid" 2>/dev/null || true
        else
            log_info "Process $pid not running (already stopped)"
        fi
    done
}

# Stop agents by process name
stop_by_name() {
    local signal="${1:-TERM}"

    log_info "Searching for league processes..."

    kill_process "agents.league_manager.main" "$signal"
    kill_process "agents.referee_.*\.main" "$signal"
    kill_process "agents.player_.*\.main" "$signal"
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --force)
                FORCE_KILL=1
                shift
                ;;
            --plain)
                set_output_mode plain
                shift
                ;;
            --json)
                OUTPUT_JSON=1
                set_output_mode json
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

    log_header "Stopping All League Agents"

    # Check if any agents are running
    if ! is_process_running "agents.league_manager.main" && \
       ! is_process_running "agents.referee_.*\.main" && \
       ! is_process_running "agents.player_.*\.main"; then
        log_info "No league agents are currently running"
        exit 0
    fi

    # Try to read PIDs from file
    if [[ -f "$PID_FILE" ]]; then
        pids=$(cat "$PID_FILE")

        if [[ $FORCE_KILL -eq 1 ]]; then
            log_warn "Force killing all agents (SIGKILL)"
            stop_by_pids "$pids" "KILL"
        else
            # Graceful shutdown
            log_info "Sending SIGTERM for graceful shutdown..."
            stop_by_pids "$pids" "TERM"

            # Wait for graceful shutdown
            log_info "Waiting for agents to shutdown gracefully..."
            sleep 2

            # Force kill if still running
            for pid in $pids; do
                if ps -p "$pid" > /dev/null 2>&1; then
                    log_warn "Process $pid still running, force killing..."
                    kill -9 "$pid" 2>/dev/null || true
                fi
            done
        fi

        # Remove PID file
        rm -f "$PID_FILE"
    else
        log_warn "No PID file found, searching for processes by name..."

        if [[ $FORCE_KILL -eq 1 ]]; then
            stop_by_name "KILL"
        else
            stop_by_name "TERM"
            sleep 2
            # Force kill stragglers
            stop_by_name "KILL"
        fi
    fi

    # Verify all agents stopped
    sleep 1
    if is_process_running "agents.league_manager.main" || \
       is_process_running "agents.referee_.*\.main" || \
       is_process_running "agents.player_.*\.main"; then
        log_warn "Some agents may still be running"
        log_info "Run with --force to force kill"
        exit "$EXIT_RUNTIME_ERROR"
    fi

    if [[ $OUTPUT_JSON -eq 1 ]]; then
        jq -n '{status:"stopped"}'
        exit 0
    fi

    log_success "All agents stopped successfully"
}

# Run main function
main "$@"
