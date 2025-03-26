# pve-config-backup

Automated backups of Proxmox VE VM & CT configuration files using NFS storage.

All following commands are expected to be run with administrative privilages.

## Installation
Copy & Paste in the Proxmox VE shell:
```bash
wget https://raw.githubusercontent.com/open-e/pve-config-backup/main/pve-config-backup \
    -O /usr/local/sbin/pve-config-backup; \
    chmod +x /usr/local/sbin/pve-config-backup; \
    pve-config-backup install; \
    pve-config-backup help
```
Run it to get the latest backup details and logs.
```bash
pve-config-backup
```
Get help:
```bash
pve-config-backup help
```
