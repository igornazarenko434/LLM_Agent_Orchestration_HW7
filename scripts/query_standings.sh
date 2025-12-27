#!/usr/bin/env bash
#
# query_standings.sh - Query current league standings
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"

LM_URL=""
OUTPUT_JSON=0
SENDER=""
AUTH_TOKEN=""

main() {
    log_header "League Standings Query"

    while [[ $# -gt 0 ]]; do
        case "$1" in
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
                log_plain "Usage: ./scripts/query_standings.sh [--sender S] [--auth-token T] [--plain] [--json]"
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

    log_info "Querying standings from League Manager..."

    protocol=$(get_protocol_version)
    conversation_id="standings-$(date +%s)"
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
    payload=$(build_rpc_payload "get_standings" "$params" "1")
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

    standings=$(echo "$response" | jq -r '.result.standings[] | "\(.player_id): \(.points) pts (\(.wins)W \(.draws)D \(.losses)L)"')
    if [[ -z "$standings" ]]; then
        log_warn "No standings found"
        exit 0
    fi
    log_plain "$standings"
}

main "$@"
