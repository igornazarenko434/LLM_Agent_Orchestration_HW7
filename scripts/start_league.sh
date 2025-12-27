#!/bin/bash
#
# Start all agents for a 4-player league
# Usage: ./scripts/start_league.sh
#

set -e

LEAGUE_ID="${1:-league_2025_even_odd}"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$PROJECT_ROOT"

echo "🚀 Starting Even/Odd League: $LEAGUE_ID"
echo "=========================================="

# Activate virtual environment
source .venv/bin/activate

# Export PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT/SHARED:$PYTHONPATH"

# Start League Manager
echo "📋 Starting League Manager on port 8000..."
python3 -m agents.league_manager.main --league-id "$LEAGUE_ID" --port 8000 > logs/league_manager.log 2>&1 &
LM_PID=$!
echo "   PID: $LM_PID"
sleep 2

# Start Referees
echo "⚖️  Starting Referee REF01 on port 8001..."
python3 -m agents.referee_REF01.main --referee-id REF01 --port 8001 > logs/referee_REF01.log 2>&1 &
REF01_PID=$!
echo "   PID: $REF01_PID"

echo "⚖️  Starting Referee REF02 on port 8002..."
python3 -m agents.referee_REF02.main --referee-id REF02 --port 8002 > logs/referee_REF02.log 2>&1 &
REF02_PID=$!
echo "   PID: $REF02_PID"
sleep 2

# Start Players
echo "🎮 Starting Player P01 on port 8101..."
python3 -m agents.player_P01.main > logs/player_P01.log 2>&1 &
P01_PID=$!
echo "   PID: $P01_PID"

echo "🎮 Starting Player P02 on port 8102..."
python3 -m agents.player_P02.main > logs/player_P02.log 2>&1 &
P02_PID=$!
echo "   PID: $P02_PID"

echo "🎮 Starting Player P03 on port 8103..."
python3 -m agents.player_P03.main > logs/player_P03.log 2>&1 &
P03_PID=$!
echo "   PID: $P03_PID"

echo "🎮 Starting Player P04 on port 8104..."
python3 -m agents.player_P04.main > logs/player_P04.log 2>&1 &
P04_PID=$!
echo "   PID: $P04_PID"

sleep 3

echo ""
echo "✅ All agents started!"
echo "=========================================="
echo "League Manager: http://localhost:8000  (PID: $LM_PID)"
echo "Referee REF01:  http://localhost:8001  (PID: $REF01_PID)"
echo "Referee REF02:  http://localhost:8002  (PID: $REF02_PID)"
echo "Player P01:     http://localhost:8101  (PID: $P01_PID)"
echo "Player P02:     http://localhost:8102  (PID: $P02_PID)"
echo "Player P03:     http://localhost:8103  (PID: $P03_PID)"
echo "Player P04:     http://localhost:8104  (PID: $P04_PID)"
echo ""
echo "To stop all agents: ./scripts/stop_league.sh"
echo "To check health: ./scripts/check_health.sh"
echo ""

# Save PIDs for later cleanup
echo "$LM_PID $REF01_PID $REF02_PID $P01_PID $P02_PID $P03_PID $P04_PID" > /tmp/league_pids.txt
