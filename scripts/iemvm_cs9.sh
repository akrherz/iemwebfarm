export I=$1

setenforce 0
hostnamectl set-hostname iemvm${I}.agron.iastate.edu

mkdir /root/.ssh
echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDbP05eBd5yn4hObLT1jzJHU2DKHKJMXrIZqZaZM4pEL6g+ILJzirOXqWQ0Om1wScs/e1xvwIxuWkwCEnzKytbRZgdaokaCnXCEAISR6yVUSLFgS5BBeUmAQA7ayQpLL5sitcm9aTzZ/JjpwcrDyKZEcidPe6eYdB1TPC5bKqeqedjBe/3ylO2wUUv6wOK9aYRzbvsS+BG+lNeFHJ0coE91r8e6uHFJyINkiBfy90jRYB/GWRvo8WPNPwV4dOJmrtpMR9qllY7bdIZktSK3kPnirI0ipdbRdLY1BTswxqc2rJtZ1LPyueMW4wcufrmFHyHAl7XFIiZjkZ3EmO8K7XgH akrherz@laptop.local" >> /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys

sed -i 's/enforcing/disabled/g' /etc/selinux/config
grubby --update-kernel ALL --args selinux=0
dnf -y groupinstall "Virtualization Host"
dnf config-manager --set-enabled crb
dnf -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm
dnf -y install centos-release-kmods
dnf config-manager --set-enabled centos-kmods-rebuild
echo "*.* @10.90.12.31" > /etc/rsyslog.d/iem.conf
systemctl restart rsyslog
dnf -y install samba krb5-workstation sssd iptables-nft-services  oddjob-mkhomedir sysstat cifs-utils git  tmux lftp byacc gcc make rpcgen libxml2-devel zlib-devel tcsh postfix  compat-libgfortran-48  keepalived dstat keepalived libnsl  nfs-utils xorg-x11-fonts-ISO8859-1-75dpi xorg-x11-fonts-75dpi tmpwatch  perl-FCGI-Client nrpe nagios-plugins-disk iperf3 libgfortran  xorg-x11-server-Xvfb  keyutils s-nail autofs s-nail  liberation-mono-fonts perl-libwww-perl nagios-plugins-perl chkconfig  libdb-cxx gd liberation-serif-fonts gifsicle virt-manager
dnf -y erase cockpit-podman cockpit-ws cockpit-system cockpit-bridge kmod-kvdo
cd /opt
git clone https://github.com/akrherz/nagios-checks.git
systemctl enable sysstat
cd /etc/nrpe.d
ln -s /opt/nagios-checks/nrpe.d/allowed.cfg
systemctl enable nrpe
echo "myhostname = $(hostname)" >> /etc/postfix/main.cf
echo 'relayhost = mailhub.iastate.edu' >> /etc/postfix/main.cf
systemctl enable postfix
systemctl start postfix
systemctl enable chronyd
systemctl start chronyd
systemctl disable firewalld
systemctl enable iptables.service

nmcli conn add type bridge con-name br0 ifname br0
nmcli conn modify eno1 master br0
nmcli conn modify br0 ipv4.method auto
nmcli conn modify br0 connection.autoconnect-slaves 1
nmcli conn modify br0 bridge.stp no
nmcli con mod eno1 connection.autoconnect yes
nmcli con mod br0 connection.autoconnect yes

nmcli conn add type bridge con-name iembr0 ifname iembr0
nmcli conn modify iembr0 ipv4.addresses "192.168.0.5${I}/24"
nmcli conn modify iembr0 ipv4.method manual
nmcli conn modify eno2 master iembr0
nmcli conn modify iembr0 connection.autoconnect-slaves 1
nmcli con mod eno2 connection.autoconnect yes
nmcli con mod iembr0 connection.autoconnect yes

umount /home
lvremove -y /dev/cs_iemvm${I}/home
lvcreate -n kvmimages -L 700G cs_iemvm${I}
mkfs.xfs -L kvmimages /dev/cs_iemvm${I}/kvmimages
mkdir /mnt/kvmimages
systemctl daemon-reload

vi /etc/fstab
