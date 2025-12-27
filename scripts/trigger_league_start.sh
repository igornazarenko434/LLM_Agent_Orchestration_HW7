#!/usr/bin/env bash
#
# trigger_league_start.sh - Trigger league to start matches
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"

LM_URL=""
OUTPUT_JSON=0
LEAGUE_ID=""
SENDER=""
AUTH_TOKEN=""

main() {
    log_header "Triggering League Start"

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --league-id)
                LEAGUE_ID="$2"
                shift 2
                ;;
            --sender)
                SENDER="$2"
                shift 2
                ;;
            --auth-token)
                AUTH_TOKEN="$2"
                shift 2
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
                log_plain "Usage: ./scripts/trigger_league_start.sh [--league-id ID] [--sender S] [--auth-token T] [--plain] [--json]"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit "$EXIT_CONFIG_ERROR"
                ;;
        esac
    done

    LM_URL=$(get_league_manager_endpoint)
    if [[ -z "$LM_URL" ]]; then
        log_error "League Manager endpoint not found in config"
        exit "$EXIT_CONFIG_ERROR"
    fi

    if ! check_health "$(endpoint_to_health "$LM_URL")" 2; then
        log_error "League Manager is not running"
        exit "$EXIT_NETWORK_ERROR"
    fi

    log_info "Sending start command to League Manager..."

    protocol=$(get_protocol_version)
    conversation_id="start-league-$(date +%s)"
    params=$(jq -n \
        --arg protocol "$protocol" \
        --arg conversation_id "$conversation_id" \
        --arg league_id "$LEAGUE_ID" \
        --arg sender "$SENDER" \
        --arg auth_token "$AUTH_TOKEN" \
        '{
            protocol:$protocol,
            conversation_id:$conversation_id
        }
        + (if $league_id != "" then {league_id:$league_id} else {} end)
        + (if $sender != "" then {sender:$sender} else {} end)
        + (if $auth_token != "" then {auth_token:$auth_token} else {} end)')

    payload=$(build_rpc_payload "start_league" "$params" "1")
    response=$(mcp_post "$LM_URL" "$payload" 20)

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

    total_rounds=$(echo "$response" | jq -r '.result.total_rounds')
    total_matches=$(echo "$response" | jq -r '.result.total_matches')
    players_count=$(echo "$response" | jq -r '.result.players_count')
    referees_count=$(echo "$response" | jq -r '.result.referees_count')
    log_success "League started: ${total_rounds} rounds, ${total_matches} matches"
    log_info "Players: ${players_count}, Referees: ${referees_count}"
}

main "$@"
