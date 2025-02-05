# pve-config-backup

Automated backups of Proxmox VE VM & CT configuration files using NFS and LVM storage.

All following commands are expected to be run with administrative privilages.

## Installation
Copy & Paste in the Proxmox VE shell:
```bash
wget https://raw.githubusercontent.com/open-e/pve-config-backup/main/pve-config-backup \
    -O /usr/local/sbin/pve-config-backup; \
    chmod +x /usr/local/sbin/pve-config-backup \
    pve-config-backup --install \
    pve-config-backup --info
```

Or run step-by-setp manully:
1. Place script at:
```
/usr/local/sbin/pve-config-backup
```
2. Make script executable:
```bash
chmod +x /usr/local/sbin/pve-config-backup
```
3. Run it to get the help
```bash
pve-config-backup
```
4. Install system service
```bash
pve-config-backup --install
```

## Service Operation
Check backup status:
```bash
pve-config-backup --info
```
For VM and CT stored in NFS Storage:
```
  the service will backup VM and CT conf files into VM or CT virtual disk folder in /mnt/pve
```
For VM and CT stored in LVM Storage:
```
  the service will backup VM and CT conf files into disk folder in
  /mnt/pve-config-backup-<lvm-volume-group-of-vm-ct-virtual-disk>
```
