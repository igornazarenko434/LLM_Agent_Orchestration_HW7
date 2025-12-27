#!/usr/bin/env bash
#
# restore_data.sh - Restore league data and logs from backup
#
# Usage:
#   ./scripts/restore_data.sh [options] [backup_name]
#
# Options:
#   --data-only    Restore only data directory
#   --logs-only    Restore only logs directory
#   --force        Skip confirmation prompts
#   --help         Show this help message
#
# If backup_name is not specified, uses the most recent backup
#

# Load common library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

# ============================================================================
# CONFIGURATION
# ============================================================================

RESTORE_DATA=1
RESTORE_LOGS=1
BACKUP_NAME=""
OUTPUT_JSON=0
DATA_BACKUP_USED=""
LOGS_BACKUP_USED=""

# ============================================================================
# FUNCTIONS
# ============================================================================

show_help() {
    print_usage \
        "restore_data.sh" \
        "Restore league data and logs from timestamped backups" \
        "./scripts/restore_data.sh [options] [backup_name]" \
        "./scripts/restore_data.sh" \
        "./scripts/restore_data.sh --data-only" \
        "./scripts/restore_data.sh data_20251227_143022" \
        "./scripts/restore_data.sh --force"

    cat << EOF
Options:
  --data-only       Restore only data directory
  --logs-only       Restore only logs directory
  --force          Skip confirmation prompts
  --plain          Plain text output (no emojis)
  --json           JSON output for automation
  --help           Show this help message

Arguments:
  backup_name      Name of backup to restore (e.g., data_20251227_143022)
                   If not specified, uses most recent backup

Restore Process:
  1. Verify backup exists
  2. Create safety backup of current SHARED/data and SHARED/logs
  3. Restore from selected backup
  4. Verify restoration

Safety:
  - Current data is backed up before restoration
  - Use --force to skip confirmations

Examples:
  # Restore from most recent backup
  ./scripts/restore_data.sh

  # Restore specific backup
  ./scripts/restore_data.sh data_20251227_143022

  # Restore only data
  ./scripts/restore_data.sh --data-only

  # Restore without confirmation
  FORCE=1 ./scripts/restore_data.sh

EOF
}

# List available backups
list_backups() {
    local backups_dir="${PROJECT_ROOT}/backups"

    if [[ ! -d "$backups_dir" ]]; then
        log_warn "No backups directory found: $backups_dir"
        return 1
    fi

    log_info "Available backups:"
    ls -1t "$backups_dir" 2>/dev/null | head -10 | sed 's/^/  - /'

    local count
    count=$(ls -1 "$backups_dir" 2>/dev/null | wc -l | tr -d ' ')
    if [[ $count -gt 10 ]]; then
        log_info "  ... and $((count - 10)) more backups"
    fi
}

# Find backup directory
find_backup() {
    local type="$1"  # "data" or "logs"
    local name="$2"  # backup name or empty for latest

    local backups_dir="${PROJECT_ROOT}/backups"

    if [[ -n "$name" ]]; then
        # Specific backup requested
        local backup_path="${backups_dir}/${name}"
        if [[ -d "$backup_path" ]]; then
            echo "$backup_path"
            return 0
        else
            log_error "Backup not found: $name"
            list_backups
            return 1
        fi
    else
        # Use most recent backup of this type
        local latest
        latest=$(get_latest_backup "$type")
        if [[ -n "$latest" ]]; then
            echo "$latest"
            return 0
        else
            log_error "No $type backups found"
            list_backups
            return 1
        fi
    fi
}

# Restore data directory
restore_data_dir() {
    local backup_path="$1"

    log_info "Restoring data from: $backup_path"

    # Verify backup exists
    if [[ ! -d "$backup_path" ]]; then
        die "Backup directory not found: $backup_path" "$EXIT_CONFIG_ERROR"
    fi

    # Create safety backup of current data
    if [[ -d "$DATA_DIR" ]] && [[ -n "$(ls -A "$DATA_DIR" 2>/dev/null)" ]]; then
        log_info "Creating safety backup of current data..."
        local safety_backup
        safety_backup=$(create_backup_dir "data_safety")
        cp -R "$DATA_DIR"/* "$safety_backup/" 2>/dev/null || true
        log_success "Safety backup created: $safety_backup"
    fi

    # Remove current data directory
    if [[ -d "$DATA_DIR" ]]; then
        rm -rf "$DATA_DIR"
    fi

    # Create data directory
    mkdir -p "$DATA_DIR"

    # Restore from backup
    if cp -R "$backup_path"/* "$DATA_DIR/" 2>/dev/null; then
        log_success "Data restored successfully"

        # Show restored items
        log_info "Restored items:"
        find "$DATA_DIR" -type f | sed "s|^$DATA_DIR/|  - |" | head -10
        local count
        count=$(find "$DATA_DIR" -type f | wc -l | tr -d ' ')
        if [[ $count -gt 10 ]]; then
            log_info "  ... and $((count - 10)) more files"
        fi
    else
        die "Failed to restore data directory" "$EXIT_RUNTIME_ERROR"
    fi
}

# Restore logs directory
restore_logs_dir() {
    local backup_path="$1"

    log_info "Restoring logs from: $backup_path"

    # Verify backup exists
    if [[ ! -d "$backup_path" ]]; then
        die "Backup directory not found: $backup_path" "$EXIT_CONFIG_ERROR"
    fi

    # Create safety backup of current logs
    if [[ -d "$LOGS_ROOT" ]] && [[ -n "$(ls -A "$LOGS_ROOT" 2>/dev/null)" ]]; then
        log_info "Creating safety backup of current logs..."
        local safety_backup
        safety_backup=$(create_backup_dir "logs_safety")
        cp -R "$LOGS_ROOT"/* "$safety_backup/" 2>/dev/null || true
        log_success "Safety backup created: $safety_backup"
    fi

    # Remove current logs directory
    if [[ -d "$LOGS_ROOT" ]]; then
        rm -rf "$LOGS_ROOT"
    fi

    # Create logs directory
    mkdir -p "$LOGS_ROOT"

    # Restore from backup
    if cp -R "$backup_path"/* "$LOGS_ROOT/" 2>/dev/null; then
        log_success "Logs restored successfully"

        # Show restored items
        log_info "Restored items:"
        find "$LOGS_ROOT" -type f | sed "s|^$LOGS_ROOT/|  - |" | head -10
        local count
        count=$(find "$LOGS_ROOT" -type f | wc -l | tr -d ' ')
        if [[ $count -gt 10 ]]; then
            log_info "  ... and $((count - 10)) more files"
        fi
    else
        die "Failed to restore logs directory" "$EXIT_RUNTIME_ERROR"
    fi
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --data-only)
                RESTORE_LOGS=0
                shift
                ;;
            --logs-only)
                RESTORE_DATA=0
                shift
                ;;
            --force)
                FORCE=1
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
            -*)
                log_error "Unknown option: $1"
                log_plain ""
                log_plain "Use --help for usage information"
                exit "$EXIT_CONFIG_ERROR"
                ;;
            *)
                # Assume this is the backup name
                BACKUP_NAME="$1"
                shift
                ;;
        esac
    done

    log_header "League Data Restoration"

    # List available backups
    list_backups

    # Show what will be restored
    if [[ $RESTORE_DATA -eq 1 ]] && [[ $RESTORE_LOGS -eq 1 ]]; then
        log_info "Will restore: SHARED/data/ and SHARED/logs/"
    elif [[ $RESTORE_DATA -eq 1 ]]; then
        log_info "Will restore: SHARED/data/ only"
    elif [[ $RESTORE_LOGS -eq 1 ]]; then
        log_info "Will restore: SHARED/logs/ only"
    else
        log_error "Nothing to restore (both --data-only and --logs-only specified)"
        exit "$EXIT_CONFIG_ERROR"
    fi

    # Confirm action
    log_warn "This will REPLACE current SHARED/data and SHARED/logs with backup"
    if ! confirm "Proceed with restoration?"; then
        log_info "Restoration cancelled"
        exit 0
    fi

    # Restore data directory
    if [[ $RESTORE_DATA -eq 1 ]]; then
        DATA_BACKUP_USED=$(find_backup "data" "$BACKUP_NAME") || exit "$EXIT_CONFIG_ERROR"
        restore_data_dir "$DATA_BACKUP_USED"
    fi

    # Restore logs directory
    if [[ $RESTORE_LOGS -eq 1 ]]; then
        LOGS_BACKUP_USED=$(find_backup "logs" "$BACKUP_NAME") || exit "$EXIT_CONFIG_ERROR"
        restore_logs_dir "$LOGS_BACKUP_USED"
    fi

    if [[ $OUTPUT_JSON -eq 1 ]]; then
        jq -n \
            --arg data_backup "${DATA_BACKUP_USED}" \
            --arg logs_backup "${LOGS_BACKUP_USED}" \
            --arg status "success" \
            '{status:$status,data_backup_used:$data_backup,logs_backup_used:$logs_backup}'
        exit 0
    fi

    log_header "Restoration Complete"
    log_success "All data restored successfully"

    # Show next steps
    log_info "Next steps:"
    log_plain "  1. Verify restored data: ls -la SHARED/data/ SHARED/logs/"
    log_plain "  2. Check safety backups: ls -la backups/*_safety_*"
    log_plain "  3. Restart agents if needed"
}

# Run main function
main "$@"
