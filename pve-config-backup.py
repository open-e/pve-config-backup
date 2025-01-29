#!/usr/bin/env python3
import os
import shutil
import socket
import time
from datetime import datetime
import logging
from pathlib import Path
import subprocess
import glob
from logging.handlers import RotatingFileHandler
import argparse
import sys
import signal
import psutil

# Script constants
SCRIPT_PATH = "/usr/local/bin/pve-config-backup.py"
SYSTEMD_PATH = "/etc/systemd/system/pve-config-backup.service"
SERVICE_NAME = "pve-config-backup"

# Configuration
CONFIG = {
    "nfs_base_backup_path": "/mnt/pve/pve-config-backup",
    # Only back up /etc/pve/nodes
    "config_paths": [
        "/etc/pve/nodes",
    ],
    "max_backups": 100,
    "backup_interval": 300,  # 5 minutes in seconds
    "log_file": "/var/log/pve-config-backup.log",
    "log_max_size": 10485760,  # 10MB
    "log_backup_count": 5,
}

SYSTEMD_SERVICE_CONTENT = '''[Unit]
Description=Proxmox VE Configuration Backup Service
After=network-online.target nfs-client.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/local/bin/pve-config-backup.py --daemon
Restart=always
RestartSec=60
User=root
Group=root

# Security hardening
ProtectSystem=full
ProtectHome=read-only
PrivateTmp=true
NoNewPrivileges=true
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true

[Install]
WantedBy=multi-user.target
'''


def setup_logging():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handlers = [
        RotatingFileHandler(
            CONFIG["log_file"],
            maxBytes=CONFIG["log_max_size"],
            backupCount=CONFIG["log_backup_count"]
        )
    ]
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    for handler in handlers:
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


logger = setup_logging()


def check_script_location():
    """Check if script is running from the correct location."""
    current_path = os.path.abspath(__file__)
    if current_path != SCRIPT_PATH:
        print("\nError: Script is not in the correct location!")
        print(f"Current location: {current_path}")
        print(f"Required location: {SCRIPT_PATH}")
        print("\nTo install the script properly, please run:")
        print(f"sudo cp {current_path} {SCRIPT_PATH}")
        print(f"sudo chmod +x {SCRIPT_PATH}")
        print("\nAfter moving the script, you can run it with:")
        print(f"sudo {SCRIPT_PATH} --install\n")
        sys.exit(1)


def install_service():
    """Install, enable, and start the systemd service."""
    try:
        with open(SYSTEMD_PATH, 'w') as f:
            f.write(SYSTEMD_SERVICE_CONTENT)
        subprocess.run(['systemctl', 'daemon-reload'], check=True)
        subprocess.run(['systemctl', 'enable', SERVICE_NAME], check=True)
        subprocess.run(['systemctl', 'start', SERVICE_NAME], check=True)
        print("Service installed, enabled, and started successfully")
        return True
    except Exception as e:
        print(f"Failed to install service: {e}")
        return False


def uninstall_service():
    """Remove systemd service."""
    try:
        subprocess.run(['systemctl', 'stop', SERVICE_NAME], check=False)
        subprocess.run(['systemctl', 'disable', SERVICE_NAME], check=False)
        if os.path.exists(SYSTEMD_PATH):
            os.remove(SYSTEMD_PATH)
        subprocess.run(['systemctl', 'daemon-reload'], check=True)
        print("Service uninstalled successfully")
        return True
    except Exception as e:
        print(f"Failed to uninstall service: {e}")
        return False


def get_service_status():
    """Get current service status."""
    try:
        result = subprocess.run(['systemctl', 'status', SERVICE_NAME],
                                capture_output=True, text=True)
        print(result.stdout)
    except Exception as e:
        print(f"Failed to get service status: {e}")


def get_hostname():
    return socket.gethostname()


def create_backup_dir():
    hostname = get_hostname()
    backup_dir = os.path.join(CONFIG["nfs_base_backup_path"], hostname)
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir


def check_nfs_mount():
    if not os.path.ismount(CONFIG["nfs_base_backup_path"]):
        return False
    return True


def perform_rsync(source, dest):
    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    backup_path = os.path.join(dest, f"config_backup_{timestamp}")
    os.makedirs(backup_path)

    # Quiet mode for rsync
    cmd_base = ["rsync", "-rtDq", "--relative"]
    try:
        for config_path in source:
            if os.path.exists(config_path):
                cmd = cmd_base + [config_path, backup_path]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return backup_path, True
    except subprocess.CalledProcessError:
        return backup_path, False


def rotate_backups(backup_dir):
    backups = sorted(
        glob.glob(os.path.join(backup_dir, "config_backup_*")),
        reverse=True
    )
    if len(backups) > CONFIG["max_backups"]:
        for old_backup in backups[CONFIG["max_backups"]:]:
            try:
                shutil.rmtree(old_backup)
            except Exception:
                pass


def stop_service():
    """Stop the running service."""
    try:
        subprocess.run(['systemctl', 'stop', SERVICE_NAME], check=True)
        print("Service stopped via systemctl")
        return True
    except subprocess.CalledProcessError:
        # If systemctl fails, try to find and kill the process
        try:
            script_name = os.path.basename(SCRIPT_PATH)
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info.get('cmdline', [])
                    if cmdline and script_name in cmdline[0] and '--daemon' in cmdline:
                        os.kill(proc.info['pid'], signal.SIGTERM)
                        print(f"Process with PID {proc.info['pid']} has been stopped")
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            print("No running backup process found")
            return False
        except Exception as e:
            print(f"Failed to stop process: {e}")
            return False


def show_info():
    """Show the most recent backups."""
    hostname = get_hostname()
    backup_host_dir = os.path.join(CONFIG["nfs_base_backup_path"], hostname)

    if not os.path.isdir(backup_host_dir):
        print("No backups found.")
        return

    backups = sorted(
        glob.glob(os.path.join(backup_host_dir, "config_backup_*")),
        reverse=True
    )

    print("The most recent config backup(s):")
    print(f"    {backup_host_dir}")

    if backups:
        for backup in backups[:5]:
            print(f"        {os.path.basename(backup)}")
    else:
        print("        No backups found.")


def run_daemon():
    while True:
        if check_nfs_mount():
            backup_dir = create_backup_dir()
            backup_path, success = perform_rsync(CONFIG["config_paths"], backup_dir)
            rotate_backups(backup_dir)

            if success:
                logger.info("Backup completed successfully")
            else:
                logger.info("Backup failed")
        else:
            logger.info("NFS not mounted, skipping backup cycle")

        time.sleep(CONFIG["backup_interval"])


def main():
    parser = argparse.ArgumentParser(
        description='Proxmox VE Configuration Backup Service'
    )
    parser.add_argument('--install', action='store_true',
                        help='Install, enable, and start the systemd service')
    parser.add_argument('--uninstall', action='store_true',
                        help='Remove systemd service')
    parser.add_argument('--status', action='store_true',
                        help='Show service status')
    parser.add_argument('--start', action='store_true',
                        help='Start the systemd service')
    parser.add_argument('--stop', action='store_true',
                        help='Stop the systemd service')
    parser.add_argument('--daemon', action='store_true',
                        help='Run the backup daemon (used by systemd)')
    parser.add_argument('--info', action='store_true',
                        help='Show recent backup folders')

    args = parser.parse_args()

    # Check script location first
    check_script_location()

    if args.install:
        install_service()
    elif args.uninstall:
        uninstall_service()
    elif args.status:
        get_service_status()
    elif args.stop:
        stop_service()
    elif args.start:
        try:
            subprocess.run(['systemctl', 'start', SERVICE_NAME], check=True)
            print("Service started successfully")
        except subprocess.CalledProcessError as e:
            print(f"Failed to start service: {e}")
    elif args.daemon:
        run_daemon()
    elif args.info:
        show_info()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
