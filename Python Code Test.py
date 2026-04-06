import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import time
import psutil

#!/usr/bin/env python3

STATE_FILE = "security_monitor_state.json"
ALERT_LOG = "security_monitor_alerts.log"

DEFAULT_MONITORED_PATHS = [
    "/etc",
    "/var/www",
    os.path.expanduser("~"),
]

PROCESS_WHITELIST = {
    "systemd",
    "sshd",
    "bash",
    "zsh",
    "python",
    "python3",
    "init",
    "cron",
    "tmux",
    "sh",
    "cmd.exe",
    "powershell.exe",
    "explorer.exe",
}

PROCESS_BLACKLIST = {
    "mimikatz",
    "cryptominer",
    "powershell.exe -nop",
    "python.exe -c",
    "cmd.exe /c",
}

NETWORK_BLACKLIST_PORTS = {22, 3389, 445, 1433}

LOG_KEYWORDS = [
    "failed password",
    "authentication failure",
    "sudo:",
    "invalid user",
    "unauthorized",
    "error",
]

def log_alert(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    entry = f"{timestamp} - {message}"
    print(entry)
    with open(ALERT_LOG, "a", encoding="utf-8") as log_file:
        log_file.write(entry + "\n")

def load_state(filename):
    if not os.path.exists(filename):
        return {"files": {}, "logs": {}}
    try:
        with open(filename, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return {"files": {}, "logs": {}}

def save_state(state, filename):
    with open(filename, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2)

def hash_file(path):
    sha256 = hashlib.sha256()
    try:
        with open(path, "rb") as handle:
            while True:
                chunk = handle.read(65536)
                if not chunk:
                    break
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception:
        return None

def find_files(root_paths):
    for root in root_paths:
        if not os.path.exists(root):
            continue
        for dirpath, _, filenames in os.walk(root):
            for filename in filenames:
                path = os.path.join(dirpath, filename)
                yield path

def monitor_files(monitored_paths, state):
    saved = state.get("files", {})
    current = {}
    for path in find_files(monitored_paths):
        file_hash = hash_file(path)
        if file_hash is None:
            continue
        current[path] = file_hash
        if path not in saved:
            log_alert(f"New file detected: {path}")
        elif saved[path] != file_hash:
            log_alert(f"File changed: {path}")
    for path in saved:
        if path not in current:
            log_alert(f"File deleted: {path}")
    state["files"] = current

def get_running_processes():
    try:
        return [p.name().lower() for p in psutil.process_iter(attrs=["name"])]
    except ImportError:
        if os.name == "nt":
            command = ["tasklist", "/fo", "csv", "/nh"]
            proc = subprocess.run(command, capture_output=True, text=True)
            lines = proc.stdout.splitlines()
            processes = []
            for line in lines:
                parts = re.findall(r'"([^"]+)"', line)
                if parts:
                    processes.append(parts[0].lower())
            return processes
        else:
            proc = subprocess.run(["ps", "-eo", "comm"], capture_output=True, text=True)
            return [line.strip().lower() for line in proc.stdout.splitlines()[1:] if line.strip()]

def monitor_processes(state):
    running = get_running_processes()
    seen = state.get("processes", [])
    for name in running:
        if name not in PROCESS_WHITELIST:
            if name not in seen:
                log_alert(f"Unwhitelisted process running: {name}")
        for pattern in PROCESS_BLACKLIST:
            if pattern in name:
                log_alert(f"Blacklisted process detected: {name}")
    state["processes"] = running

def parse_network_output(output):
    lines = output.splitlines()
    connections = []
    for line in lines:
        parts = re.split(r"\s+", line.strip())
        if len(parts) < 4:
            continue
        connections.append(parts)
    return connections

def monitor_network(state):
    os_type = platform.system().lower()
    connections = []
    if os_type == "windows":
        proc = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
        connections = parse_network_output(proc.stdout)
    else:
        for cmd in (["ss", "-ant"], ["netstat", "-ant"]):
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode == 0:
                connections = parse_network_output(proc.stdout)
                break
    suspicious = []
    for row in connections:
        if len(row) < 4:
            continue
        local = row[3]
        match = re.search(r":(\d+)$", local)
        if not match:
            continue
        port = int(match.group(1))
        if port in NETWORK_BLACKLIST_PORTS:
            suspicious.append(local)
    if suspicious:
        log_alert(f"Suspicious network ports in use: {', '.join(sorted(set(suspicious)))}")
    state["network"] = suspicious

def monitor_logs(log_path, keywords, state):
    if not os.path.exists(log_path):
        return
    saved = state.get("logs", {}).get(log_path, 0)
    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as handle:
            handle.seek(saved)
            for line in handle:
                lower = line.lower()
                if any(keyword in lower for keyword in keywords):
                    log_alert(f"Suspicious log entry in {log_path}: {line.strip()}")
            position = handle.tell()
    except Exception:
        position = saved
    if "logs" not in state:
        state["logs"] = {}
    state["logs"][log_path] = position

def main():
    parser = argparse.ArgumentParser(description="Simple security monitoring automation.")
    parser.add_argument("--paths", nargs="+", default=DEFAULT_MONITORED_PATHS, help="Paths to monitor for file changes.")
    parser.add_argument("--log", default="/var/log/auth.log" if platform.system().lower() != "windows" else None, help="Log file to scan for suspicious entries.")
    parser.add_argument("--interval", type=int, default=0, help="Repeat monitoring every N seconds. Use 0 for one-time scan.")
    args = parser.parse_args()

    state = load_state(STATE_FILE)
    while True:
        monitor_files(args.paths, state)
        monitor_processes(state)
        monitor_network(state)
        if args.log:
            monitor_logs(args.log, LOG_KEYWORDS, state)
        save_state(state, STATE_FILE)
        if args.interval <= 0:
            break
        time.sleep(args.interval)

if __name__ == "__main__":
    main()