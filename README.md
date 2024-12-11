# pve-config-backup

Backup automation for Proxmox


## Before Install

Package `python3-psutil` have to be installed for plugin to work.
```bash
sudo apt install python3-psutil
```

## Installation

1. Place script at `/usr/local/bin/pve-config-backup.py`
2. To install the script properly, please run:
```bash
sudo cp /root/pve-config-backup.py /usr/local/bin/pve-config-backup.py
```
3. Make script executable:

```bash
sudo chmod +x /usr/local/bin/pve-config-backup.py
```
4. Install system service

```bash
sudo /usr/local/bin/pve-config-backup.py --install
```

## Service Operation

By default service will backup its data to folder `/mnt/pve-config-backup`.
User is expected to mount appropriate NFS share to this folder.

Once preparation is done user can start backup service by running
```bash
/usr/local/bin/pve-config-backup.py --start
```
