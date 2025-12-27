#!/usr/bin/env bash
#
# analyze_logs.sh - Analyze league logs for errors and patterns
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"

ERROR_PATTERN="ERROR|FAILED|Exception"
WARN_PATTERN="WARN|WARNING"
OUTPUT_JSON=0
SEARCH_PATTERN=""

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
            --help|-h)
                log_plain "Usage: ./scripts/analyze_logs.sh [--plain] [--json] [pattern]"
                exit 0
                ;;
            *)
                SEARCH_PATTERN="$1"
                shift
                ;;
        esac
    done

    log_header "Log Analysis"

    if [[ ! -d "$LOGS_ROOT" ]]; then
        log_error "Logs directory not found: $LOGS_ROOT"
        exit "$EXIT_CONFIG_ERROR"
    fi

    log_files=()
    while IFS= read -r file; do
        log_files+=("$file")
    done < <(find "$LOGS_ROOT" -type f \( -name "*.jsonl" -o -name "*.log" \) 2>/dev/null)
    if [[ ${#log_files[@]} -eq 0 ]]; then
        log_warn "No log files found in ${LOGS_ROOT}"
        exit 0
    fi

    if [[ -n "$SEARCH_PATTERN" ]]; then
        if command -v rg &> /dev/null; then
            matches=$(rg -n "$SEARCH_PATTERN" "${log_files[@]}" || true)
        else
            matches=$(grep -nE "$SEARCH_PATTERN" "${log_files[@]}" 2>/dev/null || true)
        fi

        match_count=$(echo "$matches" | sed '/^$/d' | wc -l | tr -d ' ')

        if [[ $OUTPUT_JSON -eq 1 ]]; then
            jq -n \
                --arg pattern "$SEARCH_PATTERN" \
                --argjson count "$match_count" \
                --argjson files "${#log_files[@]}" \
                '{pattern:$pattern,match_count:$count,files_scanned:$files}'
            exit 0
        fi

        if [[ $match_count -eq 0 ]]; then
            log_success "No matches for pattern: ${SEARCH_PATTERN}"
            exit 0
        fi

        log_info "Matches for pattern: ${SEARCH_PATTERN}"
        log_plain "$matches"
        exit 0
    fi

    # Default summary mode
    local error_count=0
    local warn_count=0

    for log_file in "${log_files[@]}"; do
        if [[ -f "$log_file" ]]; then
            local file_errors
            local file_warns
            file_errors=$(grep -cE "$ERROR_PATTERN" "$log_file" 2>/dev/null || echo "0")
            file_warns=$(grep -cE "$WARN_PATTERN" "$log_file" 2>/dev/null || echo "0")

            file_errors=$(echo "$file_errors" | tr -d '\n\r ')
            file_warns=$(echo "$file_warns" | tr -d '\n\r ')

            error_count=$((error_count + file_errors))
            warn_count=$((warn_count + file_warns))

            if [[ $file_errors -gt 0 ]] || [[ $file_warns -gt 0 ]]; then
                log_info "$(basename "$log_file"): $file_errors errors, $file_warns warnings"
            fi
        fi
    done

    log_plain ""
    if [[ $OUTPUT_JSON -eq 1 ]]; then
        jq -n \
            --argjson errors "$error_count" \
            --argjson warnings "$warn_count" \
            '{errors:$errors,warnings:$warnings}'
        exit 0
    fi

    if [[ $error_count -eq 0 ]] && [[ $warn_count -eq 0 ]]; then
        log_success "No errors or warnings found in logs"
    else
        log_warn "Found $error_count errors and $warn_count warnings"
        log_info "Review individual log files for details"
    fi
}

main "$@"
