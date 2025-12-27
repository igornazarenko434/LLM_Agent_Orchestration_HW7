#!/usr/bin/env bash
#
# view_match_state.sh - View state of a specific match
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"

MATCH_ID=""
REFEREE_ID="REF01"
ENDPOINT=""
SENDER=""
AUTH_TOKEN=""
OUTPUT_JSON=0

main() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --referee-id)
                REFEREE_ID="$2"
                shift 2
                ;;
            --endpoint)
                ENDPOINT="$2"
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
                log_plain "Usage: ./scripts/view_match_state.sh <match_id> [--referee-id ID] [--endpoint URL] [--sender S] [--auth-token T] [--plain] [--json]"
                exit 0
                ;;
            *)
                if [[ -z "$MATCH_ID" ]]; then
                    MATCH_ID="$1"
                    shift
                else
                    log_error "Unknown option: $1"
                    exit "$EXIT_CONFIG_ERROR"
                fi
                ;;
        esac
    done

    if [[ -z "$MATCH_ID" ]]; then
        log_error "Match ID required"
        log_plain "Usage: ./scripts/view_match_state.sh <match_id> [--referee-id ID] [--endpoint URL] [--sender S] [--auth-token T]"
        exit "$EXIT_CONFIG_ERROR"
    fi

    if [[ -z "$ENDPOINT" ]]; then
        ENDPOINT=$(get_referee_endpoint "$REFEREE_ID")
    fi

    if [[ -z "$ENDPOINT" ]]; then
        log_error "Referee endpoint not found in config"
        exit "$EXIT_CONFIG_ERROR"
    fi

    if [[ -z "$SENDER" ]] || [[ -z "$AUTH_TOKEN" ]]; then
        log_error "Sender and auth token are required for get_match_state"
        log_plain "Provide --sender and --auth-token (e.g., sender=player:P01)"
        exit "$EXIT_AUTH_ERROR"
    fi

    if ! check_health "$(endpoint_to_health "$ENDPOINT")" 2; then
        log_error "Referee is not responding"
        exit "$EXIT_NETWORK_ERROR"
    fi

    log_header "Match State: $MATCH_ID"
    log_info "Querying match state..."

    protocol=$(get_protocol_version)
    conversation_id="match-state-$(date +%s)"
    params=$(jq -n \
        --arg protocol "$protocol" \
        --arg conversation_id "$conversation_id" \
        --arg match_id "$MATCH_ID" \
        --arg sender "$SENDER" \
        --arg auth_token "$AUTH_TOKEN" \
        '{
            protocol:$protocol,
            conversation_id:$conversation_id,
            match_id:$match_id,
            sender:$sender,
            auth_token:$auth_token
        }')
    payload=$(build_rpc_payload "get_match_state" "$params" "1")
    response=$(mcp_post "$ENDPOINT" "$payload" 10)

    if [[ -z "$response" ]]; then
        log_error "Empty response from referee"
        exit "$EXIT_RUNTIME_ERROR"
    fi

    if echo "$response" | jq -e '.error != null' >/dev/null 2>&1; then
        error_msg=$(echo "$response" | jq -r '.error.message')
        log_error "Referee error: ${error_msg}"
        if [[ $OUTPUT_JSON -eq 1 ]]; then
            echo "$response"
        fi
        exit "$EXIT_RUNTIME_ERROR"
    fi

    if [[ $OUTPUT_JSON -eq 1 ]]; then
        echo "$response"
        exit 0
    fi

    echo "$response" | jq '.result.match'
}

main "$@"
