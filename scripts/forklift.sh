#!/bin/bash
# Sometimes we need to forklift production, so this attempts to do it nicely.
set -x
HOST_PATTERN="iemwebfarm,iem_appliance,anticyclone.agron.iastate.edu"
INVENTORY_DIR="/home/akrherz/projects/infra-ansible/inventories"

for machine in $(ansible $HOST_PATTERN -i $INVENTORY_DIR --list-hosts | awk 'NR>1 {print $1}'); do
  # Enable the F5 denial script
  ssh root@$machine "sh /opt/iemwebfarm/scripts/f5util.sh ON"
  # Wait a minute for load to bleed away
  sleep 60
  # Copy miniconda
  rsync -a -H --delete /opt/miniconda3 mesonet@${machine}:/opt/
  # git pull various repos
  ssh mesonet@$machine "cd /opt/iem; git pull; cd /opt/iemwebfarm; git pull"
  # Restart apache
  ssh root@$machine "systemctl restart httpd"
  # Stop F5 denial
  ssh root@$machine "sh /opt/iemwebfarm/scripts/f5util.sh OFF"
done
