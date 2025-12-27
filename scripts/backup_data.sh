#!/usr/bin/env bash
#
# backup_data.sh - Backup league data and logs
#
# Usage:
#   ./scripts/backup_data.sh [options]
#
# Options:
#   --data-only    Backup only data directory
#   --logs-only    Backup only logs directory
#   --force        Skip confirmation prompts
#   --help         Show this help message
#
# Creates timestamped backups in:
#   ./backups/data_YYYYMMDD_HHMMSS/
#   ./backups/logs_YYYYMMDD_HHMMSS/
#

# Load common library
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

# ============================================================================
# CONFIGURATION
# ============================================================================

BACKUP_DATA=1
BACKUP_LOGS=1
OUTPUT_JSON=0
DATA_BACKUP_DIR=""
LOGS_BACKUP_DIR=""

# ============================================================================
# FUNCTIONS
# ============================================================================

show_help() {
    print_usage \
        "backup_data.sh" \
        "Backup league data and logs to timestamped directories" \
        "./scripts/backup_data.sh [options]" \
        "./scripts/backup_data.sh" \
        "./scripts/backup_data.sh --data-only" \
        "./scripts/backup_data.sh --logs-only" \
        "./scripts/backup_data.sh --force"

    cat << EOF
Options:
  --data-only       Backup only data directory
  --logs-only       Backup only logs directory
  --force          Skip confirmation prompts
  --plain          Plain text output (no emojis)
  --json           JSON output for automation
  --help           Show this help message

Backup Contents:
  Data Directory:
    - SHARED/data/ (match results, rounds, standings, player history)

  Logs Directory:
    - SHARED/logs/league/*.jsonl (structured logs)
    - SHARED/logs/agents/*.log   (agent stdout logs)

Backup Location:
  ./backups/data_YYYYMMDD_HHMMSS/
  ./backups/logs_YYYYMMDD_HHMMSS/

Examples:
  # Backup everything
  ./scripts/backup_data.sh

  # Backup only data
  ./scripts/backup_data.sh --data-only

  # Backup without confirmation
  FORCE=1 ./scripts/backup_data.sh

EOF
}

# Backup data directory
backup_data_dir() {
    if [[ ! -d "$DATA_DIR" ]]; then
        log_warn "Data directory does not exist: $DATA_DIR"
        log_info "Nothing to backup"
        return 0
    fi

    # Check if data directory is empty
    if [[ -z "$(ls -A "$DATA_DIR" 2>/dev/null)" ]]; then
        log_warn "Data directory is empty: $DATA_DIR"
        log_info "Nothing to backup"
        return 0
    fi

    log_info "Backing up data directory..."

    # Create backup directory
    local backup_dir
    backup_dir=$(create_backup_dir "data")
    DATA_BACKUP_DIR="$backup_dir"

    # Copy data directory
    if cp -R "$DATA_DIR"/* "$backup_dir/" 2>/dev/null; then
        log_success "Data backed up to: $backup_dir"

        # Show backup size
        local size
        size=$(du -sh "$backup_dir" 2>/dev/null | awk '{print $1}')
        log_info "Backup size: $size"

        # List backed up items
        log_info "Backed up items:"
        find "$backup_dir" -type f | sed "s|^$backup_dir/|  - |" | head -10
        local count
        count=$(find "$backup_dir" -type f | wc -l | tr -d ' ')
        if [[ $count -gt 10 ]]; then
            log_info "  ... and $((count - 10)) more files"
        fi
    else
        die "Failed to backup data directory" "$EXIT_RUNTIME_ERROR"
    fi

    echo "$backup_dir"
}

# Backup logs directory
backup_logs_dir() {
    if [[ ! -d "$LOGS_ROOT" ]]; then
        log_warn "Logs directory does not exist: $LOGS_ROOT"
        log_info "Nothing to backup"
        return 0
    fi

    # Check if logs directory is empty
    if [[ -z "$(ls -A "$LOGS_ROOT" 2>/dev/null)" ]]; then
        log_warn "Logs directory is empty: $LOGS_ROOT"
        log_info "Nothing to backup"
        return 0
    fi

    log_info "Backing up logs directory..."

    # Create backup directory
    local backup_dir
    backup_dir=$(create_backup_dir "logs")
    LOGS_BACKUP_DIR="$backup_dir"

    # Copy logs directory
    if cp -R "$LOGS_ROOT"/* "$backup_dir/" 2>/dev/null; then
        log_success "Logs backed up to: $backup_dir"

        # Show backup size
        local size
        size=$(du -sh "$backup_dir" 2>/dev/null | awk '{print $1}')
        log_info "Backup size: $size"

        # List backed up items
        log_info "Backed up items:"
        find "$backup_dir" -type f | sed "s|^$backup_dir/|  - |" | head -10
        local count
        count=$(find "$backup_dir" -type f | wc -l | tr -d ' ')
        if [[ $count -gt 10 ]]; then
            log_info "  ... and $((count - 10)) more files"
        fi
    else
        die "Failed to backup logs directory" "$EXIT_RUNTIME_ERROR"
    fi

    echo "$backup_dir"
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --data-only)
                BACKUP_LOGS=0
                shift
                ;;
            --logs-only)
                BACKUP_DATA=0
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
            *)
                log_error "Unknown option: $1"
                log_plain ""
                log_plain "Use --help for usage information"
                exit "$EXIT_CONFIG_ERROR"
                ;;
        esac
    done

    log_header "League Data Backup"

    # Show what will be backed up
    if [[ $BACKUP_DATA -eq 1 ]] && [[ $BACKUP_LOGS -eq 1 ]]; then
        log_info "Will backup: SHARED/data/ and SHARED/logs/"
    elif [[ $BACKUP_DATA -eq 1 ]]; then
        log_info "Will backup: SHARED/data/ only"
    elif [[ $BACKUP_LOGS -eq 1 ]]; then
        log_info "Will backup: SHARED/logs/ only"
    else
        log_error "Nothing to backup (both --data-only and --logs-only specified)"
        exit "$EXIT_CONFIG_ERROR"
    fi

    # Confirm action
    if ! confirm "Proceed with backup?"; then
        log_info "Backup cancelled"
        exit 0
    fi

    # Create backups directory
    mkdir -p "${PROJECT_ROOT}/backups"

    # Backup data directory
    if [[ $BACKUP_DATA -eq 1 ]]; then
        backup_data_dir
    fi

    # Backup logs directory
    if [[ $BACKUP_LOGS -eq 1 ]]; then
        backup_logs_dir
    fi

    log_header "Backup Complete"

    if [[ $OUTPUT_JSON -eq 1 ]]; then
        jq -n \
            --arg data_backup "${DATA_BACKUP_DIR}" \
            --arg logs_backup "${LOGS_BACKUP_DIR}" \
            --arg status "success" \
            '{status:$status,data_backup_dir:$data_backup,logs_backup_dir:$logs_backup}'
        exit 0
    fi

    log_success "All backups created successfully"

    # Show backup location
    log_info "Backups stored in: ${PROJECT_ROOT}/backups/"

    # List all backups
    log_info "Available backups:"
    ls -1t "${PROJECT_ROOT}/backups" 2>/dev/null | head -5 | sed 's/^/  - /'
}

# Run main function
main "$@"
