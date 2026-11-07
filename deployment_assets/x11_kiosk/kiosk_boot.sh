#!/bin/bash
# ==============================================================================
# StepMania Fitness Fork: Bare-Metal Openbox X11 Kiosk Bootloader (v9.7.0)
#
# Launches the stripped StepMania Fitness Fork directly in an Openbox window manager
# session on Linux ARM64 hardware without desktop environment overhead.
# Prevents screen blanking, disables screensavers, hides cursor, and restarts on crash.
# ==============================================================================

set -e

echo "--- Initializing StepMania Fitness Kiosk Display Layer ---"

# 1. Disable screen blanking, DPMS energy saving, and screensaver
if command -v xset >/dev/null 2>&1; then
    xset -dpms
    xset s off
    xset s noblank
    echo "[x11_kiosk] DPMS and screen blanking disabled."
fi

# 2. Hide cursor after 1 second of inactivity if unclutter is installed
if command -v unclutter >/dev/null 2>&1; then
    unclutter -idle 1 -root &
    echo "[x11_kiosk] Cursor auto-hide enabled via unclutter."
fi

# 3. Locate StepMania Fitness binary
SM_BIN="${STEPMANIA_BIN:-/opt/stepmania/stepmania}"

if [ ! -x "$SM_BIN" ]; then
    # Fallback to local executable in build or path
    if command -v stepmania >/dev/null 2>&1; then
        SM_BIN=$(command -v stepmania)
    else
        echo "[x11_kiosk] Notice: StepMania binary not found at $SM_BIN; running mock kiosk loop for testing."
        SM_BIN="mock"
    fi
fi

# 4. Infinite restart watchdog loop for 24/7 commercial gym floor operation
echo "[x11_kiosk] Launching StepMania Fitness Fork session loop..."

while true; do
    if [ "$SM_BIN" = "mock" ]; then
        echo "[x11_kiosk] Mock kiosk process running... (PID: $$)"
        sleep 5
        break
    else
        echo "[x11_kiosk] Starting binary: $SM_BIN"
        "$SM_BIN" --kiosk --fullscreen || true
        echo "[x11_kiosk] StepMania process terminated. Restarting in 3 seconds..."
        sleep 3
    fi
done
