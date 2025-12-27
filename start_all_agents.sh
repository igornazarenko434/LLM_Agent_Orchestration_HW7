#!/bin/bash

export PYTHONPATH=SHARED:$PYTHONPATH
export PYTHONDONTWRITEBYTECODE=1
export BASE_HOST=127.0.0.1

echo "Starting Referees..."
.venv/bin/python3 -u -m agents.referee_REF01.main > logs/ref01.log 2>&1 &
.venv/bin/python3 -u -m agents.referee_REF02.main > logs/ref02.log 2>&1 &
sleep 6

echo "Starting Players..."
.venv/bin/python3 -u -m agents.player_P01.main > logs/p01.log 2>&1 &
.venv/bin/python3 -u -m agents.player_P02.main > logs/p02.log 2>&1 &
.venv/bin/python3 -u -m agents.player_P03.main > logs/p03.log 2>&1 &
.venv/bin/python3 -u -m agents.player_P04.main > logs/p04.log 2>&1 &
sleep 10

echo "All agents started. Checking registration status..."
grep -h "Successfully registered\|Registration failed" logs/ref*.log logs/p0*.log 2>/dev/null
