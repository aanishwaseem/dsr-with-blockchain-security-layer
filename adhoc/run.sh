#!/bin/bash

set -euo pipefail

APP_NAME="DATAEXSYS_MESH"
BASE_DIR="$(pwd)"

echo "[BOOT] $APP_NAME Starting..."

# ---------------- CLEANUP ----------------
echo "[CLEAN] Stopping previous instances..."

pkill -f "run.py" || true
pkill -f "chat.py" || true
pkill -f "discovery.py" || true
pkill -f "transport.py" || true

sleep 1

# ---------------- SAFETY CHECKS ----------------
echo "[CHECK] Verifying Python environment..."

command -v python3 >/dev/null 2>&1 || {
  echo "[ERROR] python3 not found"
  exit 1
}

# ---------------- NETWORK SETUP ----------------
echo "[STEP 1] Running Adhoc Setup..."
sudo python3 adhoc_setup.py

# ---------------- TUN SETUP ----------------
echo "[STEP 2] Initializing TUN interface..."
sudo python3 tun_setup.py

sleep 1

# ---------------- START CORE STACK ----------------
echo "[STEP 3] Launching Mesh Runtime..."

# run full system as one orchestrator (IMPORTANT for stability)
sudo python3 run.py &
RUN_PID=$!

# ---------------- LOGGING ----------------
LOG_DIR="$BASE_DIR/logs"
mkdir -p "$LOG_DIR"

echo "[LOG] Logs directory: $LOG_DIR"

# ---------------- SIGNAL HANDLER ----------------
cleanup() {
    echo ""
    echo "[SHUTDOWN] Stopping $APP_NAME..."

    kill $RUN_PID 2>/dev/null || true

    # extra safety cleanup
    pkill -f "run.py" || true

    echo "[SHUTDOWN] Complete."
    exit 0
}

trap cleanup INT TERM

# ---------------- STATUS ----------------
echo ""
echo "=============================="
echo "  $APP_NAME RUNNING"
echo "  PID: $RUN_PID"
echo "  MODE: PROD MESH STACK"
echo "=============================="
echo ""
echo "[INFO] Press CTRL+C to stop"

# keep alive
wait $RUN_PID