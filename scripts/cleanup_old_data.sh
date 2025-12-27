#!/usr/bin/env bash
#
# cleanup_old_data.sh - Clean up old backups, logs, and data
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/lib/common.sh"

# Keep files newer than this many days
KEEP_DAYS=7
DRY_RUN=0
OUTPUT_JSON=0

show_help() {
    cat << EOF
cleanup_old_data.sh - Clean up old files

Usage:
  ./scripts/cleanup_old_data.sh [options] [days]

Arguments:
  days       Keep files newer than this (default: 7)

Options:
  --dry-run  Show what would be deleted without deleting
  --plain    Plain text output (no emojis)
  --json     JSON output for automation
  --help     Show this help

Examples:
  ./scripts/cleanup_old_data.sh --dry-run
  ./scripts/cleanup_old_data.sh 30
  ./scripts/cleanup_old_data.sh --dry-run 14

EOF
}

main() {
    # Parse options first
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --dry-run)
                DRY_RUN=1
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
            [0-9]*)
                KEEP_DAYS="$1"
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                shift
                ;;
        esac
    done

    log_header "Cleanup Old Data (keep ${KEEP_DAYS} days)"

    if [[ $DRY_RUN -eq 1 ]]; then
        log_warn "DRY RUN MODE - No files will be deleted"
    fi

    local backups_deleted=0
    local logs_deleted=0

    # Clean old backups
    if [[ -d "${PROJECT_ROOT}/backups" ]]; then
        local old_backups
        old_backups=$(find "${PROJECT_ROOT}/backups" -type d -mtime "+${KEEP_DAYS}" 2>/dev/null | wc -l | tr -d ' ')
        if [[ $old_backups -gt 0 ]]; then
            log_info "Found $old_backups old backup(s)"
            if [[ $DRY_RUN -eq 0 ]]; then
                find "${PROJECT_ROOT}/backups" -type d -mtime "+${KEEP_DAYS}" -exec rm -rf {} + 2>/dev/null || true
                log_success "Cleaned up old backups"
                backups_deleted=$old_backups
            fi
        else
            log_success "No old backups to clean"
        fi
    fi

    # Clean old logs
    if [[ -d "$LOGS_ROOT" ]]; then
        local old_logs
        old_logs=$(find "$LOGS_ROOT" -type f \( -name "*.log" -o -name "*.jsonl" \) -mtime "+${KEEP_DAYS}" 2>/dev/null | wc -l | tr -d ' ')
        if [[ $old_logs -gt 0 ]]; then
            log_info "Found $old_logs old log file(s)"
            if [[ $DRY_RUN -eq 0 ]]; then
                find "$LOGS_ROOT" -type f \( -name "*.log" -o -name "*.jsonl" \) -mtime "+${KEEP_DAYS}" -delete 2>/dev/null || true
                log_success "Cleaned up old logs"
                logs_deleted=$old_logs
            fi
        else
            log_success "No old logs to clean"
        fi
    fi

    if [[ $OUTPUT_JSON -eq 1 ]]; then
        jq -n \
            --argjson backups_deleted "$backups_deleted" \
            --argjson logs_deleted "$logs_deleted" \
            --argjson dry_run "$DRY_RUN" \
            '{backups_deleted:$backups_deleted,logs_deleted:$logs_deleted,dry_run:$dry_run}'
    fi
}

main "$@"
