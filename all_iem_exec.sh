#!/bin/sh
# Exec a script over all the IEM nodes

# Run iem21 first as it may need to be aware of changes in hostnames
MACHINES="iem-director0 iem-director1 iem11.local iem12.local iem13.local iem14.local iem15.local iem16.local iem18.local iem19.local iemvs100 iemvs101 iemvs102 iemvs103 iemvs104 iemvs105 iemvs106 iemvs107 iemvs108 iemvs109"
for MACH in $MACHINES
do
	echo "----------------------- $MACH -------------------------"
	ssh root@$MACH $1
	echo 
done
