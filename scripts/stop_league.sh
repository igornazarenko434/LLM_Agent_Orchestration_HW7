#!/bin/bash
#
# Stop all league agents gracefully
# Usage: ./scripts/stop_league.sh
#

echo "🛑 Stopping all league agents..."
echo "=========================================="

# Try to read PIDs from file
if [ -f /tmp/league_pids.txt ]; then
    PIDS=$(cat /tmp/league_pids.txt)
    echo "Found PIDs from startup: $PIDS"

    for PID in $PIDS; do
        if ps -p $PID > /dev/null 2>&1; then
            echo "Stopping process $PID..."
            kill -TERM $PID 2>/dev/null || true
        fi
    done

    # Wait for graceful shutdown
    sleep 2

    # Force kill if still running
    for PID in $PIDS; do
        if ps -p $PID > /dev/null 2>&1; then
            echo "Force killing process $PID..."
            kill -9 $PID 2>/dev/null || true
        fi
    done

    rm /tmp/league_pids.txt
else
    echo "No PID file found, searching for processes..."

    # Kill by process name
    pkill -TERM -f "agents.league_manager.main" || true
    pkill -TERM -f "agents.referee_.*\.main" || true
    pkill -TERM -f "agents.player_.*\.main" || true

    sleep 2

    # Force kill if needed
    pkill -9 -f "agents.league_manager.main" || true
    pkill -9 -f "agents.referee_.*\.main" || true
    pkill -9 -f "agents.player_.*\.main" || true
fi

echo ""
echo "✅ All agents stopped"
echo "=========================================="
