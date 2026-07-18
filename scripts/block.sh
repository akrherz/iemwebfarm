#!/bin/bash

# Ensure we are called with two arguments
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 {block|unblock} {remote_addr}"
    exit 1
fi
# Ensure argument 1 is block or unblock
if [ "$1" != "block" ] && [ "$1" != "unblock" ]; then
    echo "First argument must be 'block' or 'unblock'"
    exit 1
fi

for mach in anticyclone iemvs35-dc iemvs36-dc iemvs37-dc iemvs38-dc \
        iemvs39-dc iemvs40-dc iemvs41-dc iemvs42-dc iemvs43-dc iemvs44-dc; do
    ssh -o BatchMode=yes -o ConnectTimeout=5 \
    mesonet@${mach} /opt/miniconda3/envs/prod/bin/python \
    /opt/iemwebfarm/scripts/app_firewall.py "$1" "$2"
done
