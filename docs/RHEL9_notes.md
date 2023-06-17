# RHEL/Centos Stream 9 Setup Notes

Things to run on all hosts.

```bash
dnf config-manager --set-enabled crb
dnf -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-9.noarch.rpm
dnf -y install centos-release-kmods
dnf config-manager --set-enabled centos-kmods-rebuild
dnf groupinstall -y "Virtualization Host"
dnf install -y virt-manager
grubby --update-kernel ALL --args selinux=0
echo "*.* @10.90.12.31" > /etc/rsyslog.d/iem.conf
systemctl restart rsyslog
dnf -y install samba krb5-workstation sssd iptables-nft-services \
 oddjob-mkhomedir sysstat cifs-utils git \
 tmux lftp byacc gcc make rpcgen libxml2-devel zlib-devel tcsh postfix \
 compat-libgfortran-48 \
 keepalived dstat keepalived libnsl \
 nfs-utils xorg-x11-fonts-ISO8859-1-75dpi xorg-x11-fonts-75dpi tmpwatch \
 perl-FCGI-Client nrpe nagios-plugins-disk iperf3 libgfortran \
 xorg-x11-server-Xvfb \
 keyutils s-nail autofs s-nail \
 liberation-mono-fonts perl-libwww-perl nagios-plugins-perl chkconfig \
 libdb-cxx gd liberation-serif-fonts gifsicle ImageMagick perl

dnf -y erase cockpit-podman cockpit-ws cockpit-system cockpit-bridge kmod-kvdo

cd /opt
git clone https://github.com/akrherz/nagios-checks.git
systemctl enable sysstat
systemctl start sysstat

cd /etc/nrpe.d
ln -s /opt/nagios-checks/nrpe.d/allowed.cfg
systemctl enable nrpe
systemctl start nrpe

echo 'myhostname = changeme.agron.iastate.edu' >> /etc/postfix/main.cf
echo 'relayhost = mailhub.iastate.edu' >> /etc/postfix/main.cf

systemctl enable postfix
systemctl start postfix

systemctl enable chronyd
systemctl start chronyd

systemctl disable firewalld
systemctl enable iptables.service

```

Things to run on non-ADS joined hosts.

```bash
groupadd -g 232284 iem-friends
useradd -u 354600 -g 232284 meteor_ldm
useradd -u 411898 -g 232284 mesonet
groupadd -g 101 domain-users
groupmod -U mesonet,meteor_ldm domain-users
passwd meteor_ldm
passwd mesonet
```

Important for ib_ipoib to load.

```bash
dnf -y install rdma-core
```

```bash
cat >> /etc/systemd/system/lss.mount <<EOL
[Unit]
Description=Mount LSS
[Mount]
What=//las-dfs-01.las.iastate.edu/lss/
Where=/lss
Type=cifs
Options=_netdev,noauto,sec=krb5,multiuser,nounix,noserverino,file_mode=0700,dir_mode=0700,vers=3.0
[Install]
WantedBy=default.target
EOL

cat >> /etc/systemd/system/lss.automount <<EOL
[Unit]
Description=Automount LSS
[Automount]
Where=/lss
[Install]
WantedBy=default.target
EOL

cat > /etc/cron.d/system-keytab <<EOL
@reboot root /usr/bin/sleep 20 && /usr/bin/kinit XX\$@IASTATE.EDU -k -t '/etc/krb5.keytab'
@hourly root /usr/bin/kinit XX\$@IASTATE.EDU -k -t '/etc/krb5.keytab'
EOL

cat > /etc/krb5.conf <<EOL
# To opt out of the system crypto-policies configuration of krb5, remove the
# symlink at /etc/krb5.conf.d/crypto-policies which will not be recreated.
includedir /etc/krb5.conf.d/

[logging]
    default = FILE:/var/log/krb5libs.log
    kdc = FILE:/var/log/krb5kdc.log
    admin_server = FILE:/var/log/kadmind.log

[libdefaults]
 ticket_lifetime = 24h
 renew_lifetime = 7d
 forwardable = true
 rdns = false
 default_realm = IASTATE.EDU
 dns_lookup_realm = True
 dns_uri_lookup = false
EOL

cat > /etc/samba/smb.conf <<EOL
# See smb.conf.example for a more detailed config file or
# read the smb.conf manpage.
# Run 'testparm' to verify the config is correct after
# you modified it.

[global]
        workgroup = IASTATE
        security = ads
        realm = iastate.edu
        kerberos method = secrets and keytab
        client signing = yes
        client use spnego = yes
        passdb backend = tdbsam

        printing = cups
        printcap name = cups
        load printers = yes
        cups options = raw


[homes]
  comment = Home Directories
  valid users = %S, %D%w%S
  browseable = No
  read only = No
  inherit acls = Yes

[printers]
  comment = All Printers
  path = /var/tmp
  printable = Yes
  create mask = 0600
  browseable = No

[print$]
  comment = Printer Drivers
  path = /var/lib/samba/drivers
  write list = @printadmin root
  force group = @printadmin
  create mask = 0664
  directory mask = 0775
EOL

cat > /etc/sssd/sssd.conf <<EOL
[sssd]
domains = iastate.edu
config_file_version = 2
services = nss, pam

[pam]
# Never expire cached creds
offline_credentials_expiration = 0

[domain/iastate.edu]
ad_gpo_access_control = disabled
ad_domain = iastate.edu
dyndns_update = False
krb5_realm = IASTATE.EDU
realmd_tags = manages-system joined-with-samba 
cache_credentials = True
id_provider = ad
krb5_store_password_if_offline = True
default_shell = /bin/bash
ldap_id_mapping = False
use_fully_qualified_names = False
fallback_homedir = /home/%u
access_provider = ad
# https://access.redhat.com/solutions/6155072
timeout = 120
EOL
chmod 600 /etc/sssd/sssd.conf

net ads join --no-dns-updates -U akrherz

systemctl enable sssd
systemctl restart sssd

mkhomedir_helper meteor_ldm
mkhomedir_helper mesonet

systemctl daemon-reload
systemctl enable lss.automount
systemctl start lss.automount
```

Stuff needed for hosts running websites.

```bash
dnf -y install https://rpms.remirepo.net/enterprise/remi-release-9.rpm
dnf -y module reset php
dnf -y module enable php:remi-8.2
dnf -y module enable mod_auth_openidc
dnf -y install mod_auth_openidc php-fpm httpd mod_ssl mod_fcgid \
  php-pecl-memcached php-pgsql swig fcgi-devel php-gd php-mbstring \
  php-dbase

cd /opt
git clone https://github.com/akrherz/iemwebfarm.git
cd /etc/httpd/conf.d
ln -s /opt/iemwebfarm/apache_conf.d/server-status.conf

systemctl enable httpd
systemctl enable php-fpm
systemctl start php-fpm
systemctl start httpd

mkdir /var/cache/matplotlib
chown apache:apache /var/cache/matplotlib

ln -s /mnt/idep2/2 /i

# Copy .pgpass to /usr/share/httpd and ensure it is owned by apache
# edit security.limit_extensions to include .phtml in /etc/php-fpm.d/www.conf
# add /etc/http/conf.d/server-status.conf
# add /etc/systemd/system/httpd.service.d/override.conf￼￼￼￼
# set /etc/httpd/conf.modules.d/10-wsgi-python3.conf WSGIApplicationGroup %{GLOBAL} and
# use conda mod_wsgi
# update <directory /> setting in httpd.conf
# /mesonet/data/gis
```
