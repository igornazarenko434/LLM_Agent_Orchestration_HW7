#!/bin/bash
#
# Check health of all league agents
# Usage: ./scripts/check_health.sh
#

echo "🏥 Checking health of all agents..."
echo "=========================================="

check_endpoint() {
    local name=$1
    local url=$2

    if curl -s -f "$url" > /dev/null 2>&1; then
        echo "✅ $name is healthy"
        return 0
    else
        echo "❌ $name is NOT responding"
        return 1
    fi
}

# Check each agent
check_endpoint "League Manager" "http://localhost:8000/health"
check_endpoint "Referee REF01" "http://localhost:8001/health"
check_endpoint "Referee REF02" "http://localhost:8002/health"
check_endpoint "Player P01" "http://localhost:8101/health"
check_endpoint "Player P02" "http://localhost:8102/health"
check_endpoint "Player P03" "http://localhost:8103/health"
check_endpoint "Player P04" "http://localhost:8104/health"

echo ""
echo "=========================================="
echo "Health check complete"
