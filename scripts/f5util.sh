# Our present method to remove a webfarm node from the F5 pool

FLAG="-D"
if [ "$1" = "ON" ]; then
 FLAG="-I"
fi
set -x

iptables $FLAG INPUT -s 10.90.15.253 -j DROP
iptables $FLAG INPUT -s 10.90.15.252 -j DROP
ip6tables $FLAG INPUT -s 2610:130:108:83::252 -j DROP
ip6tables $FLAG INPUT -s 2610:130:108:83::253 -j DROP
