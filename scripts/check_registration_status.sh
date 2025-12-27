#!/usr/bin/env bash
#
# check_registration_status.sh - Check agent registration status with League Manager
#
# Usage:
#   ./scripts/check_registration_status.sh [options]
#
# Options:
#   --json           Output results as JSON
#   --plain          Plain text output (no emojis)
#   --help, -h       Show this help message
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"

OUTPUT_JSON=0
LM_URL=""
SENDER=""
AUTH_TOKEN=""

show_help() {
    cat << EOF
check_registration_status.sh - Check agent registrations

Usage:
  ./scripts/check_registration_status.sh [options]

Options:
  --json    Output as JSON
  --plain   Plain text output (no emojis)
  --sender  Sender ID (e.g., player:P01)
  --auth-token  Auth token for sender
  --help    Show this help

Examples:
  ./scripts/check_registration_status.sh
  ./scripts/check_registration_status.sh --json

EOF
}

main() {
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
            --sender)
                SENDER="$2"
                shift 2
                ;;
            --auth-token)
                AUTH_TOKEN="$2"
                shift 2
                ;;
            --help|-h) show_help; exit 0 ;;
            *) log_error "Unknown option: $1"; exit 1 ;;
        esac
    done

    log_header "Agent Registration Status"

    LM_URL=$(get_league_manager_endpoint)
    if [[ -z "$LM_URL" ]]; then
        log_error "League Manager endpoint not found in config"
        exit "$EXIT_CONFIG_ERROR"
    fi

    # Check if League Manager is running
    if ! check_health "$(endpoint_to_health "$LM_URL")" 2; then
        log_error "League Manager is not running"
        exit "$EXIT_NETWORK_ERROR"
    fi

    log_info "Checking registrations with League Manager..."

    protocol=$(get_protocol_version)
    conversation_id="reg-status-$(date +%s)"
    params=$(jq -n \
        --arg protocol "$protocol" \
        --arg conversation_id "$conversation_id" \
        --arg sender "$SENDER" \
        --arg auth_token "$AUTH_TOKEN" \
        '{
            protocol:$protocol,
            conversation_id:$conversation_id
        }
        + (if $sender != "" then {sender:$sender} else {} end)
        + (if $auth_token != "" then {auth_token:$auth_token} else {} end)')
    payload=$(build_rpc_payload "get_league_status" "$params" "1")
    response=$(mcp_post "$LM_URL" "$payload" 10)

    if [[ -z "$response" ]]; then
        log_error "Empty response from League Manager"
        exit "$EXIT_RUNTIME_ERROR"
    fi

    if echo "$response" | jq -e '.error != null' >/dev/null 2>&1; then
        error_msg=$(echo "$response" | jq -r '.error.message')
        log_error "League Manager error: ${error_msg}"
        if [[ $OUTPUT_JSON -eq 1 ]]; then
            echo "$response"
        fi
        exit "$EXIT_RUNTIME_ERROR"
    fi

    if [[ $OUTPUT_JSON -eq 1 ]]; then
        echo "$response"
        exit 0
    fi

    league_state=$(echo "$response" | jq -r '.result.status // "UNKNOWN"')
    round_id=$(echo "$response" | jq -r '.result.current_round_id // "N/A"')
    players=$(echo "$response" | jq -r '.result.registered_players | join(", ")')
    referees=$(echo "$response" | jq -r '.result.registered_referees | join(", ")')
    player_count=$(echo "$response" | jq -r '.result.registered_players | length')
    referee_count=$(echo "$response" | jq -r '.result.registered_referees | length')

    log_success "League state: ${league_state} (round: ${round_id})"
    log_info "Registered players (${player_count}): ${players}"
    log_info "Registered referees (${referee_count}): ${referees}"
}

main "$@"
