#!/bin/bash
# A common workflow to apply updates to the farm...
set -e
set -x
HOST_PATTERN="iemwebfarm"
INVENTORY_DIR="/home/akrherz/projects/infra-ansible/inventories"

for machine in $(ansible $HOST_PATTERN -i $INVENTORY_DIR --list-hosts | awk 'NR>1 {print $1}'); do
  # Enable the F5 denial script
  ssh "root@$machine" "sh /opt/iemwebfarm/scripts/f5util.sh ON"
  # Wait a minute for load to bleed away
  sleep 60
  # Run OS update
  ssh "root@$machine" "dnf -y update"
  # Copy miniconda
  rsync -a -H --delete /opt/miniconda3 "mesonet@${machine}:/opt/"
  # git pull various repos
  ssh "mesonet@$machine" "cd /opt/iem && git pull && cd /opt/iemwebfarm && git pull"
  # Stop LDM
  ssh "meteor_ldm@$machine" "ldmadmin stop"
  # Restart machine
  ssh "root@$machine" "reboot"
done
