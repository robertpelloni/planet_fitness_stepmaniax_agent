#!/usr/bin/env python3
"""
StepManiaX B2B Management System - System Tray & Server Process Manager (v9.3.0)

Provides a unified controller to inspect, start, stop, restart, and monitor background
daemons and web servers (Gunicorn/Flask on port 5000, smx-monitor / health_monitor.py, backup_job).
Operates both as a GUI system tray utility when DISPLAY is available and as a robust CLI daemon tool.
"""

import os
import sys
import time
import signal
import subprocess
import argparse
import webbrowser
import logging

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(PROJECT_ROOT, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger("SystemTrayManager")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s'))
logger.addHandler(handler)


def find_pids_on_port(port=5000):
    """Finds all PIDs listening or connected on a given TCP port."""
    try:
        out = subprocess.check_output(["lsof", "-t", f"-i:{port}"], stderr=subprocess.DEVNULL)
        return [int(pid.strip()) for pid in out.decode().strip().split() if pid.strip()]
    except Exception:
        return []


def get_process_status():
    """Returns a dictionary summary of active servers and background monitors."""
    port_5000_pids = find_pids_on_port(5000)

    # Check for health_monitor process
    monitor_pids = []
    try:
        out = subprocess.check_output(["pgrep", "-f", "health_monitor.py"], stderr=subprocess.DEVNULL)
        monitor_pids = [int(pid.strip()) for pid in out.decode().strip().split() if pid.strip()]
    except Exception:
        pass

    return {
        "web_server": {
            "running": len(port_5000_pids) > 0,
            "port": 5000,
            "pids": port_5000_pids
        },
        "health_monitor": {
            "running": len(monitor_pids) > 0,
            "pids": monitor_pids
        }
    }


def start_web_server():
    """Starts the Flask / Gunicorn application server in the background."""
    status = get_process_status()
    if status["web_server"]["running"]:
        logger.info(f"Web server is already running on port 5000 (PIDs: {status['web_server']['pids']}).")
        return True

    log_path = os.path.join(LOG_DIR, "server.log")
    logger.info("Starting Gunicorn web server on http://127.0.0.1:5000...")
    with open(log_path, "a") as out:
        subprocess.Popen(
            ["gunicorn", "--config", "gunicorn_config.py", "app:app"],
            cwd=PROJECT_ROOT,
            stdout=out,
            stderr=subprocess.STDOUT
        )
    time.sleep(1.5)
    new_status = get_process_status()
    if new_status["web_server"]["running"]:
        logger.info(f"Server started successfully (PIDs: {new_status['web_server']['pids']}).")
        return True
    else:
        logger.error("Failed to start web server. Inspect logs/server.log.")
        return False


def stop_web_server():
    """Gracefully terminates all processes running on port 5000."""
    pids = find_pids_on_port(5000)
    if not pids:
        logger.info("No active web server processes found on port 5000.")
        return True

    logger.info(f"Stopping web server processes: {pids}...")
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        except Exception as e:
            logger.warning(f"Error terminating PID {pid}: {e}")

    time.sleep(1.0)
    # Force kill if still lingering
    remaining = find_pids_on_port(5000)
    for pid in remaining:
        try:
            os.kill(pid, signal.SIGKILL)
        except Exception:
            pass
    logger.info("Web server stopped.")
    return True


def start_health_monitor():
    """Starts the health_monitor background daemon."""
    status = get_process_status()
    if status["health_monitor"]["running"]:
        logger.info(f"Health monitor daemon is already running (PIDs: {status['health_monitor']['pids']}).")
        return True

    log_path = os.path.join(LOG_DIR, "health_monitor.log")
    logger.info("Starting health monitor daemon...")
    with open(log_path, "a") as out:
        subprocess.Popen(
            [sys.executable, "health_monitor.py"],
            cwd=PROJECT_ROOT,
            stdout=out,
            stderr=subprocess.STDOUT
        )
    time.sleep(1.0)
    return True


def stop_health_monitor():
    """Terminates active health monitor processes."""
    status = get_process_status()
    pids = status["health_monitor"]["pids"]
    if not pids:
        logger.info("No active health monitor processes found.")
        return True

    logger.info(f"Stopping health monitor processes: {pids}...")
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except Exception:
            pass
    return True


def stop_all_services():
    """Stops both web server and health monitor processes."""
    logger.info("Quitting and stopping all StepManiaX B2B servers and monitors...")
    stop_web_server()
    stop_health_monitor()
    logger.info("All services shut down.")


def open_dashboard():
    """Opens the Global Operations Center in the default browser."""
    url = "http://127.0.0.1:5000/admin/unified-dashboard"
    logger.info(f"Opening dashboard in browser: {url}")
    webbrowser.open(url)


def tail_logs(log_name="server.log", lines=20):
    """Displays the most recent log lines from the specified file."""
    path = os.path.join(LOG_DIR, log_name)
    if not os.path.exists(path):
        print(f"Log file not found: {path}")
        return
    with open(path, "r") as f:
        content = f.readlines()
        print(f"\n--- Tail of {log_name} (last {lines} lines) ---")
        for line in content[-lines:]:
            print(line, end="")
        print("----------------------------------------------\n")


def print_status_report():
    """Prints a formatted console report of system health and process statuses."""
    status = get_process_status()
    print("\n=======================================================")
    print("   StepManiaX B2B System Tray & Process Manager")
    print("=======================================================")
    ws_run = status["web_server"]["running"]
    ws_color = "\033[92mONLINE\033[0m" if ws_run else "\033[91mOFFLINE\033[0m"
    print(f" Web Server (Port 5000):   {ws_color} (PIDs: {status['web_server']['pids']})")

    hm_run = status["health_monitor"]["running"]
    hm_color = "\033[92mONLINE\033[0m" if hm_run else "\033[91mOFFLINE\033[0m"
    print(f" Health Monitor Daemon:    {hm_color} (PIDs: {status['health_monitor']['pids']})")
    print(" Dashboard URL:            http://127.0.0.1:5000/admin/unified-dashboard")
    print(" Logs Directory:           " + LOG_DIR)
    print("=======================================================\n")


def run_gui_tray():
    """Initializes GUI system tray if supported by environment (e.g. pystray)."""
    try:
        import pystray
        from PIL import Image, ImageDraw

        def create_image():
            # Generate a 64x64 icon with SMX branding
            image = Image.new('RGB', (64, 64), color=(30, 41, 59))
            d = ImageDraw.Draw(image)
            d.rectangle((8, 8, 56, 56), fill=(250, 204, 21))
            return image

        menu = pystray.Menu(
            pystray.MenuItem("Open Global Operations Center", lambda: open_dashboard()),
            pystray.MenuItem("Start All Servers", lambda: (start_web_server(), start_health_monitor())),
            pystray.MenuItem("Stop All Servers", lambda: stop_all_services()),
            pystray.MenuItem("Restart Servers", lambda: (stop_all_services(), time.sleep(1), start_web_server())),
            pystray.MenuItem("Quit", lambda icon, item: (stop_all_services(), icon.stop()))
        )

        icon = pystray.Icon("SMX_B2B", create_image(), "StepManiaX B2B Manager", menu)
        logger.info("Starting System Tray Icon...")
        icon.run()
    except Exception as e:
        logger.warning(f"GUI System Tray not available on this platform ({e}). Using CLI manager mode.")
        print_status_report()


def main():
    parser = argparse.ArgumentParser(description="StepManiaX B2B System Tray & Process Manager")
    parser.add_argument("--status", action="store_true", help="Display service status")
    parser.add_argument("--start", action="store_true", help="Start web server and health monitor")
    parser.add_argument("--stop", action="store_true", help="Stop web server and health monitor")
    parser.add_argument("--restart", action="store_true", help="Restart web server")
    parser.add_argument("--open", action="store_true", help="Open Operations Center in browser")
    parser.add_argument("--logs", type=str, default=None, help="Tail specified log file (e.g., server.log)")
    parser.add_argument("--tray", action="store_true", help="Launch graphical system tray icon")

    args = parser.parse_args()

    if args.status:
        print_status_report()
    elif args.start:
        start_web_server()
        start_health_monitor()
        print_status_report()
    elif args.stop:
        stop_all_services()
        print_status_report()
    elif args.restart:
        stop_all_services()
        time.sleep(1)
        start_web_server()
        start_health_monitor()
        print_status_report()
    elif args.open:
        open_dashboard()
    elif args.logs:
        tail_logs(args.logs)
    elif args.tray:
        run_gui_tray()
    else:
        # Default action: Display status report
        print_status_report()


if __name__ == "__main__":
    main()
